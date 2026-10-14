#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy"]
# ///
"""Motion tracking com OpenCV -> JSON para <Tracked> (ponto) e <CornerPin> (plano).

  uv run scripts/track.py footage.mp4 --point 812,430 -o public/track/logo.json --smooth 5
  uv run scripts/track.py footage.mp4 --quad 100,80,600,90,610,400,95,390 -o public/track/screen.json
  uv run scripts/track.py footage.mp4 --face -o public/track/rosto.json --smooth 5              # maior rosto
  uv run scripts/track.py footage.mp4 --face 120,300 -o public/track/pessoa.json                 # rosto mais perto do ponto
  uv run --with mediapipe scripts/track.py footage.mp4 --hand -o public/track/mao.json --smooth 3
Ponto: Lucas-Kanade sobre cantos em volta do ponto, deslocamento pela mediana, recarrega cantos quando somem.
Plano: cantos dentro do quadrilátero, homografia RANSAC por frame contra a referência, cantos transformados.
Rosto: detector YuNet (OpenCV Zoo, MIT, 230 KB baixados uma vez) em todo frame; segue o rosto escolhido pelo vizinho
mais próximo. Sai centro (x, y), largura e altura da caixa e roll em graus (inclinação da linha dos olhos).
Mão: MediaPipe Hand Landmarker (Apache-2.0, 7,5 MB baixados uma vez). Sai o centro da palma (x, y), tamanho (w),
ângulo do punho ao dedo médio (roll), ponta do indicador (ix, iy), ponta do polegar (tx, ty) e pinch (distância
entre as duas dividida pelo tamanho da mão: abaixo de 0,35 os dedos estão juntos).
Em rosto e mão, frame sem detecção ganha "found": false e valor interpolado entre os vizinhos: use para esconder
o elemento, não para fingir que rastreou. Câmera na mão e gesto rápido pedem --smooth 3 a 5.
Coordenadas em px do vídeo; use --scale se a composição tiver outra resolução.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import hashlib
import os
import urllib.request

import cv2
import numpy as np

CACHE = pathlib.Path(os.environ.get("MOTION_DESIGN_CACHE", pathlib.Path.home() / ".cache" / "motion-design"))
YUNET = ("https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
         "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4")
HAND = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", None)


def model(name: str, url: str, sha: str | None) -> str:
    f = CACHE / name
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        print(f"baixando {url}", flush=True)
        urllib.request.urlretrieve(url, f.with_suffix(".part"))
        f.with_suffix(".part").rename(f)
    if sha and hashlib.sha256(f.read_bytes()).hexdigest() != sha:
        f.unlink()
        raise SystemExit(f"{name}: o arquivo baixado não confere com o hash esperado")
    return str(f)


def fill(rows: list[dict | None], keys: list[str], k: int, scale: float) -> list[dict]:
    """Interpola os frames sem detecção, suaviza e marca found."""
    found = np.array([r is not None for r in rows])
    if not found.any():
        raise SystemExit("nada foi detectado em nenhum frame")
    idx = np.arange(len(rows))
    cols = [np.interp(idx, idx[found], [rows[i][key] for i in idx[found]]) for key in keys]
    arr = smooth(np.stack(cols, 1), k)
    out = []
    for i in range(len(rows)):
        d = {"f": i, "found": bool(found[i])}
        for j, key in enumerate(keys):
            d[key] = round(float(arr[i, j]) * (1.0 if key in ("roll", "pinch") else scale), 2)
        out.append(d)
    return out


def track_face(cap, first, near, k, scale):
    h, w = first.shape[:2]
    det = cv2.FaceDetectorYN.create(model("yunet.onnx", *YUNET), "", (w, h), 0.6, 0.3, 50)
    rows, last, frame = [], near, first
    while True:
        _, faces = det.detect(frame)
        pick = None
        if faces is not None and len(faces):
            cands = [f for f in faces]
            # sem ponto de partida vale o maior rosto; depois, o mais perto de onde ele estava
            pick = max(cands, key=lambda f: f[2] * f[3]) if last is None else min(cands, key=lambda f: (f[0] + f[2] / 2 - last[0]) ** 2 + (f[1] + f[3] / 2 - last[1]) ** 2)
            cx, cy = pick[0] + pick[2] / 2, pick[1] + pick[3] / 2
            if last is not None and np.hypot(cx - last[0], cy - last[1]) > 0.8 * max(pick[2], pick[3]) and rows and rows[-1] is not None:
                pick = None  # pulou para outro rosto: conta como frame sem detecção
        if pick is None:
            rows.append(None)
        else:
            cx, cy = float(pick[0] + pick[2] / 2), float(pick[1] + pick[3] / 2)
            roll = float(np.degrees(np.arctan2(pick[7] - pick[5], pick[6] - pick[4])))  # olho direito -> olho esquerdo da imagem
            rows.append({"x": cx, "y": cy, "w": float(pick[2]), "h": float(pick[3]), "roll": roll})
            last = (cx, cy)
        ok, frame = cap.read()
        if not ok:
            break
    return fill(rows, ["x", "y", "w", "h", "roll"], k, scale)


def track_hand(cap, first, near, k, scale, fps):
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
    except ImportError:
        raise SystemExit("--hand usa o MediaPipe: rode com `uv run --with mediapipe scripts/track.py ...`")
    h, w = first.shape[:2]
    opts = vision.HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=model("hand_landmarker.task", *HAND)),
                                        running_mode=vision.RunningMode.VIDEO, num_hands=2, min_hand_detection_confidence=0.4, min_tracking_confidence=0.4)
    rows, last, frame, i = [], near, first, 0
    with vision.HandLandmarker.create_from_options(opts) as lm:
        while True:
            res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
            best = None
            for hand in res.hand_landmarks:
                p = np.array([[q.x * w, q.y * h] for q in hand])
                c = p[[0, 5, 9, 13, 17]].mean(0)  # punho e base dos dedos: o centro da palma
                if best is None or (last is not None and np.hypot(*(c - last)) < np.hypot(*(best[1] - last))):
                    best = (p, c)
            if best is None:
                rows.append(None)
            else:
                p, c = best
                size = float(np.hypot(*(p[9] - p[0])))
                rows.append({"x": float(c[0]), "y": float(c[1]), "w": size, "roll": float(np.degrees(np.arctan2(p[9][1] - p[0][1], p[9][0] - p[0][0]))),
                             "ix": float(p[8][0]), "iy": float(p[8][1]), "tx": float(p[4][0]), "ty": float(p[4][1]),
                             "pinch": float(np.hypot(*(p[8] - p[4])) / max(size, 1))})
                last = c
            ok, frame = cap.read()
            i += 1
            if not ok:
                break
    return fill(rows, ["x", "y", "w", "roll", "ix", "iy", "tx", "ty", "pinch"], k, scale)

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
    g.add_argument("--face", nargs="?", const="", help="rastreia um rosto; opcional x,y perto do rosto no primeiro frame")
    g.add_argument("--hand", nargs="?", const="", help="rastreia uma mão (MediaPipe); opcional x,y perto dela")
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

    if a.face is not None or a.hand is not None:
        arg = a.face if a.face is not None else a.hand
        near = tuple(float(v) for v in arg.split(",")) if arg else None
        frames = track_face(cap, frame, near, a.smooth, a.scale) if a.face is not None else track_hand(cap, frame, near, a.smooth, a.scale, fps)
        lost = sum(not f["found"] for f in frames)
        path = pathlib.Path(a.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"fps": fps, "width": w * a.scale, "height": h * a.scale, "kind": "face" if a.face is not None else "hand", "frames": frames}), encoding="utf-8")
        print(json.dumps({"out": str(path), "frames": len(frames), "fps": fps, "sem_deteccao": lost}))
        return

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
