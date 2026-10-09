#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Entrega: garante h264 yuv420p (faixa TV), AAC 48 kHz e faststart sem reencodar o que já está certo.

  uv run scripts/deliver.py out/render.mp4 -o out/final.mp4
O render do Remotion já sai em yuv420p faixa TV: nesse caso o vídeo é copiado sem perda.
Só há reencode quando o arquivo chega em faixa cheia (yuvj420p) ou em outro pixel format.
Renderize com --color-space=bt709 (o template já configura) para o arquivo sair com a cor marcada.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", path], capture_output=True, text=True, check=True).stdout
    streams = json.loads(out)["streams"]
    v = next((s for s in streams if s["codec_type"] == "video"), None)
    a = next((s for s in streams if s["codec_type"] == "audio"), None)
    return v, a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    a = ap.parse_args()
    v, au = probe(a.src)
    if v is None:
        sys.exit("sem stream de vídeo")
    pix, rng = v.get("pix_fmt"), v.get("color_range")
    full = pix == "yuvj420p" or rng == "pc"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.src]
    if v["codec_name"] == "h264" and pix == "yuv420p" and not full:
        cmd += ["-c:v", "copy"]
        modo = "vídeo copiado sem reencode"
        if v.get("color_space") != "bt709":
            print("WARN  cor sem marca BT.709: renderize com --color-space=bt709", file=sys.stderr)
    else:
        # Comprimir a faixa só quando a origem é faixa cheia: aplicar em faixa TV lava o contraste.
        vf = "scale=in_range=pc:out_range=tv,format=yuv420p" if full else "format=yuv420p"
        cmd += [
            "-vf", vf, "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        ]
        modo = f"vídeo reencodado ({pix}, faixa {'cheia' if full else rng or 'não marcada'})"
    if au is not None and au["codec_name"] == "aac" and au.get("sample_rate") == "48000":
        cmd += ["-c:a", "copy"]
    elif au is not None:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(modo, file=sys.stderr)
    print(a.out)


if __name__ == "__main__":
    main()
