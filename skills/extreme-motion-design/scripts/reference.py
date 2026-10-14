#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["opencv-python-headless", "numpy", "pillow", "librosa>=0.10"]
# ///
"""Modo referência: desmonta um vídeo de referência em estrutura medida e mede o quanto a peça nova ficou parecida.

  uv run scripts/reference.py analyze referencia.mp4 -o reference          # reference.json, folha e keyframes
  uv run scripts/reference.py plan reference/reference.json -o roteiro.json   # esqueleto de roteiro com os mesmos tempos
  uv run scripts/reference.py compare reference/reference.json out/final.mp4 --timeline public/timeline.json
analyze extrai, por plano: início, fim, energia de movimento, movimento de câmera (zoom, pan, parado), paleta,
luminância, onde está a massa visual (grade 3x3) e três keyframes; do áudio: BPM, batidas, loudness e quantos
cortes caem na batida. A folha (sheet.png) é para o agente OLHAR: tipografia, tratamento e conteúdo não saem de número.
plan escreve um roteiro.json com uma cena por plano (planos curtos viram uma montagem), para o score.py.
compare analisa o vídeo novo do mesmo jeito e dá uma nota de fidelidade de 0 a 100, com a parcela de cada eixo.
A nota mede estrutura (ritmo, energia, composição, cor, câmera), não qualidade, e não mede conteúdo.
Reproduza estrutura, ritmo e técnica. Não copie asset, marca, texto nem quadro de terceiro: veja references/reference.md.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

import cv2
import numpy as np

SMALL = (160, 90)
MIN_SHOT = 0.2  # s: abaixo disso é flash, não plano
AXES = {"ritmo": 0.30, "energia": 0.25, "composicao": 0.15, "cor": 0.15, "camera": 0.10, "duracao": 0.05}


def hexc(bgr) -> str:
    return "#%02X%02X%02X" % (int(bgr[2]), int(bgr[1]), int(bgr[0]))


def lab_of(hexs: str) -> np.ndarray:
    rgb = np.uint8([[[int(hexs[5:7], 16), int(hexs[3:5], 16), int(hexs[1:3], 16)]]])
    return cv2.cvtColor(rgb, cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0] * np.array([100 / 255, 1, 1], np.float32)


def palette(frames: list[np.ndarray], k=5) -> list[dict]:
    px = np.concatenate([cv2.resize(f, (64, 64), interpolation=cv2.INTER_AREA).reshape(-1, 3) for f in frames]).astype(np.float32)
    lab = cv2.cvtColor(px.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    _, labels, _ = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0), 3, cv2.KMEANS_PP_CENTERS)
    labels = labels.reshape(-1)
    out = []
    for i in range(k):
        m = labels == i
        if m.sum():
            out.append({"hex": hexc(px[m].mean(0)), "share": round(float(m.mean()), 3)})
    out.sort(key=lambda c: -c["share"])
    merged: list[dict] = []
    for c in out:  # funde tons quase iguais para a paleta não virar cinco pretos
        near = next((m for m in merged if np.linalg.norm(lab_of(m["hex"]) - lab_of(c["hex"])) < 9), None)
        if near:
            near["share"] = round(near["share"] + c["share"], 3)
        else:
            merged.append(c)
    return merged


def saturation(hexs: str) -> float:
    lab = lab_of(hexs)
    return float(np.hypot(lab[1] - 128, lab[2] - 128))


def grid_of(gray: np.ndarray) -> tuple[list[float], float, float]:
    """Onde está a massa visual: energia de borda por célula de uma grade 3x3 e o centro de massa (0 a 1)."""
    e = cv2.magnitude(cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1))
    h, w = e.shape
    total = float(e.sum()) or 1.0
    cells = [float(e[r * h // 3:(r + 1) * h // 3, c * w // 3:(c + 1) * w // 3].sum() / total) for r in range(3) for c in range(3)]
    ys, xs = np.mgrid[0:h, 0:w]
    return [round(v, 3) for v in cells], round(float((e * xs).sum() / total / w), 3), round(float((e * ys).sum() / total / h), 3)


def camera_of(grays: list[np.ndarray]) -> dict:
    """Movimento de câmera do plano: escala e translação acumuladas entre frames (cantos + Lucas-Kanade + afim parcial)."""
    zoom, pan, used = 1.0, np.zeros(2), 0
    for a, b in zip(grays, grays[1:]):
        pts = cv2.goodFeaturesToTrack(a, 120, 0.01, 6)
        if pts is None or len(pts) < 12:
            continue
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(a, b, pts, None, winSize=(15, 15), maxLevel=2)
        good = st.reshape(-1) == 1
        if good.sum() < 12:
            continue
        M, _ = cv2.estimateAffinePartial2D(pts[good], nxt[good], method=cv2.RANSAC, ransacReprojThreshold=2.0)
        if M is None:
            continue
        s = float(np.hypot(M[0, 0], M[1, 0]))
        if 0.8 < s < 1.25:
            zoom *= s
            pan += M[:, 2] / np.array([a.shape[1], a.shape[0]])
            used += 1
    z, (px, py) = zoom - 1, pan
    kind = "parado"
    if used >= 2:
        if abs(z) > 0.04 and abs(z) >= 0.6 * max(abs(px), abs(py)):
            kind = "zoom in" if z > 0 else "zoom out"
        elif max(abs(px), abs(py)) > 0.05:
            kind = ("pan direita" if px < 0 else "pan esquerda") if abs(px) >= abs(py) else ("tilt baixo" if py < 0 else "tilt cima")
    return {"type": kind, "zoom": round(z, 3), "pan": [round(float(px), 3), round(float(py), 3)]}


def audio_of(path: str, cuts: list[float]) -> dict | None:
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    if not probe:
        return None
    import re

    import librosa

    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"I:\s+(-?[\d.]+) LUFS", err[err.rfind("Summary:"):])
    sr = 22050  # pelo ffmpeg: o librosa não abre MP4 direto
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-map", "0:a:0", "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    beats = [round(float(b), 3) for b in beats]
    on = sum(1 for c in cuts if beats and min(abs(c - b) for b in beats) <= 0.085)
    return {"lufs": float(m.group(1)) if m else None, "bpm": round(float(np.atleast_1d(tempo)[0]), 1), "beats": beats,
            "cuts_on_beat": round(on / len(cuts), 2) if cuts else None}


def analyze(path: str, out: pathlib.Path | None, with_audio=True, cuts_override: list[float] | None = None) -> dict:
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    small, grays, hists = [], [], []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        s = cv2.resize(f, SMALL, interpolation=cv2.INTER_AREA)
        small.append(s)
        grays.append(cv2.cvtColor(s, cv2.COLOR_BGR2GRAY))
        hsv = cv2.cvtColor(s, cv2.COLOR_BGR2HSV)
        hists.append(cv2.normalize(cv2.calcHist([hsv], [0, 1, 2], None, [8, 4, 4], [0, 180, 0, 256, 0, 256]), None).flatten())
    n = len(small)
    if n < 3:
        sys.exit(f"não consegui ler {path}")
    dur = n / fps
    g = np.stack(grays).astype(np.float32) / 255
    motion = np.concatenate([[0], np.abs(np.diff(g, axis=0)).mean((1, 2))])
    hd = np.array([0] + [cv2.compareHist(hists[i - 1], hists[i], cv2.HISTCMP_BHATTACHARYYA) for i in range(1, n)])
    if cuts_override is not None:
        cut_frames = sorted({int(round(c * fps)) for c in cuts_override if 0 < c < dur})
    else:
        # Corte seco: salto de histograma muito acima do vizinho e do ruído do próprio vídeo.
        med, mad = np.median(hd), np.median(np.abs(hd - np.median(hd))) + 1e-6
        thr = max(0.28, med + 8 * mad)
        cut_frames, last = [], -999
        for i in range(2, n - 1):
            if hd[i] > thr and hd[i] > 2.2 * max(hd[i - 1], hd[i + 1], 1e-6) and i - last >= MIN_SHOT * fps:
                cut_frames.append(i)
                last = i
    bounds = [0, *cut_frames, n]
    ref = float(np.percentile(motion, 90)) or 1e-6
    shots = []
    if out:
        out.mkdir(parents=True, exist_ok=True)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if b - a < 1:
            continue
        mid = (a + b) // 2
        picks = sorted({min(b - 1, a + 2), mid, max(a, b - 3)})
        seg = motion[a + 1:b] if b - a > 1 else motion[a:b]
        cells, cx, cy = grid_of(grays[mid])
        pal = palette([small[p] for p in picks])
        accent = max((c for c in pal if c["share"] >= 0.02), key=lambda c: saturation(c["hex"]), default=pal[0])
        step = max(1, (b - a) // 12)
        shot = {
            "i": i + 1, "start": round(a / fps, 3), "end": round(b / fps, 3), "dur": round((b - a) / fps, 3),
            "energy": round(float(seg.mean() / ref), 2) if len(seg) else 0.0,
            "peak_at": round(float(seg.argmax() / max(len(seg), 1)), 2) if len(seg) else 0.0,
            "camera": camera_of(grays[a:b:step]),
            "palette": pal, "bg": pal[0]["hex"], "accent": accent["hex"],
            "brightness": round(float(g[mid].mean()), 3),
            "layout": {"grid": cells, "cx": cx, "cy": cy},
        }
        if out:
            names = []
            for tag, p in zip("amz", [picks[0], mid, picks[-1]]):
                cap.set(cv2.CAP_PROP_POS_FRAMES, p)
                ok, full = cap.read()
                if ok:
                    name = f"shot_{i + 1:02d}_{tag}.png"
                    cv2.imwrite(str(out / name), cv2.resize(full, (360, round(360 * H / W / 2) * 2), interpolation=cv2.INTER_AREA))
                    names.append(name)
            shot["frames"] = names
        shots.append(shot)
    cuts = [s["start"] for s in shots[1:]]
    durs = [s["dur"] for s in shots]
    data = {
        "source": pathlib.Path(path).name, "duration": round(dur, 3), "fps": round(fps, 3), "width": W, "height": H,
        "aspect": "9:16" if W / H < 0.8 else "1:1" if W / H < 1.25 else "16:9",
        "rhythm": {"shots": len(shots), "asl": round(float(np.mean(durs)), 2), "shortest": min(durs), "longest": max(durs), "cuts": cuts},
        "palette": palette([small[i] for i in np.linspace(0, n - 1, min(n, 24)).astype(int)], k=6),
        "energy_curve": [round(float(v), 3) for v in np.interp(np.linspace(0, n - 1, 200), np.arange(n), np.convolve(motion / ref, np.ones(5) / 5, "same"))],
        "brightness_curve": [round(float(v), 3) for v in np.interp(np.linspace(0, n - 1, 100), np.arange(n), g.mean((1, 2)))],
        "audio": audio_of(path, cuts) if with_audio else None,
        "shots": shots,
    }
    return data


def sheet(data: dict, out: pathlib.Path):
    from PIL import Image, ImageDraw

    tiles = [(s, Image.open(out / s["frames"][1 if len(s["frames"]) > 1 else 0]).convert("RGB")) for s in data["shots"] if s.get("frames")]
    if not tiles:
        return
    w, h = tiles[0][1].size
    w, h = 240, round(240 * h / w)
    cols = min(8, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    pad, head = 8, 54
    img = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + head + pad) + pad), (24, 24, 24))
    d = ImageDraw.Draw(img)
    for k, (s, im) in enumerate(tiles):
        x, y = pad + (k % cols) * (w + pad), pad + (k // cols) * (h + head + pad)
        img.paste(im.resize((w, h)), (x, y + head))
        d.text((x, y + 2), f"#{s['i']}  {s['start']:.2f}s  dur {s['dur']:.2f}s", fill=(235, 235, 235))
        d.text((x, y + 16), f"{s['camera']['type']}  energia {s['energy']}", fill=(180, 180, 180))
        for j, c in enumerate(s["palette"][:5]):
            d.rectangle([x + j * 22, y + 34, x + j * 22 + 18, y + 48], fill=c["hex"])
    img.save(out / "sheet.png")


def cmd_analyze(a):
    out = pathlib.Path(a.out)
    data = analyze(a.video, out)
    (out / "reference.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    sheet(data, out)
    au = data["audio"] or {}
    print(json.dumps({"out": str(out / "reference.json"), "sheet": str(out / "sheet.png"), "duration": data["duration"], "aspect": data["aspect"],
                      "shots": data["rhythm"]["shots"], "asl": data["rhythm"]["asl"], "bpm": au.get("bpm"), "cuts_on_beat": au.get("cuts_on_beat"),
                      "palette": [c["hex"] for c in data["palette"][:5]]}, ensure_ascii=False))
    print("olhe a folha: tipografia, tratamento e o que cada plano mostra não saem de número", file=sys.stderr)


def cmd_plan(a):
    R = json.loads(pathlib.Path(a.reference).read_text(encoding="utf-8"))
    scenes, group = [], []

    def flush():
        if group:
            scenes.append({"id": f"montagem{len(scenes) + 1:02d}", "dur": round(sum(s["dur"] for s in group), 3),
                           "reference": {"shots": [s["i"] for s in group], "note": f"{len(group)} planos de {min(s['dur'] for s in group):.2f} a {max(s['dur'] for s in group):.2f} s: um corte por batida"}})
            group.clear()

    for s in R["shots"]:
        if s["dur"] < a.montage:
            group.append(s)
            continue
        flush()
        scenes.append({"id": f"cena{len(scenes) + 1:02d}", "dur": s["dur"],
                       "reference": {"shot": s["i"], "camera": s["camera"]["type"], "energy": s["energy"], "bg": s["bg"], "accent": s["accent"],
                                     "mass": [s["layout"]["cx"], s["layout"]["cy"]]}})
    flush()
    au = R.get("audio") or {}
    fmt = {"9:16": "reels", "1:1": "square"}.get(R["aspect"], "youtube")
    roteiro = {"format": fmt, "fps": 30, "duration": R["duration"], "voice": {"provider": "none"},
               "cut": {"on": "phrase", "lead": 0.2},
               "reference": {"source": R["source"], "bpm": au.get("bpm"), "cuts_on_beat": au.get("cuts_on_beat"), "palette": [c["hex"] for c in R["palette"][:5]]},
               "scenes": scenes}
    pathlib.Path(a.out).write_text(json.dumps(roteiro, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": a.out, "scenes": len(scenes), "duration": R["duration"], "bpm": au.get("bpm")}, ensure_ascii=False))
    print("as cenas saem sem fala e com a duração da referência: ponha voz, texto e marcas, e troque os ids por nomes", file=sys.stderr)


def corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() < 1e-6 or b.std() < 1e-6:
        return 1.0 if a.std() < 1e-6 and b.std() < 1e-6 else 0.0
    return float(np.corrcoef(a, b)[0, 1])


def cmd_compare(a):
    R = json.loads(pathlib.Path(a.reference).read_text(encoding="utf-8"))
    cuts = None
    if a.timeline:  # motion graphics troca de cena sem corte seco: valem as fronteiras da partitura
        cuts = [s["start"] for s in json.loads(pathlib.Path(a.timeline).read_text(encoding="utf-8"))["scenes"][1:]]
    N = analyze(a.video, None, with_audio=False, cuts_override=cuts)
    skip = set(a.skip.split(",")) if a.skip else set()
    out = {}
    out["duracao"] = max(0.0, 1 - abs(N["duration"] - R["duration"]) / R["duration"])
    rc, nc = [c / R["duration"] for c in R["rhythm"]["cuts"]], [c / N["duration"] for c in N["rhythm"]["cuts"]]
    if rc and nc:
        tol = 0.5 / max(len(rc), 1) * 0.5  # um quarto do plano médio da referência
        hit = lambda xs, ys: float(np.mean([max(0.0, 1 - min(abs(x - y) for y in ys) / tol) for x in xs]))  # noqa: E731
        out["ritmo"] = 0.5 * (hit(rc, nc) + hit(nc, rc))
    else:
        out["ritmo"] = 1.0 if not rc and not nc else 0.0
    out["energia"] = max(0.0, corr(R["energy_curve"], N["energy_curve"]))

    def at(shots, total, t):
        return next((s for s in shots if s["start"] / total <= t < s["end"] / total), shots[-1])

    pairs = [(s, at(N["shots"], N["duration"], (s["start"] + s["end"]) / 2 / R["duration"])) for s in R["shots"]]
    w = np.array([s["dur"] for s, _ in pairs])
    out["composicao"] = float(np.average([max(0.0, corr(s["layout"]["grid"], n["layout"]["grid"])) for s, n in pairs], weights=w))
    out["camera"] = float(np.average([1.0 if s["camera"]["type"] == n["camera"]["type"] else 0.5 if s["camera"]["type"].split()[0] == n["camera"]["type"].split()[0] else 0.0 for s, n in pairs], weights=w))
    npal = [lab_of(c["hex"]) for c in N["palette"]]
    out["cor"] = float(sum(c["share"] * max(0.0, 1 - min(np.linalg.norm(lab_of(c["hex"]) - p) for p in npal) / 45) for c in R["palette"]) / sum(c["share"] for c in R["palette"]))
    axes = {k: v for k, v in AXES.items() if k not in skip}
    total = sum(out[k] * v for k, v in axes.items()) / sum(axes.values())
    rows = [{"axis": k, "score": round(out[k] * 100), "weight": AXES[k], "counted": k not in skip} for k in AXES]
    detail = {"reference": {"duration": R["duration"], "shots": R["rhythm"]["shots"], "asl": R["rhythm"]["asl"]},
              "video": {"duration": N["duration"], "shots": N["rhythm"]["shots"], "asl": N["rhythm"]["asl"]}}
    score = round(total * 100)
    if a.json:
        print(json.dumps({"fidelity": score, "axes": rows, **detail}, ensure_ascii=False, indent=1))
    else:
        print(f"referência: {R['duration']:.1f} s, {R['rhythm']['shots']} planos, plano médio {R['rhythm']['asl']} s")
        print(f"vídeo:      {N['duration']:.1f} s, {N['rhythm']['shots']} planos, plano médio {N['rhythm']['asl']} s")
        for r in rows:
            print(f"  {r['axis']:11s} {r['score']:3d}  peso {r['weight']:.2f}" + ("" if r["counted"] else "  (fora da nota)"))
        print(json.dumps({"fidelity": score, "min": a.min, "pass": score >= a.min}))
    sys.exit(0 if score >= a.min else 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("analyze", help="desmonta o vídeo de referência")
    p.add_argument("video")
    p.add_argument("-o", "--out", default="reference")
    p.set_defaults(fn=cmd_analyze)
    p = sub.add_parser("plan", help="esqueleto de roteiro.json com os tempos da referência")
    p.add_argument("reference")
    p.add_argument("-o", "--out", default="roteiro.reference.json")
    p.add_argument("--montage", type=float, default=0.7, help="planos mais curtos que isto viram uma cena de montagem")
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("compare", help="nota de fidelidade do vídeo novo contra a referência")
    p.add_argument("reference")
    p.add_argument("video")
    p.add_argument("--timeline", default=None, help="timeline.json do vídeo novo: usa as fronteiras de cena como cortes")
    p.add_argument("--skip", default=None, help="eixos fora da nota, separados por vírgula (ex.: cor quando a marca manda na paleta)")
    p.add_argument("--min", type=int, default=0, help="nota mínima; abaixo dela sai com código 1")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_compare)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
