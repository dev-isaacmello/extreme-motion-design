#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "soundfile"]
# ///
"""Mixagem a partir de timeline.json: narração + trilha com ducking + SFX nos eventos + loudness.

  uv run scripts/mix.py public/timeline.json
Lê (caminhos relativos à pasta do timeline.json):
  duration, narration{file,start,gain_db}, music{file,gain_db,duck_db,fade_in,fade_out,start},
  sfx[{at,type|file,gain_db,dur,seed}], loudness{lufs,tp}, audio (arquivo de saída).
Requer ffmpeg no PATH (decodifica qualquer formato e faz loudnorm em duas passadas).
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sfx as sfxlib  # noqa: E402

SR = 48000


def load(path: pathlib.Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).copy()


def db(x):
    return 10 ** (x / 20)


def place(bus: np.ndarray, clip: np.ndarray, at: float, gain: float):
    s = int(round(at * SR))
    if s >= len(bus) or s + len(clip) <= 0:
        return
    c = clip[max(0, -s):]
    s = max(s, 0)
    e = min(len(bus), s + len(c))
    bus[s:e] += c[: e - s] * gain


def envelope(x: np.ndarray, attack=0.02, release=0.4, win=0.02) -> np.ndarray:
    mono = np.abs(x).mean(1)
    hop = int(win * SR)
    rms = np.sqrt(np.convolve(mono ** 2, np.ones(hop) / hop, mode="same"))
    out = np.zeros_like(rms)
    a, r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    level = 0.0
    for i, v in enumerate(rms):  # seguidor de envelope com ataque e release
        level = a * level + (1 - a) * v if v > level else r * level + (1 - r) * v
        out[i] = level
    return out


def loudnorm(src: pathlib.Path, dst: pathlib.Path, lufs: float, tp: float):
    first = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(re.findall(r"\{[^{}]*\}", first)[-1])
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", str(SR), "-c:a", "pcm_s16le", str(dst)], check=True)
    return m


def main():
    tl_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "public/timeline.json")
    base = tl_path.parent
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    n = int(tl["duration"] * SR)
    voice = np.zeros((n, 2), np.float32)
    music = np.zeros((n, 2), np.float32)
    fx = np.zeros((n, 2), np.float32)

    nar = tl.get("narration") or {}
    if nar.get("file"):
        place(voice, load(base / nar["file"]), nar.get("start", 0), db(nar.get("gain_db", 0)))

    mus = tl.get("music") or {}
    if mus.get("file"):
        m = load(base / mus["file"])
        start = mus.get("start", 0)
        need = n - int(start * SR)
        if len(m) < need:  # repete com crossfade curto se a faixa for menor que o vídeo
            reps = int(np.ceil(need / len(m))) + 1
            m = np.concatenate([m] * reps)
        m = m[:need].copy()
        fi, fo = int(mus.get("fade_in", 0.5) * SR), int(mus.get("fade_out", 1.5) * SR)
        if fi:
            m[:fi] *= np.linspace(0, 1, fi)[:, None]
        if fo:
            m[-fo:] *= np.linspace(1, 0, fo)[:, None]
        place(music, m, start, db(mus.get("gain_db", -16)))

    for ev in tl.get("sfx", []):
        clip = load(base / ev["file"]) if ev.get("file") else np.repeat(sfxlib.render(ev["type"], ev.get("dur"), ev.get("seed", 7))[:, None], 2, 1)
        place(fx, clip, ev["at"], db(ev.get("gain_db", -12)))

    duck = mus.get("duck_db", -10)
    if duck and np.abs(voice).max() > 0:
        env = envelope(voice)
        active = np.clip((20 * np.log10(env + 1e-9) + 45) / 15, 0, 1)  # 0 abaixo de -45 dBFS, 1 acima de -30
        music *= db(duck * active)[:, None]

    mix = voice + music + fx
    out = base / tl.get("audio", "audio/mix.wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    loud = tl.get("loudness", {"lufs": -14, "tp": -1.5})
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "pre.wav"
        sf.write(tmp, np.clip(mix, -1, 1), SR, subtype="FLOAT")
        measured = loudnorm(tmp, out, loud["lufs"], loud["tp"])
    print(json.dumps({"out": str(out), "duration": tl["duration"], "pre_lufs": measured["input_i"], "target": loud}))


if __name__ == "__main__":
    main()
