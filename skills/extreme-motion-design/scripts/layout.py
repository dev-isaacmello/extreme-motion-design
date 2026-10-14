#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pillow"]
# ///
"""QA de layout sobre os stills: mede o texto de verdade, em vez de confiar no olho.

  uv run scripts/layout.py out/stills                               # lê index.json, layout.json e os PNG
  uv run scripts/layout.py out/stills --timeline public/timeline.json   # também compara as cenas entre si
  uv run scripts/layout.py out/stills --json
Entrada: a pasta do stills.cjs. layout.json vem da sonda <Probe /> (caixa, tamanho, cor e visibilidade de cada
texto no DOM); a cor de fundo sai dos pixels do PNG. Só julga texto assentado (visível, opaco, sem blur): texto
no meio de uma entrada não conta. Texto ornamental que sangra do quadro de propósito leva data-decor e é ignorado.
Reprova (FAIL): texto cortado pela borda, fora da área de ação, sobreposto a outro texto, menor que o mínimo
legível ou com contraste abaixo de 3:1. Avisa (WARN): fora da área segura de texto, contraste abaixo de 4,5:1,
letra pequena e cenas com a mesma espinha de composição. Sai com código 1 se houver FAIL.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import numpy as np
from PIL import Image

SETTLED = {"vis": 0.88, "op": 0.9, "blur": 2.0}
MIN_FONT_FAIL, MIN_FONT_WARN = 20, 28  # px no lado menor de 1080: abaixo disso não se lê no celular
OVERLAP = 0.15
SAME_PAIR, SAME_ALL = 0.90, 0.80  # correlação entre miniaturas de cenas


def lum(rgb):
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def parse_color(s: str):
    m = re.findall(r"[\d.]+", s or "")
    if len(m) < 3:
        return None, 0.0
    return tuple(float(x) for x in m[:3]), (float(m[3]) if len(m) > 3 else 1.0)


def background(img: np.ndarray, fg) -> tuple[tuple, float]:
    """Cor de fundo da caixa do texto: a cor dominante que não é a do próprio texto, e quanto da caixa ela cobre."""
    px = img.reshape(-1, 3).astype(float)
    bins = (px // 24).astype(int)
    code = bins[:, 0] * 10000 + bins[:, 1] * 100 + bins[:, 2]
    keys, counts = np.unique(code, return_counts=True)
    for k in keys[np.argsort(-counts)][:4]:
        mean = px[code == k].mean(0)
        if np.linalg.norm(mean - np.asarray(fg)) > 28:  # mais perto que isso é o próprio glifo
            return tuple(mean), float((code == k).mean())
    return tuple(fg), 1.0  # a caixa inteira tem a cor do texto: ele não se separa do fundo


def safe_areas(w, h):
    reels = w / h < 0.8
    text = (w * 0.1, h * 360 / 1920, w * 0.9, h * 1420 / 1920) if reels else (w * 0.1, h * 0.1, w * 0.9, h * 0.9)
    return text, (w * 0.05, h * 0.05, w * 0.95, h * 0.95)


def thumb(path: pathlib.Path) -> np.ndarray:
    im = Image.open(path).convert("L").resize((24, 24), Image.BILINEAR)
    a = np.asarray(im, float)
    return (a - a.mean()) / (a.std() + 1e-6)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stills", nargs="?", default="out/stills")
    ap.add_argument("--timeline", default=None, help="timeline.json: compara a composição das cenas entre si")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    d = pathlib.Path(a.stills)
    idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
    lp = d / "layout.json"
    if not lp.exists():
        sys.exit("layout.json não existe: gere os stills com o stills.cjs desta versão")
    lay = json.loads(lp.read_text(encoding="utf-8"))
    W, H, scale = lay["width"], lay["height"], idx.get("scale", 0.5)
    u = min(W, H) / 1080
    text_safe, action_safe = safe_areas(W, H)
    res, seen, measured = [], set(), 0

    def add(level, t, what, msg):
        key = (level, what, msg.split(" em ")[0])
        if key in seen:  # o mesmo texto com o mesmo defeito em vários stills conta uma vez
            return
        seen.add(key)
        res.append({"level": level, "t": t, "what": what, "msg": msg})

    # O mesmo texto pode aparecer pequeno num still porque está crescendo: vale o maior tamanho que ele atinge.
    biggest: dict[str, float] = {}
    for fr in lay["frames"]:
        for it in fr["items"] or []:
            biggest[it["text"]] = max(biggest.get(it["text"], 0), it["font"])

    for fr in lay["frames"]:
        if fr["items"] is None:
            continue
        measured += 1
        img = np.asarray(Image.open(d / fr["file"]).convert("RGB"))
        settled = [it for it in fr["items"] if it["vis"] >= SETTLED["vis"] and it["op"] >= SETTLED["op"] and it["blur"] < SETTLED["blur"]]
        # Texto inteiro fora do quadro não está na tela: não é defeito de layout.
        settled = [it for it in settled if it["x"] + it["w"] > 0 and it["y"] + it["h"] > 0 and it["x"] < W and it["y"] < H]
        for it in settled:
            x0, y0, x1, y1 = it["x"], it["y"], it["x"] + it["w"], it["y"] + it["h"]
            name = f"\"{it['text']}\""
            if x0 < -2 or y0 < -2 or x1 > W + 2 or y1 > H + 2:
                add("FAIL", fr["t"], name, f"texto cortado pela borda do quadro ({x0},{y0} a {x1},{y1} em {W}x{H})")
            elif x0 < action_safe[0] or y0 < action_safe[1] or x1 > action_safe[2] or y1 > action_safe[3]:
                add("FAIL", fr["t"], name, "texto fora da área de ação (90% do quadro): fica colado na borda")
            elif x0 < text_safe[0] - 1 or y0 < text_safe[1] - 1 or x1 > text_safe[2] + 1 or y1 > text_safe[3] + 1:
                add("WARN", fr["t"], name, f"texto fora da área segura de texto (y {y0} a {y1}, seguro {round(text_safe[1])} a {round(text_safe[3])})")
            font = biggest[it["text"]]
            if font > it["font"] * 1.15:
                continue  # no meio de uma entrada por escala: o still em que ele assenta é que conta
            if it["font"] < MIN_FONT_FAIL * u:
                add("FAIL", fr["t"], name, f"letra de {it['font']:.0f} px: mínimo legível é {MIN_FONT_FAIL * u:.0f} px neste formato")
            elif it["font"] < MIN_FONT_WARN * u:
                add("WARN", fr["t"], name, f"letra de {it['font']:.0f} px: pequena para celular (recomendado {MIN_FONT_WARN * u:.0f} px ou mais)")
            fg, alpha = parse_color(it["color"])
            crop = img[max(0, int(y0 * scale)):max(1, int(y1 * scale)), max(0, int(x0 * scale)):max(1, int(x1 * scale))]
            if fg and alpha * it["op"] > 0.6 and crop.size >= 48:
                bg, cover = background(crop, fg)
                ratio = contrast(fg, bg)
                tag = f"contraste {ratio:.1f}:1 (texto {'#%02x%02x%02x' % tuple(int(v) for v in fg)} sobre {'#%02x%02x%02x' % tuple(int(v) for v in bg)})"
                if ratio < 3 and cover >= 0.35:
                    add("FAIL", fr["t"], name, f"{tag}: mínimo 3:1")
                elif ratio < 3 or (ratio < 4.5 and it["font"] < 40 * u):
                    add("WARN", fr["t"], name, f"{tag}: recomendado 4,5:1" + ("" if cover >= 0.35 else " (fundo irregular, confira no frame)"))
        for i, p in enumerate(settled):
            for q in settled[i + 1:]:
                # A caixa do DOM tem a altura da fonte inteira (ascendente e descendente): com entrelinha
                # apertada, linhas vizinhas se tocam na caixa sem se tocar no glifo. Compara o miolo.
                ix = min(p["x"] + p["w"], q["x"] + q["w"]) - max(p["x"], q["x"])
                iy = min(p["y"] + p["h"] * 0.84, q["y"] + q["h"] * 0.84) - max(p["y"] + p["h"] * 0.16, q["y"] + q["h"] * 0.16)
                if ix > 0 and iy > 0 and ix * iy > OVERLAP * min(p["w"] * p["h"], q["w"] * q["h"]) * 0.68:
                    add("FAIL", fr["t"], f"\"{p['text']}\" x \"{q['text']}\"", "dois textos sobrepostos")

    if a.timeline:
        scenes = json.loads(pathlib.Path(a.timeline).read_text(encoding="utf-8"))["scenes"]
        picks = []
        for s in scenes:
            inside = [it for it in idx["stills"] if s["start"] <= it["t"] < s["end"]]
            if inside:
                mid = min(inside, key=lambda it: abs(it["t"] - (s["start"] + s["end"]) / 2))
                picks.append((s["id"], thumb(d / mid["file"])))
        if len(picks) >= 3:
            corr = {(x[0], y[0]): float((x[1] * y[1]).mean()) for i, x in enumerate(picks) for y in picks[i + 1:]}
            for (x, y), c in zip(zip(picks, picks[1:]), [corr[(x[0], y[0])] for x, y in zip(picks, picks[1:])]):
                if c > SAME_PAIR:
                    add("WARN", None, f"{x[0]} e {y[0]}", f"cenas vizinhas com a mesma composição (semelhança {c:.2f}): mude a espinha, o enquadramento ou a escala")
            med = float(np.median(list(corr.values())))
            if med > SAME_ALL:
                add("WARN", None, "peça", f"as cenas têm a mesma espinha de composição (semelhança mediana {med:.2f}): é o sinal de vídeo de template")
            res.append({"level": "INFO", "t": None, "what": "distinção entre cenas", "msg": f"semelhança mediana {med:.2f}, maior {max(corr.values()):.2f} (avisa acima de {SAME_ALL} e {SAME_PAIR})"})

    if not measured:
        res.append({"level": "WARN", "t": None, "what": "sonda", "msg": "nenhum still foi medido: ponha <Probe /> na composição (veja o Showcase do template)"})
    fails = sum(r["level"] == "FAIL" for r in res)
    warns = sum(r["level"] == "WARN" for r in res)
    if a.json:
        print(json.dumps({"pass": not fails, "fails": fails, "warns": warns, "frames": measured, "issues": res}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            when = f"{r['t']:.2f}s " if r["t"] is not None else ""
            print(f"{r['level']:4s}  {when}{r['what']}: {r['msg']}")
        print(json.dumps({"pass": not fails, "fails": fails, "warns": warns, "frames": measured}))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
