#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy"]
# ///
"""SFX procedurais para motion design: sem amostras, sem rede, sem licença de terceiros.

  uv run scripts/sfx.py whoosh -o public/audio/sfx/whoosh.wav --dur 0.6 --seed 3
  uv run scripts/sfx.py --all public/audio/sfx
Tipos: whoosh, swoosh (UI), riser, impact, click, pop, tick, shimmer.
mix.py importa este módulo para gerar o SFX de cada evento de timeline.json no frame exato.
"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000


def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _norm(x, peak_db=-1.0):
    peak = np.max(np.abs(x)) or 1.0
    return (x / peak * 10 ** (peak_db / 20)).astype(np.float32)


def _sweep(noise, f0, f1, q=4.0, block=256):
    out = np.zeros_like(noise)
    n = int(np.ceil(len(noise) / block))
    zi = None
    for i, fc in enumerate(np.geomspace(f0, f1, max(n, 1))):
        bw = fc / q
        sos = signal.butter(2, [max(fc - bw / 2, 20), min(fc + bw / 2, SR / 2 - 100)], "bandpass", fs=SR, output="sos")
        seg = noise[i * block:(i + 1) * block]
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        y, zi = signal.sosfilt(sos, seg, zi=zi)
        out[i * block:i * block + len(seg)] = y
    return out


def whoosh(dur=0.7, lo=300, hi=4000, seed=7):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    n = rng.standard_normal(len(t))
    h = len(t) // 2
    x = np.concatenate([_sweep(n[:h], lo, hi), _sweep(n[h:], hi, lo)])
    return _norm(x * np.sin(np.pi * t / dur) ** 2)


def swoosh(dur=0.25, seed=7):
    return whoosh(dur, 1500, 9000, seed)


def riser(dur=2.0, seed=7):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    tone = signal.chirp(t, f0=200, t1=dur, f1=2000, method="logarithmic")
    noise = _sweep(rng.standard_normal(len(t)), 500, 8000, q=2)
    return _norm((0.6 * tone + 0.8 * noise) * (t / dur) ** 2)


def impact(dur=1.2, seed=7):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    f = 30 + 90 * np.exp(-t * 18)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
    crack = signal.sosfilt(signal.butter(2, 2500, "highpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 60)
    tail = signal.sosfilt(signal.butter(2, 400, "lowpass", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 3) * 0.3
    return _norm(np.tanh(1.5 * (thump + 0.5 * crack + tail)))


def click(dur=0.03, seed=7):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    x = signal.sosfilt(signal.butter(2, [2000, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(len(t)))
    return _norm(x * np.exp(-t * 400))


def pop(dur=0.12, seed=7):
    t = _t(dur)
    f = 900 * np.exp(-t * 25) + 250
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45))


def tick(dur=0.05, seed=7):
    t = _t(dur)
    return _norm(np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 160))


def shimmer(dur=1.2, seed=7):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    x = np.zeros_like(t)
    for f in rng.uniform(2500, 7000, 14):
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t * rng.uniform(2, 6))
    return _norm(x * np.minimum(1, t / 0.03))


GENERATORS = {"whoosh": whoosh, "swoosh": swoosh, "riser": riser, "impact": impact, "click": click, "pop": pop, "tick": tick, "shimmer": shimmer}


def render(kind: str, dur: float | None = None, seed: int = 7) -> np.ndarray:
    fn = GENERATORS[kind]
    return fn(seed=seed) if dur is None else fn(dur=dur, seed=seed)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", nargs="?", choices=list(GENERATORS))
    ap.add_argument("-o", "--out")
    ap.add_argument("--dur", type=float)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--all", metavar="DIR")
    a = ap.parse_args()
    if a.all:
        d = pathlib.Path(a.all)
        d.mkdir(parents=True, exist_ok=True)
        for k in GENERATORS:
            wavfile.write(d / f"{k}.wav", SR, render(k, seed=a.seed))
        print(f"{len(GENERATORS)} SFX em {d}")
        return
    if not a.kind:
        ap.error("informe o tipo ou --all")
    out = pathlib.Path(a.out or f"{a.kind}.wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(out, SR, render(a.kind, a.dur, a.seed))
    print(out)


if __name__ == "__main__":
    main()
