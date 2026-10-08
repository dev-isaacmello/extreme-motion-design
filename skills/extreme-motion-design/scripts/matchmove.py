#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy"]
# ///
"""Match moving planar: cantos rastreados (track.py --quad) + tamanho real do plano -> câmera por frame.

  uv run scripts/matchmove.py public/track/screen.json --plane 0.07x0.15 --fov 60 --size 1920x1080 -o public/track/camera.json
  uv run scripts/matchmove.py --selftest
Saída no sistema do Three.js: {fps, fov, frames: [{f, position: [x,y,z], quaternion: [x,y,z,w]}]}.
O plano fica em z = 0, centrado na origem, largura no eixo x, y para cima. fov é vertical, como no Three.js.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import cv2
import numpy as np

S = np.diag([1.0, -1.0, -1.0])  # OpenCV (y para baixo, z para frente) -> Three.js (y para cima, z para trás)


def intrinsics(w, h, fov_v):
    f = (h / 2) / math.tan(math.radians(fov_v) / 2)
    return np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], float)


def plane_points(pw, ph):
    return np.array([[-pw / 2, -ph / 2, 0], [pw / 2, -ph / 2, 0], [pw / 2, ph / 2, 0], [-pw / 2, ph / 2, 0]], float)


def quat(R):
    tr = R[0, 0] + R[1, 1] + R[2, 2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [(R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s]
    i = int(np.argmax([R[0, 0], R[1, 1], R[2, 2]]))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1.0 + R[i, i] - R[j, j] - R[k, k]) * 2
    q = [0.0, 0.0, 0.0, (R[k, j] - R[j, k]) / s]
    q[i] = 0.25 * s
    q[j] = (R[j, i] + R[i, j]) / s
    q[k] = (R[k, i] + R[i, k]) / s
    return q


def solve(corners, K, obj):
    img = np.array(corners, float).reshape(4, 2)
    ok, rvec, tvec = cv2.solvePnP(obj, img, K, None, flags=cv2.SOLVEPNP_IPPE)
    if not ok:
        return None
    R, _ = cv2.Rodrigues(rvec)
    C = (-R.T @ tvec).reshape(3)  # centro da câmera no sistema do plano (OpenCV)
    R3 = S @ R.T @ S  # rotação câmera->mundo no Three.js
    return (S @ C).tolist(), quat(R3)


def selftest():
    K = intrinsics(1920, 1080, 50)
    obj = plane_points(1.6, 0.9)
    rvec = np.array([0.25, -0.35, 0.05])
    tvec = np.array([0.1, -0.05, 3.0])
    img, _ = cv2.projectPoints(obj, rvec, tvec, K, None)
    pos, q = solve(img.reshape(-1).tolist(), K, obj)
    R, _ = cv2.Rodrigues(rvec)
    expected = (S @ (-R.T @ tvec)).tolist()
    err = float(np.linalg.norm(np.array(pos) - np.array(expected)) / np.linalg.norm(expected))
    print(json.dumps({"position": [round(v, 4) for v in pos], "expected": [round(v, 4) for v in expected], "rel_error": err}))
    raise SystemExit(0 if err < 0.01 else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", nargs="?")
    ap.add_argument("--plane", default="1.6x0.9", help="largura x altura reais do plano (qualquer unidade)")
    ap.add_argument("--fov", type=float, default=50.0, help="fov vertical da câmera em graus")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("-o", "--out", default="public/track/camera.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    tr = json.loads(pathlib.Path(a.track).read_text(encoding="utf-8"))
    w, h = (int(v) for v in a.size.split("x"))
    pw, ph = (float(v) for v in a.plane.split("x"))
    K, obj = intrinsics(w, h, a.fov), plane_points(pw, ph)
    frames = []
    for fr in tr["frames"]:
        r = solve(fr["corners"], K, obj)
        if r:
            frames.append({"f": fr["f"], "position": [round(v, 5) for v in r[0]], "quaternion": [round(v, 6) for v in r[1]]})
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"fps": tr.get("fps", 30), "fov": a.fov, "frames": frames}), encoding="utf-8")
    print(json.dumps({"out": str(out), "frames": len(frames)}))


if __name__ == "__main__":
    main()
