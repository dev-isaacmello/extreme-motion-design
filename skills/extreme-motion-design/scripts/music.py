#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "scipy", "requests"]
# ///
"""Trilha com licença verificada, ou gerada localmente. Toda faixa entra em credits.json.

Fontes (nesta ordem de preferência):
  incompetech  Kevin MacLeod, CC BY 4.0, catálogo pieces.json feito para agentes, já traz BPM.
  openverse    só license=cc0,pdm,by (ND e SA quebram em vídeo; NC e sampling+ bloqueados).
  generate     cama procedural offline (sem direitos de terceiros), determinística por seed.

  uv run scripts/music.py incompetech --feel calm --bpm 70-110 --min-sec 60 -o public/audio/music.mp3
  uv run scripts/music.py openverse --q "ambient piano" -o public/audio/music.mp3
  uv run scripts/music.py generate --sec 30 --bpm 84 --mood calm -o public/audio/music.wav
Créditos: <pasta do arquivo>/credits.json (acumula). Cole o campo "attribution" na descrição do vídeo.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import numpy as np
from scipy import signal
from scipy.io import wavfile

ALLOWED = {"cc0", "pdm", "by"}
UA = {"User-Agent": "motion-design-skill/1.0 (agent; contact: see credits.json)"}


def add_credit(out: pathlib.Path, entry: dict):
    path = out.parent / "credits.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    data = [d for d in data if d.get("file") != out.name] + [{"file": out.name, "checked_at": dt.datetime.now().isoformat(timespec="seconds"), **entry}]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"créditos: {path}", file=sys.stderr)


def incompetech(a):
    import requests

    base = "https://incompetech.com/music/royalty-free/"
    pieces = requests.get(base + "pieces.json", headers=UA, timeout=60).json()
    lo, hi = (int(x) for x in a.bpm.split("-")) if a.bpm else (0, 999)

    def secs(p):
        try:
            m, s = str(p.get("length", "0:0")).split(":")[-2:]
            return int(m) * 60 + int(s)
        except ValueError:
            return 0

    def ok(p):
        feel = " ".join(str(p.get(k, "")) for k in ("feel", "genre", "title")).lower()
        bpm = int(p.get("bpm") or 0)
        return (not a.feel or a.feel.lower() in feel) and lo <= bpm <= hi and secs(p) >= a.min_sec

    found = [p for p in pieces if ok(p)]
    if not found:
        sys.exit("nada encontrado; afrouxe --feel/--bpm/--min-sec")
    p = found[a.pick % len(found)]
    url = base + "mp3-royaltyfree/" + p["filename"]
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(requests.get(url, headers=UA, timeout=300).content)
    title = p.get("title", p["filename"])
    add_credit(out, {
        "role": "music", "title": title, "author": "Kevin MacLeod", "source": "incompetech.com", "url": url,
        "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/", "bpm": p.get("bpm"),
        "attribution": f'"{title}" Kevin MacLeod (incompetech.com). Licensed under Creative Commons: By Attribution 4.0 License. http://creativecommons.org/licenses/by/4.0/',
        "modifications": "cortada, com fades, ducking e normalização de loudness",
    })
    print(json.dumps({"file": str(out), "title": title, "bpm": p.get("bpm"), "candidates": len(found)}, ensure_ascii=False))


def openverse(a):
    import requests

    params = {"q": a.q, "license": "cc0,pdm,by", "category": a.category, "page_size": 20, "filter_dead": "true"}
    headers = dict(UA)
    if a.token:
        headers["Authorization"] = f"Bearer {a.token}"
    res = requests.get("https://api.openverse.org/v1/audio/", params=params, headers=headers, timeout=60).json().get("results", [])
    res = [r for r in res if str(r.get("license", "")).lower() in ALLOWED and (r.get("duration") or 0) >= a.min_sec * 1000]
    if not res:
        sys.exit("nada encontrado com licença permitida")
    r = res[a.pick % len(res)]
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(requests.get(r["url"], headers=UA, timeout=300).content)
    add_credit(out, {
        "role": "music" if a.category == "music" else "sfx", "title": r.get("title"), "author": r.get("creator"),
        "source": r.get("source"), "url": r.get("foreign_landing_url"), "file_url": r.get("url"),
        "license": f"{r.get('license')} {r.get('license_version') or ''}".strip(), "license_url": r.get("license_url"),
        "attribution": r.get("attribution"), "notice": "made using Openverse",
        "modifications": "cortada, com fades, ducking e normalização de loudness",
    })
    print(json.dumps({"file": str(out), "title": r.get("title"), "license": r.get("license")}, ensure_ascii=False))


# ---------- cama procedural ----------
NOTES = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
PROGS = {
    "calm": [(0, [0, 4, 7, 11]), (9, [0, 3, 7, 10]), (5, [0, 4, 7, 11]), (7, [0, 5, 7, 10])],
    "uplift": [(0, [0, 4, 7]), (7, [0, 4, 7]), (9, [0, 3, 7]), (5, [0, 4, 7])],
    "tense": [(0, [0, 3, 7]), (8, [0, 4, 7]), (3, [0, 4, 7]), (10, [0, 4, 7])],
}


def generate(a):
    sr = 48000
    rng = np.random.default_rng(a.seed)
    beat = 60 / a.bpm
    bar = beat * 4
    n = int(a.sec * sr)
    t = np.arange(n) / sr
    root = 48 + NOTES[a.key]
    prog = PROGS[a.mood]
    L = np.zeros(n)
    R = np.zeros(n)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    for b in range(int(np.ceil(a.sec / bar))):
        deg, chord = prog[b % len(prog)]
        s0, s1 = int(b * bar * sr), min(int((b + 1) * bar * sr), n)
        tt = t[s0:s1] - b * bar
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (bar - tt) / 0.5)
        for iv in chord:
            f = hz(root + deg + iv + 12)
            L[s0:s1] += env * np.sin(2 * np.pi * f * 0.998 * tt) * 0.12
            R[s0:s1] += env * np.sin(2 * np.pi * f * 1.002 * tt) * 0.12
        bass = env * np.sin(2 * np.pi * hz(root + deg - 12) * tt) * 0.22
        L[s0:s1] += bass
        R[s0:s1] += bass
        for k in range(8):  # arpejo em colcheias, decaimento curto
            st = int((b * bar + k * beat / 2) * sr)
            if st >= n:
                break
            ln = min(int(0.45 * sr), n - st)
            ta = np.arange(ln) / sr
            iv = chord[(k * 2 + b) % len(chord)]
            note = np.sin(2 * np.pi * hz(root + deg + iv + 24) * ta) * np.exp(-ta * 7) * 0.07
            pan = 0.5 + 0.35 * np.sin(k)
            L[st:st + ln] += note * (1 - pan)
            R[st:st + ln] += note * pan
    ir_len = int(2.4 * sr)  # reverb por convolução com ruído decaindo
    ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / sr * 2.6)
    ir /= np.sqrt((ir ** 2).sum())
    wet = 0.35
    L = (1 - wet) * L + wet * signal.fftconvolve(L, ir)[:n]
    R = (1 - wet) * R + wet * signal.fftconvolve(R, ir[::-1].copy())[:n]
    st = np.stack([L, R], 1)
    fade = int(1.5 * sr)
    st[:fade] *= np.linspace(0, 1, fade)[:, None]
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    st *= 10 ** (-18 / 20) / (np.sqrt((st ** 2).mean()) or 1)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(out, sr, np.clip(st, -1, 1).astype(np.float32))
    add_credit(out, {"role": "music", "title": f"procedural {a.mood} {a.bpm} BPM em {a.key}", "author": "gerado por scripts/music.py",
                     "license": "sem direitos de terceiros", "seed": a.seed, "bpm": a.bpm, "attribution": None})
    print(json.dumps({"file": str(out), "sec": a.sec, "bpm": a.bpm}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("incompetech")
    p.add_argument("--feel", default="calm")
    p.add_argument("--bpm", default=None, help="faixa, ex.: 70-110")
    p.add_argument("--min-sec", type=int, default=30)
    p.add_argument("--pick", type=int, default=0)
    p.add_argument("-o", "--out", required=True)
    p = sub.add_parser("openverse")
    p.add_argument("--q", required=True)
    p.add_argument("--category", default="music", choices=["music", "sound_effect"])
    p.add_argument("--min-sec", type=int, default=0)
    p.add_argument("--pick", type=int, default=0)
    p.add_argument("--token", default=None, help="OAuth2 do Openverse (opcional, aumenta o limite)")
    p.add_argument("-o", "--out", required=True)
    p = sub.add_parser("generate")
    p.add_argument("--sec", type=float, required=True)
    p.add_argument("--bpm", type=int, default=84)
    p.add_argument("--key", default="D", choices=list(NOTES))
    p.add_argument("--mood", default="calm", choices=list(PROGS))
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    {"incompetech": incompetech, "openverse": openverse, "generate": generate}[a.cmd](a)


if __name__ == "__main__":
    main()
