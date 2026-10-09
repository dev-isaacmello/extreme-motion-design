#!/usr/bin/env python3
"""Mede qual backend gráfico do Chrome renderiza este projeto mais rápido nesta máquina e imprime a flag.

  python3 <skill>/scripts/gl.py Showcase            # imprime "--gl=vulkan" ou nada
  npx remotion render Showcase out/render.mp4 --codec=h264 --audio-codec=aac $(python3 <skill>/scripts/gl.py Showcase)
Rode na pasta do projeto. Renderiza um trecho com o backend padrão e com cada candidato, e só troca o
padrão por um que seja ao menos 20% mais rápido e dê a mesma imagem (SSIM). O resultado fica em out/gl.json;
--force mede de novo. Flag fixa não serve: sem GPU, --gl=vulkan cai em software sem avisar e dobra o tempo.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import time

CANDIDATES = ["vulkan", "angle-egl"]


def render(comp, gl, frames, out, timeout):
    cmd = ["npx", "remotion", "render", comp, str(out), f"--frames={frames}", "--muted", "--log=error"]
    if gl:
        cmd.append(f"--gl={gl}")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None
    return time.time() - t0 if r.returncode == 0 and out.exists() else None


def ssim(a, b):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(a), "-i", str(b), "-lavfi", "ssim", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"All:([\d.]+)", err)
    return float(m.group(1)) if m else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("composition")
    ap.add_argument("--timeline", default="public/timeline.json")
    ap.add_argument("--frames", type=int, default=150, help="tamanho do trecho medido")
    ap.add_argument("--min-ssim", type=float, default=0.99)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    cache = pathlib.Path("out/gl.json")
    if cache.exists() and not a.force:
        gl = json.loads(cache.read_text(encoding="utf-8")).get("gl")
        print(f"--gl={gl}" if gl else "")
        return

    total = 0
    tl = pathlib.Path(a.timeline)
    if tl.exists():
        j = json.loads(tl.read_text(encoding="utf-8"))
        total = int(j["duration"] * j["fps"])
    n = min(a.frames, total) if total else a.frames
    start = max(0, int(total * 0.2)) if total > n else 0
    frames = f"{start}-{start + n - 1}"

    tmp = pathlib.Path("out/gl")
    tmp.mkdir(parents=True, exist_ok=True)
    base = render(a.composition, None, frames, tmp / "padrao.mp4", 600)
    if base is None:
        sys.exit("o render de teste com o backend padrão falhou: rode o render normal para ver o erro")
    rows, best, best_t = [{"gl": None, "sec": round(base, 1)}], None, base * 0.8
    for gl in CANDIDATES:
        out = tmp / f"{gl}.mp4"
        t = render(a.composition, gl, frames, out, max(60, base * 3))
        row = {"gl": gl, "sec": round(t, 1) if t else None, "ssim": round(ssim(tmp / "padrao.mp4", out), 4) if t else None}
        rows.append(row)
        if t and row["ssim"] >= a.min_ssim and t < best_t:
            best, best_t = gl, t
    for f in tmp.glob("*.mp4"):
        f.unlink()
    tmp.rmdir()
    cache.write_text(json.dumps({"gl": best, "frames": frames, "medido": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(f"{r['gl'] or 'padrão':10s} {r['sec']} s" + (f"  SSIM {r['ssim']}" if r.get("ssim") is not None else ""), file=sys.stderr)
    print(f"escolhido: {best or 'padrão'}", file=sys.stderr)
    print(f"--gl={best}" if best else "")


if __name__ == "__main__":
    main()
