#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy"]
# ///
"""Motion tracking com OpenCV -> JSON para <Tracked> (ponto) e <CornerPin> (plano).

  uv run scripts/track.py footage.mp4 --point 812,430 -o public/track/logo.json --smooth 5
  uv run scripts/track.py footage.mp4 --quad 100,80,600,90,610,400,95,390 -o public/track/screen.json
Ponto: Lucas-Kanade sobre cantos em volta do ponto, deslocamento pela mediana, recarrega cantos quando somem.
Plano: cantos dentro do quadrilátero, homografia RANSAC por frame contra a referência, cantos transformados.
Coordenadas em px do vídeo; use --scale se a composição tiver outra resolução.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import cv2
import numpy as np

LK = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))


def features(gray, mask, n=200):
    p = cv2.goodFeaturesToTrack(gray, maxCorners=n, qualityLevel=0.01, minDistance=5, mask=mask)
    return p if p is not None else np.empty((0, 1, 2), np.float32)


def smooth(vals: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return vals
    pad = np.pad(vals, ((k // 2, k - 1 - k // 2), (0, 0)), mode="edge")
    ker = np.ones(k) / k
    return np.stack([np.convolve(pad[:, i], ker, mode="valid") for i in range(vals.shape[1])], 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--point", help="x,y no frame inicial")
    g.add_argument("--quad", help="x0,y0,x1,y1,x2,y2,x3,y3 (TL, TR, BR, BL)")
    ap.add_argument("--radius", type=int, default=40)
    ap.add_argument("--smooth", type=int, default=1)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    ok, frame = cap.read()
    if not ok:
        raise SystemExit("não consegui ler o vídeo")
    prev = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = prev.shape
    out = []

    if a.point:
        x, y = (float(v) for v in a.point.split(","))
        def roi(cx, cy):
            m = np.zeros_like(prev)
            cv2.circle(m, (int(cx), int(cy)), a.radius, 255, -1)
            return m
        pts = features(prev, roi(x, y))
        out.append([x, y])
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if len(pts) >= 4:
                nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray, pts, None, **LK)
                good = st.reshape(-1) == 1
                if good.sum() >= 3:
                    d = np.median((nxt[good] - pts[good]).reshape(-1, 2), axis=0)
                    x, y = x + float(d[0]), y + float(d[1])
                    pts = nxt[good].reshape(-1, 1, 2)
            if len(pts) < 8:
                pts = features(gray, roi(x, y))
            out.append([x, y])
            prev = gray
        arr = smooth(np.array(out), a.smooth) * a.scale
        data = {"fps": fps, "width": w * a.scale, "height": h * a.scale, "frames": [{"f": i, "x": round(float(p[0]), 2), "y": round(float(p[1]), 2)} for i, p in enumerate(arr)]}
    else:
        quad = np.array([float(v) for v in a.quad.split(",")], np.float32).reshape(4, 2)
        mask = np.zeros_like(prev)
        cv2.fillConvexPoly(mask, quad.astype(np.int32), 255)
        ref_pts = features(prev, mask, 400)
        ref_quad = quad.copy()
        pts = ref_pts.copy()
        out.append(quad.reshape(-1).tolist())
        cur_quad = quad
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray, pts, None, **LK)
            good = st.reshape(-1) == 1
            if good.sum() >= 8:
                H, inl = cv2.findHomography(ref_pts[good].reshape(-1, 2), nxt[good].reshape(-1, 2), cv2.RANSAC, 3.0)
                if H is not None:
                    cur_quad = cv2.perspectiveTransform(ref_quad.reshape(-1, 1, 2), H).reshape(4, 2)
                ref_pts, pts = ref_pts[good], nxt[good]
            if len(pts) < 30:  # recarrega e troca a referência para o frame atual
                mask = np.zeros_like(gray)
                cv2.fillConvexPoly(mask, cur_quad.astype(np.int32), 255)
                ref_pts = features(gray, mask, 400)
                pts = ref_pts.copy()
                ref_quad = cur_quad.copy()
            out.append(cur_quad.reshape(-1).tolist())
            prev = gray
        arr = smooth(np.array(out), a.smooth) * a.scale
        data = {"fps": fps, "width": w * a.scale, "height": h * a.scale, "frames": [{"f": i, "corners": [round(float(v), 2) for v in c]} for i, c in enumerate(arr)]}

    path = pathlib.Path(a.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    print(json.dumps({"out": str(path), "frames": len(data["frames"]), "fps": fps}))


if __name__ == "__main__":
    main()
