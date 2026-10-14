#!/usr/bin/env python3
"""Lint antes do render: contrato de direção (direction.json), partitura (timeline.json + palavras) e código das cenas.

  python3 scripts/lint.py                       # na pasta do projeto: public/timeline.json, direction.json e src/
  python3 scripts/lint.py public/timeline.json --src src --words public/audio/narration.words.json
  python3 scripts/lint.py --json

Pega em segundos o que um render de minutos só mostraria depois: peça sem direção declarada, cenas com a
mesma composição e a mesma entrada, corte no meio de frase, cena com texto demais para o tempo, SFX
empilhado, API que faz o render divergir do preview, curva linear ou fora dos tokens, cor fora do tema.
Sai com código 1 se houver FAIL. Só biblioteca padrão.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

WORDS_PER_SEC = 2.6  # teto por cena; a meta de roteiro é 2,3
CUT_TOLERANCE = 0.25  # corte até 0,25 s do início de uma frase conta como casado
SFX_MIN_GAP = 0.12
END_HOLD = 1.0

# (regex, nível, mensagem). Valem para src/**/*.ts(x).
CODE_RULES = [
    (r"\bMath\.random\s*\(", "FAIL", "Math.random(): use random(seed) do remotion"),
    (r"\bDate\.now\s*\(|\bnew Date\s*\(\s*\)|\bperformance\.now\s*\(", "FAIL", "relógio de parede: derive tudo de useCurrentFrame()"),
    (r"\bset(Timeout|Interval)\s*\(|\brequestAnimationFrame\s*\(", "FAIL", "timer do navegador: o render não espera por ele"),
    (r"\buseFrame\s*\(", "FAIL", "useFrame() do React Three Fiber: anime com useCurrentFrame()"),
    (r"\btransition\s*:\s*['\"`]|\banimation\s*:\s*['\"`]|@keyframes|\banimate-[a-z]", "FAIL", "animação ou transição CSS: pisca no render"),
    (r"\bEasing\.(bounce|elastic)\b", "FAIL", "bounce e elastic são proibidos pela doutrina"),
    (r"<(video|audio|img)\b", "WARN", "tag HTML de mídia: use OffthreadVideo, Audio ou Img do remotion (esperam carregar)"),
    (r"[\U0001F300-\U0001FAFF☀-➿]", "WARN", "emoji no código da cena"),
]
BEZIER = re.compile(r"\bEasing\.(bezier|in|out|inOut|poly|exp|circle|back|cubic|quad)\b")


def lint_score(tl: dict, words: list[dict] | None, absolute: bool = False) -> list[dict]:
    out = []

    def add(level, where, msg):
        out.append({"level": level, "where": where, "msg": msg})

    dur, scenes = float(tl.get("duration", 0)), tl.get("scenes", [])
    if not scenes:
        add("FAIL", "partitura", "sem cenas")
        return out
    if abs(scenes[0]["start"]) > 0.02:
        add("FAIL", scenes[0]["id"], f"a primeira cena começa em {scenes[0]['start']} s, não em 0")
    if abs(scenes[-1]["end"] - dur) > 0.05:
        add("FAIL", scenes[-1]["id"], f"a última cena termina em {scenes[-1]['end']} s e a duração é {dur} s")
    for a, b in zip(scenes, scenes[1:]):
        if abs(a["end"] - b["start"]) > 0.02:
            add("FAIL", f"{a['id']} > {b['id']}", f"buraco ou sobreposição: {a['end']} s x {b['start']} s")
    lens = [s["end"] - s["start"] for s in scenes]
    for s, n in zip(scenes, lens):
        if n < 1.0:
            add("WARN", s["id"], f"cena de {n:.2f} s: curta demais para ler qualquer coisa")
    if len(lens) > 2 and max(lens) / max(min(lens), 0.01) < 1.25:
        add("WARN", "ritmo", f"todas as cenas têm quase a mesma duração ({min(lens):.1f} a {max(lens):.1f} s): sem contraste de ritmo")

    sfx = sorted(tl.get("sfx", []), key=lambda e: e["at"])
    for e in sfx:
        if not 0 <= e["at"] <= dur:
            add("FAIL", f"sfx {e['type']}", f"evento em {e['at']} s, fora da duração")
    for a, b in zip(sfx, sfx[1:]):
        if b["at"] - a["at"] < SFX_MIN_GAP:
            add("WARN", f"sfx {a['type']} + {b['type']}", f"dois eventos a {b['at'] - a['at']:.2f} s um do outro em {a['at']:.2f} s: um mascara o outro")

    if not words:
        if tl.get("narration"):
            add("WARN", "narração", "partitura tem narração mas o words.json não foi encontrado: checagens de fala puladas")
        return out
    off = 0.0 if absolute else float((tl.get("narration") or {}).get("start", 0))
    t = [(w["word"], w["start"] + off, w["end"] + off) for w in words]
    if t[0][1] < 0.1:
        add("WARN", "narração", f"a voz começa em {t[0][1]:.2f} s: dê 0,1 a 0,3 s depois do corte")
    if t[-1][2] > dur + 0.02:
        add("FAIL", "narração", f"a voz termina em {t[-1][2]:.2f} s e o vídeo em {dur:.2f} s")
    elif dur - t[-1][2] < END_HOLD:
        add("WARN", "final", f"só {dur - t[-1][2]:.2f} s depois da última palavra: segure o quadro final por 1 s ou mais")
    starts = [t[0][1]] + [t[i + 1][1] for i in range(len(t) - 1) if re.search(r"[.!?…:]$", t[i][0])]
    for s in scenes[1:]:
        cut = s["start"]
        near = min(starts, key=lambda x: abs(x - cut))
        # Em palavra com pontuação o fim informado pelo TTS inclui a pausa: só os primeiros 60% contam como fala.
        mid = next((w for w in t if w[1] + 0.03 < cut < w[1] + (w[2] - w[1]) * (0.6 if re.search(r"[.,;:!?…]$", w[0]) else 1) - 0.03), None)
        if mid:
            add("FAIL", s["id"], f"o corte em {cut:.2f} s cai dentro da palavra '{mid[0]}'")
        elif abs(near - cut) > CUT_TOLERANCE and cut < t[-1][2]:
            add("WARN", s["id"], f"o corte em {cut:.2f} s não casa com início de frase (o mais próximo é {near:.2f} s)")
    for s, n in zip(scenes, lens):
        spoken = [w for w in t if s["start"] <= w[1] < s["end"]]
        if spoken and len(spoken) / n > WORDS_PER_SEC:
            add("WARN", s["id"], f"{len(spoken)} palavras em {n:.1f} s ({len(spoken) / n:.1f} por segundo): corte texto, meta 2,3")
    return out


def linear_interpolates(text: str) -> list[int]:
    """Linhas com interpolate(frame, ...) sem easing: o padrão do Remotion é linear, a marca do amador."""
    hits = []
    for m in re.finditer(r"\binterpolate\s*\(", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        call = text[m.end():i - 1]
        first = call.split(",", 1)[0].strip()
        if re.search(r"frame|^t$|time", first, re.I) and "easing" not in call:
            hits.append(text.count("\n", 0, m.start()) + 1)
    return hits


def lint_code(src: pathlib.Path) -> list[dict]:
    out, fades, moves, loose = [], 0, 0, []
    for f in sorted(src.rglob("*.ts*")):
        if "node_modules" in f.parts:
            continue
        in_tokens = f.name == "motion.ts"
        text = f.read_text(encoding="utf-8")
        if not in_tokens:
            for n in linear_interpolates(text):
                out.append({"level": "WARN", "where": f"{f.relative_to(src.parent)}:{n}", "msg": "interpolate() sem easing é movimento linear: use tween() ou keys() com um token de ease.*"})
        if f.name not in ("theme.ts", "theme.tsx"):
            loose += [(f"{f.relative_to(src.parent)}:{text.count(chr(10), 0, m.start()) + 1}", m.group(0)) for m in re.finditer(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![0-9a-fA-F])", "\n".join(l.split("//")[0] for l in text.splitlines()))]
        for n, line in enumerate(text.splitlines(), 1):
            code = line.split("//")[0] if "://" not in line else line
            for rx, level, msg in CODE_RULES:
                if re.search(rx, code):
                    out.append({"level": level, "where": f"{f.relative_to(src.parent)}:{n}", "msg": msg})
            if not in_tokens and BEZIER.search(code):
                out.append({"level": "WARN", "where": f"{f.relative_to(src.parent)}:{n}", "msg": "curva criada na cena: use os tokens ease.* de lib/motion.ts"})
            fades += len(re.findall(r"\bopacity\s*[:=]", code))
            moves += len(re.findall(r"\b(translate[XYZ3d]*|scale[XY]?|rotate[XYZ]?|clipPath|strokeDashoffset)\b", code))
    if loose:
        sample = ", ".join(f"{c} em {w}" for w, c in loose[:4])
        out.append({"level": "WARN", "where": "src", "msg": f"{len(loose)} cores escritas fora de theme.ts ({sample}): a paleta da peça mora em public/brand.json"})
    if fades >= 6 and fades > 2 * max(moves, 1):
        out.append({"level": "WARN", "where": "src", "msg": f"{fades} usos de opacity contra {moves} de transform, máscara ou traço: tudo entrando com fade tem cara de gerado"})
    return out


DIRECTION_FIELDS = ("concept", "law", "motif", "options", "chosen", "approved_by", "scenes")


def lint_direction(root: pathlib.Path, tl: dict) -> list[dict]:
    """Contrato de direção: o que a peça declara antes de qualquer cena existir (references/direction.md)."""
    out = []

    def add(level, where, msg):
        out.append({"level": level, "where": where, "msg": msg})

    p = root / "direction.json"
    if not p.is_file():
        add("FAIL", "direction.json", "a peça não tem contrato de direção: escreva direction.json antes de animar (references/direction.md)")
        return out
    d = json.loads(p.read_text(encoding="utf-8"))
    for k in DIRECTION_FIELDS:
        if not d.get(k):
            add("FAIL", "direction.json", f"falta '{k}'")
    if out:
        return out
    if len(d["options"]) < 2:
        add("FAIL", "direction.json", "só uma direção considerada: monte de 2 a 3 styleframes de direções diferentes antes de escolher")
    if d["chosen"] not in [o.get("name") for o in d["options"]]:
        add("FAIL", "direction.json", f"'chosen' ({d['chosen']}) não é uma das opções")
    if d["approved_by"] == "agent":
        add("WARN", "direction.json", "a direção foi escolhida pelo agente, sem aprovação do usuário: diga isso na entrega")
    elif d["approved_by"] != "user":
        add("FAIL", "direction.json", "'approved_by' é 'user' (o usuário escolheu) ou 'agent' (o pedido delegou a escolha)")
    declared = {s.get("id"): s for s in d["scenes"]}
    ids = [s["id"] for s in tl.get("scenes", [])]
    for i in ids:
        s = declared.get(i)
        if not s:
            add("FAIL", i, "cena sem declaração em direction.json (layout, entrance, hero)")
        elif not all(s.get(k) for k in ("layout", "entrance", "hero")):
            add("FAIL", i, "a declaração da cena precisa de layout, entrance e hero")
    seq = [declared[i] for i in ids if i in declared and declared[i].get("layout") and declared[i].get("entrance")]
    if len(seq) >= 3:
        layouts = [s["layout"] for s in seq]
        top = max(set(layouts), key=layouts.count)
        if len(set(layouts)) == 1:
            add("FAIL", "direção", f"todas as cenas declaram o mesmo layout ('{top}'): isso é slide de marca, não filme")
        elif layouts.count(top) > len(layouts) / 2:
            add("WARN", "direção", f"{layouts.count(top)} de {len(layouts)} cenas usam o layout '{top}'")
        entrances = [s["entrance"] for s in seq]
        if len(set(entrances)) == 1:
            add("FAIL", "direção", f"todas as cenas entram do mesmo jeito ('{entrances[0]}')")
    for a, b in zip(seq, seq[1:]):
        if (a["layout"], a["entrance"]) == (b["layout"], b["entrance"]):
            add("WARN", f"{a['id']} > {b['id']}", f"cenas vizinhas com o mesmo layout e a mesma entrada ({a['layout']}, {a['entrance']})")
    return out


def lint_env(root: pathlib.Path) -> list[dict]:
    if not (root / ".env").is_file():
        return []
    gi = root / ".gitignore"
    rules = [l.strip() for l in gi.read_text(encoding="utf-8").splitlines()] if gi.is_file() else []
    if any(r in (".env", "/.env", ".env*", "*.env") for r in rules):
        return []
    return [{"level": "FAIL", "where": ".env", "msg": "há um .env e o .gitignore não o ignora: renomeie o gitignore do template para .gitignore"}]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline", nargs="?", default="public/timeline.json")
    ap.add_argument("--words", default=None, help="padrão: <narration.file sem extensão>.words.json ao lado da partitura")
    ap.add_argument("--src", default=None, help="padrão: src/ ao lado de public/")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    tlp = pathlib.Path(a.timeline)
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    wp = pathlib.Path(a.words) if a.words else None
    if wp is None and (tl.get("narration") or {}).get("file"):
        wp = tlp.parent / (str(pathlib.Path(tl["narration"]["file"]).with_suffix("")) + ".words.json")
    words = json.loads(wp.read_text(encoding="utf-8"))["words"] if wp and wp.exists() else None
    cues = tlp.parent / "cues.json"
    absolute = False
    if not a.words and cues.exists():  # score.py: palavras já no tempo do vídeo, com qualquer origem de voz
        cw = json.loads(cues.read_text(encoding="utf-8")).get("words") or []
        words, absolute = (cw or words), bool(cw)
    src = pathlib.Path(a.src) if a.src else tlp.parent.parent / "src"
    root = tlp.resolve().parent.parent

    res = lint_direction(root, tl) + lint_score(tl, words, absolute) + (lint_code(src) if src.is_dir() else []) + lint_env(root)
    fails = sum(r["level"] == "FAIL" for r in res)
    if a.json:
        print(json.dumps({"pass": not fails, "fails": fails, "warns": len(res) - fails, "issues": res}, ensure_ascii=False, indent=1))
    else:
        for r in res:
            print(f"{r['level']:4s}  {r['where']}: {r['msg']}")
        print(json.dumps({"pass": not fails, "fails": fails, "warns": len(res) - fails}))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
