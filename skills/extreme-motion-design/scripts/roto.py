#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy", "pillow"]
# ///
"""Rotoscopia: máscara por frame (PNG com alfa) e contornos SVG para roto estilizado.

  uv run scripts/roto.py footage.mp4 --backend mog2 -o public/roto --svg
  uv run --with "rembg[cpu]" scripts/roto.py footage.mp4 --backend rembg -o public/roto --svg
  uv run scripts/roto.py footage.mp4 --backend chroma --key 0,255,0 -o public/roto
Backends: rembg (pessoa ou objeto, modelo baixado do GitHub, 1 a 3 fps em CPU), mog2 (câmera fixa),
chroma (fundo de cor sólida). Qualidade de cinema: SAM 2 ou MatAnyone em GPU, mesma saída.
Saída: <out>/frame_00000.png (RGBA) e, com --svg, <out>/contours.json {fps,width,height,frames:[{f,paths}]}.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import cv2
import numpy as np


def mask_rembg(frame, session):
    from rembg import remove

    rgba = remove(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), session=session)
    return np.array(rgba)[:, :, 3]


def mask_chroma(frame, key, tol):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
    k = cv2.cvtColor(np.uint8([[key[::-1]]]), cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    d = np.linalg.norm(lab[:, :, 1:] - k[1:], axis=2)
    return np.clip((d - tol) / tol * 255, 0, 255).astype(np.uint8)


def to_paths(mask, eps=1.5, min_area=200):
    cnts, _ = cv2.findContours((mask > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    paths = []
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        p = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        paths.append("M " + " L ".join(f"{x},{y}" for x, y in p) + " Z")
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--backend", default="mog2", choices=["rembg", "mog2", "chroma"])
    ap.add_argument("--key", default="0,255,0", help="chroma: cor de fundo R,G,B")
    ap.add_argument("--tol", type=float, default=18.0)
    ap.add_argument("--feather", type=int, default=3, help="desfoque da borda em px")
    ap.add_argument("--svg", action="store_true")
    ap.add_argument("-o", "--out", default="public/roto")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    session = None
    if a.backend == "rembg":
        from rembg import new_session

        session = new_session("u2net")
    mog = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=24, detectShadows=False)
    key = [int(v) for v in a.key.split(",")]
    frames, i, w, h = [], 0, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        if a.backend == "rembg":
            m = mask_rembg(frame, session)
        elif a.backend == "chroma":
            m = mask_chroma(frame, key, a.tol)
        else:
            m = mog.apply(frame)
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        if a.feather:
            m = cv2.GaussianBlur(m, (a.feather * 2 + 1, a.feather * 2 + 1), 0)
        rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        rgba[:, :, 3] = m
        cv2.imwrite(str(out / f"frame_{i:05d}.png"), rgba)
        if a.svg:
            frames.append({"f": i, "paths": to_paths(m)})
        i += 1
    if a.svg:
        (out / "contours.json").write_text(json.dumps({"fps": fps, "width": w, "height": h, "frames": frames}), encoding="utf-8")
    print(json.dumps({"out": str(out), "frames": i, "backend": a.backend}))


if __name__ == "__main__":
    main()
