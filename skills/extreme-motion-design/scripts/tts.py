#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["kokoro-onnx>=0.4.9", "soundfile", "numpy", "num2words", "requests"]
# ///
"""Narração: roteiro -> <out>.wav + <out>.words.json (palavras com início e fim em segundos).

Provedores:
  kokoro      local, grátis, Apache-2.0, CPU. Padrão. Vozes pt-BR: pf_dora (F), pm_alex, pm_santa (M).
  elevenlabs  ELEVENLABS_API_KEY. Tempos por caractere reais.
  openai      OPENAI_API_KEY. Sem tempos: palavras estimadas (approx=true).
  azure       AZURE_SPEECH_KEY + AZURE_SPEECH_REGION. Sem tempos via REST (approx=true).

Exemplos:
  uv run scripts/tts.py roteiro.txt -o public/audio/narration
  uv run scripts/tts.py roteiro.txt -o public/audio/narration --voice pm_alex --speed 0.9
  uv run scripts/tts.py roteiro.txt -o out/nar --provider elevenlabs --voice <voice_id>
  uv run scripts/tts.py --normalize-only "Custa R$ 1.234,56 às 14h30"
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.request
from xml.sax.saxutils import escape

import numpy as np
import soundfile as sf

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEXICON = ROOT / "assets" / "lexicon.pt-BR.json"
KOKORO_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
KOKORO_DIR = pathlib.Path(os.environ.get("KOKORO_DIR", pathlib.Path.home() / ".cache" / "motion-design" / "kokoro"))


# ---------- normalização pt-BR ----------
def _n2w(n, **kw) -> str:
    from num2words import num2words

    return num2words(n, lang="pt_BR", **kw)


def _fem(n: int) -> str:
    s = _n2w(n)
    s = re.sub(r"\bum\b", "uma", s)
    return re.sub(r"\bdois\b", "duas", s)


def normalize_ptbr(text: str, lexicon: dict[str, str] | None = None) -> str:
    t = " ".join(text.split())
    for k in sorted(lexicon or {}, key=len, reverse=True):
        t = re.sub(rf"(?<![\w]){re.escape(k)}(?![\w])", lexicon[k], t)

    def money(m):
        v = float(m.group(1).replace(".", "").replace(",", "."))
        return _n2w(v, to="currency").replace("mil,", "mil")

    t = re.sub(r"R\$\s?(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:,\d{1,2})?)", money, t)
    t = re.sub(r"\b(\d{1,2})h(\d{2})\b", lambda m: f"{_fem(int(m.group(1)))} e {_n2w(int(m.group(2)))}", t)
    t = re.sub(r"\b(\d{1,2})h\b", lambda m: f"{_fem(int(m.group(1)))} {'hora' if m.group(1) in ('1', '01') else 'horas'}", t)
    t = re.sub(r"(\d+(?:,\d+)?)\s?%", lambda m: f"{m.group(1)} por cento", t)
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})+)\b", lambda m: _n2w(int(m.group(1).replace(".", ""))), t)
    t = re.sub(r"\b(\d+),(\d+)\b", lambda m: f"{_n2w(int(m.group(1)))} vírgula {' '.join(_n2w(int(c)) for c in m.group(2))}", t)
    t = re.sub(r"\b(\d+)º", lambda m: _n2w(int(m.group(1)), to="ordinal"), t)
    t = re.sub(r"\b(\d+)ª", lambda m: _n2w(int(m.group(1)), to="ordinal").replace("o", "a")[:-1] + "a", t)
    t = re.sub(r"\b\d+\b", lambda m: _n2w(int(m.group(0))), t)
    return t


def display_pairs(raw: str, lexicon: dict[str, str], normalize: bool) -> list[tuple[str, list[str]]]:
    """Cada token exibido (o que aparece na tela) com as palavras faladas que ele vira."""
    t = " ".join(raw.split())
    if normalize:
        for k in sorted([k for k in lexicon if " " in k], key=len, reverse=True):
            t = re.sub(rf"(?<![\w]){re.escape(k)}(?![\w])", k.replace(" ", " "), t)
        t = re.sub(r"R\$\s", "R$ ", t)
    pairs = []
    for tok in t.split(" "):
        disp = tok.replace(" ", " ")
        spoken = normalize_ptbr(disp, lexicon).split() if normalize else [disp]
        if any(re.search(r"\w", s) for s in spoken):
            pairs.append((disp, spoken))
    return pairs


def to_display(pairs, words):
    """Agrega tempos das palavras faladas de volta nos tokens exibidos."""
    out, i = [], 0
    for disp, spoken in pairs:
        seg = words[i:i + len(spoken)]
        i += len(spoken)
        if seg:
            out.append({"word": disp, "spoken": " ".join(spoken), "start": seg[0]["start"], "end": seg[-1]["end"]})
    return out


def warn_unknown(text: str) -> list[str]:
    caps = sorted(set(re.findall(r"\b[A-Z]{2,6}s?\b", text)))
    latin = sorted(set(w for w in re.findall(r"\b\w*(?:th|sh|w|y|k)\w*\b", text, flags=re.I) if len(w) > 2))
    return caps + latin


# ---------- tempos por palavra ----------
def _split_words(text: str) -> list[str]:
    return [w for w in text.split() if re.search(r"\w", w)]


def approx_words(text: str, duration: float, lead: float = 0.05, tail: float = 0.1) -> list[dict]:
    words = _split_words(text)
    weights = np.array([len(re.sub(r"\W", "", w)) + 2.5 * bool(re.search(r"[.,;:!?…]$", w)) for w in words], float)
    span = max(duration - lead - tail, 0.1)
    edges = lead + np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * span
    return [{"word": w, "start": round(float(edges[i]), 3), "end": round(float(edges[i + 1]), 3)} for i, w in enumerate(words)]


def chars_to_words(chars: list[str], starts: list[float], ends: list[float]) -> list[dict]:
    out, cur, s, e = [], "", None, None
    for ch, cs, ce in zip(chars, starts, ends):
        if ch.isspace():
            if cur:
                out.append({"word": cur, "start": round(s, 3), "end": round(e, 3)})
            cur, s = "", None
            continue
        cur += ch
        s = cs if s is None else s
        e = ce
    if cur:
        out.append({"word": cur, "start": round(s, 3), "end": round(e, 3)})
    return out


# ---------- provedores ----------
def _download(url: str, dest: pathlib.Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"baixando {url}", file=sys.stderr)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(dest)


def tts_kokoro(text, voice, lang, speed):
    from kokoro_onnx import Kokoro

    model = KOKORO_DIR / "kokoro-v1.0.onnx"
    voices = KOKORO_DIR / "voices-v1.0.bin"
    for f in (model, voices):
        if not f.exists():
            _download(KOKORO_URL + f.name, f)
    k = Kokoro(str(model), str(voices))
    samples, sr, timings = k.create_timed(text, voice=voice, speed=speed, lang=lang, sentence_pause=0.35, clause_pause=0.12)
    groups, cur = [], []
    for t in [*timings, None]:
        if t is not None and t.phoneme.strip():
            cur.append(t)
            continue
        if cur:
            groups.append((cur[0].start, cur[-1].end, "".join(x.phoneme for x in cur)))
        cur = []
    words = _split_words(text)
    if len(groups) == len(words):
        return samples, sr, [{"word": w, "start": round(g[0], 3), "end": round(g[1], 3), "ph": g[2]} for w, g in zip(words, groups)], False
    print(f"aviso: {len(groups)} grupos de fonemas para {len(words)} palavras; tempos estimados", file=sys.stderr)
    return samples, sr, approx_words(text, len(samples) / sr), True


def tts_elevenlabs(text, voice, model, speed):
    import requests

    key = os.environ["ELEVENLABS_API_KEY"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=pcm_24000"
    body = {
        "text": text,
        "model_id": model or "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.0, "speed": speed},
    }
    r = requests.post(url, json=body, headers={"xi-api-key": key}, timeout=300)
    r.raise_for_status()
    j = r.json()
    pcm = np.frombuffer(base64.b64decode(j["audio_base64"]), dtype="<i2").astype(np.float32) / 32768
    al = j.get("normalized_alignment") or j["alignment"]
    words = chars_to_words(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])
    return pcm, 24000, words, False


def tts_openai(text, voice, model, speed, instructions):
    import requests

    key = os.environ["OPENAI_API_KEY"]
    body = {
        "model": model or "gpt-4o-mini-tts",
        "voice": voice or "marin",
        "input": text,
        "response_format": "pcm",
        "instructions": instructions
        or "Português do Brasil. Voz calma, suave e acolhedora, ritmo pausado, sem soar como locutor de rádio.",
        "speed": speed,
    }
    r = requests.post("https://api.openai.com/v1/audio/speech", json=body, headers={"Authorization": f"Bearer {key}"}, timeout=300)
    r.raise_for_status()
    pcm = np.frombuffer(r.content, dtype="<i2").astype(np.float32) / 32768
    return pcm, 24000, approx_words(text, len(pcm) / 24000), True


def tts_azure(text, voice, style, speed):
    import requests

    key, region = os.environ["AZURE_SPEECH_KEY"], os.environ["AZURE_SPEECH_REGION"]
    rate = f"{round((speed - 1) * 100):+d}%"
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="pt-BR">'
        f'<voice name="{voice or "pt-BR-FranciscaNeural"}"><mstts:express-as style="{style}"><prosody rate="{rate}">{escape(text)}</prosody>'
        "</mstts:express-as></voice></speak>"
    )
    r = requests.post(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode(),
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "raw-24khz-16bit-mono-pcm",
            "User-Agent": "motion-design-skill",
        },
        timeout=300,
    )
    r.raise_for_status()
    pcm = np.frombuffer(r.content, dtype="<i2").astype(np.float32) / 32768
    return pcm, 24000, approx_words(text, len(pcm) / 24000), True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", nargs="?", help="arquivo .txt com o roteiro (ou '-' para stdin)")
    ap.add_argument("-o", "--out", default="public/audio/narration", help="prefixo de saída (sem extensão)")
    ap.add_argument("--provider", default="kokoro", choices=["kokoro", "elevenlabs", "openai", "azure"])
    ap.add_argument("--voice", default=None, help="kokoro: pf_dora | pm_alex | pm_santa | af_heart ...")
    ap.add_argument("--lang", default="pt-br", help="kokoro: pt-br, en-us, es ...")
    ap.add_argument("--speed", type=float, default=0.92, help="0.85-0.95 soa calmo; 1.0 é neutro")
    ap.add_argument("--model", default=None)
    ap.add_argument("--style", default="calm", help="azure: calm, gentle, friendly ...")
    ap.add_argument("--instructions", default=None, help="openai: direção de voz")
    ap.add_argument("--no-normalize", action="store_true")
    ap.add_argument("--normalize-only", default=None, help="só imprime o texto normalizado")
    a = ap.parse_args()

    env = pathlib.Path(".env")
    if env.is_file():  # chaves de API ficam no .env do projeto, fora do chat e do git
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip("'\""))

    lex = json.loads(LEXICON.read_text(encoding="utf-8")) if LEXICON.exists() else {}
    if a.normalize_only is not None:
        print(normalize_ptbr(a.normalize_only, lex))
        return
    raw = sys.stdin.read() if a.script in (None, "-") else pathlib.Path(a.script).read_text(encoding="utf-8")
    pt = a.lang.lower().startswith("pt")
    pairs = display_pairs(raw, lex, normalize=pt and not a.no_normalize)
    text = " ".join(" ".join(s) for _, s in pairs)
    unknown = warn_unknown(text) if pt else []
    if unknown:
        print(f"revise a pronúncia (adicione ao léxico se soar errado): {', '.join(unknown)}", file=sys.stderr)

    if a.provider == "kokoro":
        samples, sr, words, approx = tts_kokoro(text, a.voice or ("pf_dora" if pt else "af_heart"), a.lang, a.speed)
    elif a.provider == "elevenlabs":
        samples, sr, words, approx = tts_elevenlabs(text, a.voice, a.model, a.speed)
    elif a.provider == "openai":
        samples, sr, words, approx = tts_openai(text, a.voice, a.model, a.speed, a.instructions)
    else:
        samples, sr, words, approx = tts_azure(text, a.voice, a.style, a.speed)

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out.with_suffix(".wav"), samples, sr)
    dur = len(samples) / sr
    if len(words) != sum(len(s) for _, s in pairs):
        approx, words = True, approx_words(text, dur)
    words = to_display(pairs, words)
    wpm = len(words) / max(dur, 0.1) * 60
    meta = {"text": text, "provider": a.provider, "voice": a.voice, "duration": round(dur, 3), "wpm": round(wpm), "approx": approx, "words": words}
    pathlib.Path(str(out) + ".words.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"wav": str(out.with_suffix(".wav")), "duration": round(dur, 2), "words": len(words), "wpm": round(wpm), "approx": approx}))
    if wpm > 170:
        print("aviso: acima de 170 palavras por minuto; corte texto ou reduza --speed", file=sys.stderr)


if __name__ == "__main__":
    main()
