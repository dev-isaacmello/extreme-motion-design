#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Entrega: reencoda para h264 yuv420p (faixa TV), BT.709, faststart, AAC 48 kHz.

  uv run scripts/deliver.py out/render.mp4 -o out/final.mp4 --crf 18
O render do Remotion com frames JPEG sai em yuvj420p (faixa cheia); plataformas esperam faixa TV.
"""
from __future__ import annotations

import argparse
import subprocess


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args()
    cmd = [
        "ffmpeg", "-v", "error", "-y", "-i", a.src,
        "-vf", "scale=in_range=pc:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", a.out,
    ]
    subprocess.run(cmd, check=True)
    print(a.out)


if __name__ == "__main__":
    main()
