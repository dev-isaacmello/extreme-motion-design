#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "pillow"]
# ///
"""Medidor de design: diz, em número, se a peça tem direção própria ou caiu no quadro padrão do modelo.

  uv run scripts/design.py out/stills --timeline public/timeline.json     # stills do stills.cjs (pixels + texto do DOM)
  uv run scripts/design.py --video out/final.mp4                          # qualquer vídeo, só pixels
  uv run scripts/design.py out/stills --json
O layout.py acha defeito (texto cortado, sem contraste). Este script mede escolha: quantas cores com área de verdade,
quanto do quadro está vazio, onde está a massa visual e se ela muda de cena para cena, o salto de escala entre o maior
texto e o segundo, e quanto do texto é mono ou caixa alta. No fim ele conta os sinais do "quadro padrão" (quase preto
com um acento, condensada gigante sempre na mesma margem, mono no canto, tudo em caixa alta, duas cores, mesma
composição em toda cena). Três sinais ou mais: a peça é a que o modelo faria sem direção nenhuma.
Tudo sai como aviso: os limiares vêm de references/design.md e foram calibrados em poucos vídeos. --strict faz o
veredito "padrão" sair com código 1.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

CONDENSED = ("anton", "bebas", "oswald", "barlow condensed", "league gothic", "big shoulders", "fjalla", "archivo narrow", "impact", "sofia sans condensed")


def oklch(rgb: np.ndarray) -> np.ndarray:
    """sRGB 0..1 -> (L, C, h em graus) do OKLab."""
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    l = 0.4122214708 * c[..., 0] + 0.5363325363 * c[..., 1] + 0.0514459929 * c[..., 2]
    m = 0.2119034982 * c[..., 0] + 0.6806995451 * c[..., 1] + 0.1073969566 * c[..., 2]
    s = 0.0883024619 * c[..., 0] + 0.2817188376 * c[..., 1] + 0.6299787005 * c[..., 2]
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return np.stack([L, np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360, a, b], -1)


def frame_metrics(img: Image.Image) -> dict:
    small = np.asarray(img.convert("RGB").resize((96, round(96 * img.height / img.width)), Image.BOX), np.float32) / 255
    o = oklch(small)
    lab = np.stack([o[..., 0], o[..., 3], o[..., 4]], -1).reshape(-1, 3)
    # Agrupa por distância em OKLab: cada cor com 2% ou mais da área conta.
    clusters = []
    q = np.round(lab / np.array([0.07, 0.05, 0.05])).astype(int)
    keys, inv, counts = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    means = np.stack([lab[inv == i].mean(0) for i in range(len(keys))])
    for i in np.argsort(-counts):
        hit = next((c for c in clusters if np.linalg.norm(c["lab"] - means[i]) < 0.075), None)
        if hit:
            hit["n"] += counts[i]
        else:
            clusters.append({"lab": means[i], "n": int(counts[i])})
    total = len(lab)
    big = [c for c in clusters if c["n"] / total >= 0.02]
    bg = max(clusters, key=lambda c: c["n"])["lab"]
    dist = np.linalg.norm(lab - bg, axis=1).reshape(o.shape[:2])
    h, w = dist.shape
    wgt = np.abs(o[..., 0] - bg[0]) + 0.5 * np.hypot(o[..., 3] - bg[1], o[..., 4] - bg[2])
    tot = float(wgt.sum()) or 1.0
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = float((wgt * xs).sum() / tot / (w - 1)), float((wgt * ys).sum() / tot / (h - 1))
    chroma = [float(np.hypot(c["lab"][1], c["lab"][2])) for c in big]
    return {
        "n_colors": len(big), "empty_frac": round(float((dist < 0.035).mean()), 3), "chroma_frac": round(float((o[..., 1] > 0.10).mean()), 3),
        "bg_L": round(float(bg[0]), 3), "bg_C": round(float(np.hypot(bg[1], bg[2])), 3),
        "saturated": sum(1 for c in chroma if c > 0.13), "cx": round(cx, 3), "cy": round(cy, 3),
        "mass_offset": round(float(np.hypot(cx - 0.5, cy - 0.5) / 0.7071), 3),
    }


def text_metrics(items: list[dict], W: int, H: int) -> dict | None:
    it = [x for x in items if x["vis"] >= 0.88 and x["op"] >= 0.9 and 0 <= x["x"] < W and 0 <= x["y"] < H]
    if not it:
        return None
    sizes = sorted({round(x["font"]) for x in it}, reverse=True)
    distinct = [sizes[0]]
    for s in sizes[1:]:
        if s < distinct[-1] * 0.96:
            distinct.append(s)
    hero = max(it, key=lambda x: x["font"])
    edges = sorted({round(x["x"] / 6) * 6 for x in it if x["font"] >= distinct[min(1, len(distinct) - 1)] * 0.9})
    fam = hero.get("family", "").lower()
    return {
        "ratio_top2": round(distinct[0] / distinct[1], 2) if len(distinct) > 1 else None, "n_sizes": len(distinct),
        "mono_frac": round(sum("mono" in x.get("family", "").lower() for x in it) / len(it), 2),
        "caps_frac": round(sum(bool(x.get("upper")) for x in it) / len(it), 2),
        "hero_px": hero["font"], "hero_share": round(hero["font"] / min(W, H), 3), "hero_x": round(hero["x"] / W, 3),
        "hero_condensed": any(k in fam for k in CONDENSED), "hero_weight": hero.get("weight"), "left_edges": len(edges),
        "has_family": "family" in hero,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stills", nargs="?", default=None)
    ap.add_argument("--video", default=None, help="mede só pixels de um vídeo qualquer")
    ap.add_argument("--every", type=float, default=1.5, help="com --video: um frame a cada tantos segundos")
    ap.add_argument("--timeline", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = []
    if a.video:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"fps=1/{a.every},scale=480:-2", f"{td}/%04d.png"], check=True)
            for i, f in enumerate(sorted(pathlib.Path(td).glob("*.png"))):
                rows.append({"t": round((i + 0.5) * a.every, 2), **frame_metrics(Image.open(f)), "text": None})
    elif a.stills:
        d = pathlib.Path(a.stills)
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        lay = json.loads((d / "layout.json").read_text(encoding="utf-8")) if (d / "layout.json").exists() else None
        frames = {f["frame"]: f for f in lay["frames"]} if lay else {}
        picks = idx["stills"]
        if a.timeline:  # um still por cena, o do meio: entrada e saída não representam a composição
            scenes = json.loads(pathlib.Path(a.timeline).read_text(encoding="utf-8"))["scenes"]
            picks = [min((s for s in idx["stills"] if sc["start"] <= s["t"] < sc["end"]), key=lambda s: abs(s["t"] - (sc["start"] + sc["end"]) / 2), default=None) for sc in scenes]
            picks = [p for p in picks if p]
        for s in picks:
            items = (frames.get(s["frame"]) or {}).get("items")
            rows.append({"t": s["t"], **frame_metrics(Image.open(d / s["file"])), "text": text_metrics(items, lay["width"], lay["height"]) if items else None})
    else:
        ap.error("informe a pasta de stills ou --video")
    if not rows:
        sys.exit("nenhum frame para medir")

    n = len(rows)
    frac = lambda f: sum(1 for r in rows if f(r)) / n  # noqa: E731
    txt = [r["text"] for r in rows if r["text"]]
    tfrac = lambda f: (sum(1 for t in txt if f(t)) / len(txt)) if txt else 0.0  # noqa: E731
    spread = float(np.hypot(np.std([r["cx"] for r in rows]), np.std([r["cy"] for r in rows])))
    signals = []

    def sig(cond, name, detail):
        if cond:
            signals.append({"signal": name, "detail": detail})

    dark = frac(lambda r: r["bg_L"] < 0.25 and r["saturated"] <= 1 and r["n_colors"] <= 3)
    sig(dark >= 0.6, "quase preto com um acento", f"{dark:.0%} dos quadros têm fundo escuro e no máximo uma cor saturada")
    two = frac(lambda r: r["n_colors"] <= 2)
    sig(two >= 0.6, "duas cores", f"{two:.0%} dos quadros têm só duas cores com área de 2% ou mais")
    sig(n >= 3 and spread < 0.05, "mesma composição", f"a massa visual quase não muda de lugar entre os quadros (dispersão {spread:.3f}, mínimo 0,05)")
    if txt:
        cond = tfrac(lambda t: t["hero_condensed"] and t["hero_share"] >= 0.12)
        sig(cond >= 0.6, "condensada gigante", f"{cond:.0%} dos quadros têm uma condensada como maior texto")
        caps = float(np.mean([t["caps_frac"] for t in txt]))
        sig(caps > 0.5, "tudo em caixa alta", f"{caps:.0%} dos blocos de texto estão em caixa alta (referência: até 20%)")
        mono = tfrac(lambda t: t["mono_frac"] > 0)
        sig(mono >= 0.6 and float(np.mean([t["mono_frac"] for t in txt])) > 0.15, "mono de enfeite", f"há texto mono em {mono:.0%} dos quadros")
        left = tfrac(lambda t: t["hero_x"] < 0.14)
        sig(left >= 0.7, "tudo na margem esquerda", f"em {left:.0%} dos quadros o maior texto começa na margem esquerda")
        heavy = tfrac(lambda t: (t["hero_weight"] or 0) >= 700 or t["hero_condensed"])
        sig(heavy >= 0.9 and len(txt) >= 3, "peso único", f"em {heavy:.0%} dos quadros o maior texto é pesado: não há hero leve em nenhuma cena")

    summary = {
        "frames": n, "n_colors_median": float(np.median([r["n_colors"] for r in rows])), "empty_frac_median": round(float(np.median([r["empty_frac"] for r in rows])), 2),
        "mass_spread": round(spread, 3), "bg_light_frac": round(frac(lambda r: r["bg_L"] > 0.6), 2),
        "ratio_top2_median": round(float(np.median([t["ratio_top2"] for t in txt if t["ratio_top2"]])), 2) if any(t["ratio_top2"] for t in txt) else None,
        "n_sizes_max": max((t["n_sizes"] for t in txt), default=None),
    }
    warns = []
    if summary["ratio_top2_median"] and 1.2 <= summary["ratio_top2_median"] < 2:
        warns.append(f"salto de escala mediano de {summary['ratio_top2_median']}: entre 1,2 e 2 o maior texto não é igual nem contrasta com o segundo (alvo 3 ou mais)")
    if summary["n_sizes_max"] and summary["n_sizes_max"] > 4:
        warns.append(f"até {summary['n_sizes_max']} tamanhos de letra no mesmo quadro (alvo: 4 ou menos)")
    if summary["empty_frac_median"] < 0.25:
        warns.append(f"mediana de {summary['empty_frac_median']:.0%} de área vazia: abaixo de 25% só em colagem declarada")
    verdict = "padrão do modelo" if len(signals) >= 3 else "direção própria" if len(signals) <= 1 else "perto do padrão"
    out = {"verdict": verdict, "signals": signals, "warnings": warns, "summary": summary}
    if a.json:
        print(json.dumps({**out, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            t = r["text"]
            extra = f"  maior texto {t['hero_px']:.0f}px razão {t['ratio_top2']} tamanhos {t['n_sizes']} caixa alta {t['caps_frac']:.0%}" if t else ""
            print(f"  {r['t']:6.2f}s  cores {r['n_colors']}  vazio {r['empty_frac']:.0%}  fundo L {r['bg_L']:.2f}  massa ({r['cx']:.2f}, {r['cy']:.2f}){extra}")
        for s in signals:
            print(f"SINAL {s['signal']}: {s['detail']}")
        for w in warns:
            print(f"WARN  {w}")
        print(json.dumps({"verdict": verdict, "signals": len(signals), **summary}, ensure_ascii=False))
    sys.exit(1 if a.strict and verdict == "padrão do modelo" else 0)


if __name__ == "__main__":
    main()
