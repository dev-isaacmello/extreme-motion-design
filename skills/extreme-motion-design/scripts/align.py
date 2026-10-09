#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper>=1.1", "numpy"]
# ///
"""Alinha um WAV de narração já gerado ao roteiro e escreve <out>.words.json com tempos reais.

Serve para qualquer voz que não devolve tempos por palavra: modelo local fora do tts.py
(Chatterbox, F5-TTS, Qwen3-TTS, Piper...), OpenAI, Azure ou voz gravada por uma pessoa.

  uv run scripts/align.py public/audio/narration.wav roteiro.txt
  uv run scripts/align.py voz.wav roteiro.txt -o public/audio/narration --lang pt --model small
  uv run scripts/align.py voz.wav roteiro.txt --against public/audio/narration.words.json   # mede o erro

O roteiro manda no texto (o que aparece na tela); o Whisper só empresta os tempos. `mismatch` conta
palavras ouvidas diferente do roteiro (pronúncia errada, texto trocado, número por extenso) e
`interpolated` as que não foram ouvidas e ganharam tempo repartido entre as vizinhas.
"""
from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

import numpy as np


def norm(w: str) -> str:
    w = unicodedata.normalize("NFKD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if not unicodedata.combining(c)))


def decode(path: str) -> np.ndarray:
    # ffmpeg em vez do PyAV do faster-whisper: evita incompatibilidade de versão do PyAV.
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
        capture_output=True, check=True,
    ).stdout
    return np.frombuffer(raw, np.float32)


def transcribe(audio: np.ndarray, lang: str, model: str) -> list[dict]:
    from faster_whisper import WhisperModel

    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language=lang, word_timestamps=True, vad_filter=False)
    return [{"word": w.word.strip(), "start": w.start, "end": w.end} for s in segs for w in s.words if w.word.strip()]


def align(script_words: list[str], heard: list[dict], duration: float) -> tuple[list[dict], int, int]:
    """Devolve (palavras com tempo, quantas foram interpoladas, quantas o Whisper ouviu diferente do roteiro)."""
    a, b = [norm(w) for w in script_words], [norm(h["word"]) for h in heard]
    times: list[tuple[float, float] | None] = [None] * len(a)
    exact = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            exact += i2 - i1
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
        elif tag == "replace" and j2 > j1:
            # Trecho ouvido diferente do escrito (número por extenso, sigla): reparte o intervalo por tamanho.
            t0, t1 = heard[j1]["start"], heard[j2 - 1]["end"]
            w = np.array([max(len(x), 1) for x in a[i1:i2]], float)
            edges = t0 + np.concatenate([[0], np.cumsum(w)]) / w.sum() * (t1 - t0)
            for k in range(i2 - i1):
                times[i1 + k] = (float(edges[k]), float(edges[k + 1]))
    missing = sum(t is None for t in times)
    i = 0
    while i < len(times):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(times) and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i else 0.0
        t1 = times[j][0] if j < len(times) else duration
        step = (t1 - t0) / (j - i)
        for k in range(i, j):
            times[k] = (t0 + (k - i) * step, t0 + (k - i + 1) * step)
        i = j
    words = [{"word": w, "spoken": w, "start": round(t[0], 3), "end": round(t[1], 3)} for w, t in zip(script_words, times)]
    return words, missing, len(a) - exact


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav")
    ap.add_argument("script", help="roteiro .txt com o texto exibido")
    ap.add_argument("-o", "--out", default=None, help="prefixo de saída (padrão: o do wav)")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--model", default="small", help="tiny, base, small (padrão), medium")
    ap.add_argument("--against", default=None, help="words.json de referência: imprime o erro médio de início de palavra")
    a = ap.parse_args()

    script_words = [w for w in pathlib.Path(a.script).read_text(encoding="utf-8").split() if re.search(r"\w", w)]
    audio = decode(a.wav)
    duration = len(audio) / 16000
    heard = transcribe(audio, a.lang, a.model)
    words, missing, differ = align(script_words, heard, duration)
    wpm = len(words) / max(duration, 0.1) * 60
    out = pathlib.Path(a.out) if a.out else pathlib.Path(a.wav).with_suffix("")
    meta = {
        "text": " ".join(script_words), "provider": "align", "voice": None, "duration": round(duration, 3),
        "wpm": round(wpm), "approx": max(missing, differ) > len(words) * 0.2, "interpolated": missing, "mismatch": differ, "words": words,
    }
    report = {"words": len(words), "heard": len(heard), "interpolated": missing, "mismatch": differ, "wpm": round(wpm), "approx": meta["approx"]}
    if a.against:
        ref = json.load(open(a.against, encoding="utf-8"))["words"]
        if len(ref) == len(words):
            err = [abs(r["start"] - w["start"]) for r, w in zip(ref, words)]
            report["start_error_ms"] = {"mean": round(float(np.mean(err)) * 1000), "max": round(float(np.max(err)) * 1000)}
        else:
            report["start_error_ms"] = f"referência tem {len(ref)} palavras, roteiro tem {len(words)}"
    else:
        pathlib.Path(str(out) + ".words.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        report["out"] = str(out) + ".words.json"
    print(json.dumps(report, ensure_ascii=False))
    if differ > len(words) * 0.2:
        print(f"aviso: {differ} de {len(words)} palavras foram ouvidas diferente do roteiro: confira pronúncia, texto e idioma (números e siglas contam)", file=sys.stderr)


if __name__ == "__main__":
    main()
