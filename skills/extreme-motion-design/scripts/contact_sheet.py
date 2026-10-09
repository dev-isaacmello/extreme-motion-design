#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""Folha de contato (dailies): frames-chave do vídeo numa grade com timecode, para revisão visual.

  uv run scripts/contact_sheet.py out/video.mp4 --timeline public/timeline.json -o out/sheet.png
  uv run scripts/contact_sheet.py out/video.mp4 --every 0.5 -o out/sheet.png
  uv run scripts/contact_sheet.py --stills out/stills -o out/sheet.png     # a partir do stills.cjs, sem MP4
Com --timeline, pega início (+0,15 s), meio e fim (-0,15 s) de cada cena: é onde entradas,
saídas e cortes quebram. Depois abra a imagem e revise com o checklist de references/qa.md.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import tempfile

from PIL import Image, ImageDraw


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--stills", help="pasta gerada pelo stills.cjs (dispensa o vídeo)")
    ap.add_argument("--timeline")
    ap.add_argument("--every", type=float, default=None)
    ap.add_argument("--times", default=None, help="lista em segundos: 0.5,1.2,3")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("-o", "--out", default="out/contact_sheet.png")
    a = ap.parse_args()
    if a.stills:
        d = pathlib.Path(a.stills)
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))["stills"]
        tiles = []
        for it in idx:
            im = Image.open(d / it["file"]).convert("RGB")
            tiles.append((it["t"], im.resize((a.width, round(im.height * a.width / im.width / 2) * 2))))
        return save(tiles, a)
    if not a.video:
        ap.error("informe o vídeo ou --stills")
    total = duration(a.video)
    if a.times:
        times = [float(x) for x in a.times.split(",")]
    elif a.timeline:
        tl = json.loads(pathlib.Path(a.timeline).read_text(encoding="utf-8"))
        times = []
        for s in tl["scenes"]:
            times += [s["start"] + 0.15, (s["start"] + s["end"]) / 2, s["end"] - 0.15]
    else:
        step = a.every or max(total / 12, 0.25)
        times = [round(i * step, 3) for i in range(int(total / step) + 1)]
    times = [min(max(t, 0), total - 0.05) for t in times]
    tiles = []
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(times):
            p = pathlib.Path(td) / f"{i}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1", "-vf", f"scale={a.width}:-2", str(p)], check=True)
            tiles.append((t, Image.open(p).convert("RGB")))
    save(tiles, a)


def save(tiles, a):
    w, h = tiles[0][1].size
    rows = (len(tiles) + a.cols - 1) // a.cols
    pad = 8
    sheet = Image.new("RGB", (a.cols * (w + pad) + pad, rows * (h + pad + 22) + pad), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for i, (t, im) in enumerate(tiles):
        x = pad + (i % a.cols) * (w + pad)
        y = pad + (i // a.cols) * (h + pad + 22)
        sheet.paste(im, (x, y + 22))
        draw.text((x, y + 4), f"#{i + 1}  {t:6.2f}s", fill=(230, 230, 230))
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
