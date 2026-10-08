#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Gate de QA do MP4 final. Sai com código 1 se qualquer verificação bloqueante falhar.

  uv run scripts/qa.py out/video.mp4 --profile youtube
  uv run scripts/qa.py out/loop.mp4 --loop
  uv run scripts/qa.py out/video.mp4 --words public/audio/narration.words.json --lufs -14
Verifica: codec/pixel format/fps/áudio, duração de áudio x vídeo, loudness integrado e true peak,
flashes fotossensíveis (mais de 3 por segundo), trechos parados, frames pretos, emenda de loop
e velocidade de leitura das legendas (caracteres por segundo).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

import numpy as np

PROFILES = {
    "youtube": {"w": 1920, "h": 1080, "lufs": -14, "tp": -1.0},
    "reels": {"w": 1080, "h": 1920, "lufs": -14, "tp": -1.0},
    "tiktok": {"w": 1080, "h": 1920, "lufs": -14, "tp": -1.0},
    "square": {"w": 1080, "h": 1080, "lufs": -14, "tp": -1.0},
    "linkedin": {"w": 1920, "h": 1080, "lufs": -14, "tp": -1.0},
    "podcast": {"w": None, "h": None, "lufs": -16, "tp": -1.0},
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    j = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    return j, v, a


def gray_frames(path, w=64, h=36):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32) / 255


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--profile", default="youtube", choices=list(PROFILES))
    ap.add_argument("--lufs", type=float, default=None)
    ap.add_argument("--loop", action="store_true", help="checa a emenda do último frame para o primeiro")
    ap.add_argument("--words", default=None, help="words.json da narração para medir leitura")
    ap.add_argument("--max-cps", type=float, default=17.0)
    ap.add_argument("--static-sec", type=float, default=1.5, help="tempo máximo sem movimento")
    a = ap.parse_args()
    prof = PROFILES[a.profile]
    lufs_target = a.lufs if a.lufs is not None else prof["lufs"]
    res = []

    def check(name, ok, detail, blocking=True):
        res.append({"check": name, "status": "PASS" if ok else ("FAIL" if blocking else "WARN"), "detail": detail})

    j, v, au = probe(a.video)
    fps = eval(v["avg_frame_rate"]) if v else 0  # noqa: S307 (fração do ffprobe, ex.: 30/1)
    vdur = float(j["format"]["duration"])
    check("video h264 yuv420p", v and v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p", f"{v and v['codec_name']} {v and v.get('pix_fmt')}")
    if prof["w"]:
        check("resolução do perfil", v and (v["width"], v["height"]) == (prof["w"], prof["h"]), f"{v['width']}x{v['height']} (perfil {a.profile})", blocking=False)
    check("fps padrão", round(fps, 3) in (24, 25, 30, 50, 60, 23.976, 29.97, 59.94), f"{fps:.3f}", blocking=False)
    check("tem áudio", au is not None, au["codec_name"] if au else "sem stream de áudio")

    if au:
        adur = float(au.get("duration", vdur))
        check("áudio cobre o vídeo", abs(adur - vdur) <= 0.15, f"áudio {adur:.2f}s x vídeo {vdur:.2f}s")
        e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        summ = e[e.rfind("Summary:"):]
        I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
        tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
        check("loudness integrado", abs(I - lufs_target) <= 1.0, f"{I:.1f} LUFS (alvo {lufs_target})")
        check("true peak", tp <= prof["tp"] + 0.05, f"{tp:.1f} dBTP (máx {prof['tp']})")

    g = gray_frames(a.video)
    mean = g.mean((1, 2))
    # Flash: par de variações opostas de luminância média >= 10% (aprox. WCAG 2.3.1 geral).
    d = np.diff(mean)
    ev = np.where(np.abs(d) >= 0.10)[0]
    flashes, last_sign = [], 0
    for i in ev:
        s = np.sign(d[i])
        if last_sign and s != last_sign:
            flashes.append(i)
        last_sign = s
    win = int(round(fps)) or 30
    worst = max((sum(1 for f in flashes if k <= f < k + win) for k in range(0, len(mean), max(1, win // 2))), default=0)
    check("flashes por segundo <= 3", worst <= 3, f"pior janela: {worst}")

    motion = np.abs(np.diff(g, axis=0)).mean((1, 2))
    still = motion < 0.0015
    longest, run_len = 0, 0
    for s in still:
        run_len = run_len + 1 if s else 0
        longest = max(longest, run_len)
    check("sem trecho parado longo", longest / fps <= a.static_sec, f"maior trecho parado: {longest / fps:.2f}s", blocking=False)

    dark = mean < 0.02
    check("sem frames pretos no meio", not dark[int(fps * 0.5):-int(fps * 0.5) or None].any(), f"{int(dark.sum())} frames quase pretos", blocking=False)

    if a.loop:
        seam = np.abs(g[0] - g[-1]).mean()
        typical = np.median(motion) if len(motion) else 0
        check("emenda do loop", seam <= max(2.5 * typical, 0.004), f"diferença na emenda {seam:.4f} x passo típico {typical:.4f}")

    if a.words:
        words = json.load(open(a.words, encoding="utf-8"))["words"]
        sys.path.insert(0, "")
        groups, cur = [], []
        for i, w in enumerate(words):
            cur.append(w)
            nxt = words[i + 1] if i + 1 < len(words) else None
            if not nxt or re.search(r"[.,;:!?…]$", w["word"]) or len(cur) >= 6:
                groups.append(cur)
                cur = []
        worst_cps = max((sum(len(x["word"]) for x in g_) / max(g_[-1]["end"] - g_[0]["start"], 0.3) for g_ in groups), default=0)
        check("leitura das legendas", worst_cps <= a.max_cps, f"pior frase: {worst_cps:.1f} cps (máx {a.max_cps})", blocking=False)

    for r in res:
        print(f"{r['status']:4s}  {r['check']}: {r['detail']}")
    failed = [r for r in res if r["status"] == "FAIL"]
    print(json.dumps({"pass": not failed, "fails": len(failed), "warns": sum(r['status'] == 'WARN' for r in res)}))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
