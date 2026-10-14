#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "pillow", "numpy"]
# ///
"""Marca real para o vídeo: extrai paleta, fontes, logo e tom de um site, de um repositório ou de imagens.

Roda uma vez por marca. O resultado (brand.json, BRAND.md e assets/) é reusado em todos os vídeos.

  uv run scripts/brand.py --url https://exemplo.com -o brand/
  uv run scripts/brand.py --repo ../meu-app/apps/web -o brand/
  uv run scripts/brand.py --screens telas/ -o brand/
  uv run scripts/brand.py --url https://exemplo.com --repo ../meu-app -o brand/    # as fontes somam evidência

--url     baixa o HTML e as folhas de estilo (linkadas e @import) e tira screenshots 1440x900 e 390x844.
--repo    lê o código sem executar nada: CSS com custom properties, tailwind.config, objetos de tema,
          package.json, next/font, @font-face e logos em public/, static/ e assets/. Pode repetir.
--screens só imagens (png, jpg, webp): a paleta sai dos pixels.

Nada é inventado: campo sem evidência fica null e entra em "missing". Contraste abaixo do WCAG
(ink/bg 4,5 e accent/bg 3) vira aviso com o número medido; a cor da marca não é alterada.
Chrome: node_modules/.remotion/chrome-headless-shell (pasta atual e pais), depois chromium,
chromium-browser e google-chrome no PATH. Sem Chrome, segue sem screenshot e avisa.
"""
from __future__ import annotations

import argparse
import base64
import colorsys
import datetime as dt
import ipaddress
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from html.parser import HTMLParser

UA = "extreme-motion-design-brand/1.0 (extrator de marca para video; execucao manual de um usuario)"
TIMEOUT = (8, 20)
MAX_REQUESTS = 140
MAX_CSS = 4_000_000
MAX_IMG = 6_000_000
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "out", "coverage", ".venv", "venv", "__pycache__", ".turbo", ".cache", "vendor",
             "target", ".svelte-kit", ".nuxt", ".output", "android", "ios", "storybook-static", "playwright-report", "test-results", ".vercel"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def pt(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


# ---------- cor ----------
_NAMED = (
    "aliceblue f0f8ff antiquewhite faebd7 aqua 00ffff aquamarine 7fffd4 azure f0ffff beige f5f5dc bisque ffe4c4 black 000000 "
    "blanchedalmond ffebcd blue 0000ff blueviolet 8a2be2 brown a52a2a burlywood deb887 cadetblue 5f9ea0 chartreuse 7fff00 "
    "chocolate d2691e coral ff7f50 cornflowerblue 6495ed cornsilk fff8dc crimson dc143c cyan 00ffff darkblue 00008b darkcyan 008b8b "
    "darkgoldenrod b8860b darkgray a9a9a9 darkgreen 006400 darkgrey a9a9a9 darkkhaki bdb76b darkmagenta 8b008b darkolivegreen 556b2f "
    "darkorange ff8c00 darkorchid 9932cc darkred 8b0000 darksalmon e9967a darkseagreen 8fbc8f darkslateblue 483d8b darkslategray 2f4f4f "
    "darkslategrey 2f4f4f darkturquoise 00ced1 darkviolet 9400d3 deeppink ff1493 deepskyblue 00bfff dimgray 696969 dimgrey 696969 "
    "dodgerblue 1e90ff firebrick b22222 floralwhite fffaf0 forestgreen 228b22 fuchsia ff00ff gainsboro dcdcdc ghostwhite f8f8ff "
    "gold ffd700 goldenrod daa520 gray 808080 green 008000 greenyellow adff2f grey 808080 honeydew f0fff0 hotpink ff69b4 "
    "indianred cd5c5c indigo 4b0082 ivory fffff0 khaki f0e68c lavender e6e6fa lavenderblush fff0f5 lawngreen 7cfc00 lemonchiffon fffacd "
    "lightblue add8e6 lightcoral f08080 lightcyan e0ffff lightgoldenrodyellow fafad2 lightgray d3d3d3 lightgreen 90ee90 lightgrey d3d3d3 "
    "lightpink ffb6c1 lightsalmon ffa07a lightseagreen 20b2aa lightskyblue 87cefa lightslategray 778899 lightslategrey 778899 "
    "lightsteelblue b0c4de lightyellow ffffe0 lime 00ff00 limegreen 32cd32 linen faf0e6 magenta ff00ff maroon 800000 "
    "mediumaquamarine 66cdaa mediumblue 0000cd mediumorchid ba55d3 mediumpurple 9370db mediumseagreen 3cb371 mediumslateblue 7b68ee "
    "mediumspringgreen 00fa9a mediumturquoise 48d1cc mediumvioletred c71585 midnightblue 191970 mintcream f5fffa mistyrose ffe4e1 "
    "moccasin ffe4b5 navajowhite ffdead navy 000080 oldlace fdf5e6 olive 808000 olivedrab 6b8e23 orange ffa500 orangered ff4500 "
    "orchid da70d6 palegoldenrod eee8aa palegreen 98fb98 paleturquoise afeeee palevioletred db7093 papayawhip ffefd5 peachpuff ffdab9 "
    "peru cd853f pink ffc0cb plum dda0dd powderblue b0e0e6 purple 800080 rebeccapurple 663399 red ff0000 rosybrown bc8f8f "
    "royalblue 4169e1 saddlebrown 8b4513 salmon fa8072 sandybrown f4a460 seagreen 2e8b57 seashell fff5ee sienna a0522d silver c0c0c0 "
    "skyblue 87ceeb slateblue 6a5acd slategray 708090 slategrey 708090 snow fffafa springgreen 00ff7f steelblue 4682b4 tan d2b48c "
    "teal 008080 thistle d8bfd8 tomato ff6347 turquoise 40e0d0 violet ee82ee wheat f5deb3 white ffffff whitesmoke f5f5f5 "
    "yellow ffff00 yellowgreen 9acd32"
).split()
NAMED = {_NAMED[i]: _NAMED[i + 1] for i in range(0, len(_NAMED), 2)}
CLIPPED: set[str] = set()  # hex que saiu de cor fora do sRGB (oklch/P3 cortado canal a canal)

_FUNC = r"(?:rgba?|hsla?|oklch|oklab|color-mix|light-dark|color)\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\)"
COLOR_RE = re.compile(_FUNC + r"|#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![0-9a-zA-Z_-])|(?<![\w#.$@-])[a-zA-Z]{3,20}(?![\w(-])")
TRIPLET_PCT = re.compile(r"^-?[\d.]+(?:deg)?[\s,]+[\d.]+%[\s,]+[\d.]+%(?:\s*/\s*[\d.]+%?)?$")


def _num(tok: str, pct_of: float = 1.0) -> float | None:
    tok = tok.strip()
    if tok == "none":
        return 0.0
    try:
        return float(tok[:-1]) / 100 * pct_of if tok.endswith("%") else float(tok)
    except ValueError:
        return None


def _hue(tok: str) -> float | None:
    tok = tok.strip()
    for suf, k in (("deg", 1.0), ("grad", 0.9), ("rad", 180 / math.pi), ("turn", 360.0)):
        if tok.endswith(suf) and tok != "grad":
            v = _num(tok[: -len(suf)])
            return None if v is None else v * k
    return _num(tok)


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (max(c, 0.0) ** (1 / 2.4)) - 0.055


def _from_linear(rl: float, gl: float, bl: float, a: float):
    raw = [_gam(rl), _gam(gl), _gam(bl)]
    out = tuple(int(round(min(1.0, max(0.0, v)) * 255)) for v in raw)
    if any(v < -0.02 or v > 1.02 for v in raw):
        CLIPPED.add(hexof(out))
    return (*out, a)


def oklab_to_rgb(L: float, a: float, b: float, alpha: float = 1.0):
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return _from_linear(4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
                        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
                        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_, alpha)


def rgb_to_oklab(rgb) -> tuple[float, float, float]:
    r, g, b = (_lin(v / 255) for v in rgb[:3])
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def lch(rgb) -> tuple[float, float, float]:
    L, a, b = rgb_to_oklab(rgb)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def hexof(rgb) -> str:
    return "#%02X%02X%02X" % tuple(rgb[:3])


def _split_top(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return out + [cur.strip()]


def parse_color(s: str, dark: bool = False):
    """Texto CSS -> (r, g, b, alfa) em sRGB de 8 bits, ou None."""
    s = s.strip().lower()
    if not s:
        return None
    if s[0] == "#":
        h = s[1:]
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8) or re.search(r"[^0-9a-f]", h):
            return None
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)
    if s in NAMED:
        return (*bytes.fromhex(NAMED[s]), 1.0)
    m = re.fullmatch(r"([a-z-]+)\((.*)\)", s, re.S)
    if not m:
        return None
    fn, body = m.group(1), m.group(2).strip()
    if fn == "light-dark":
        parts = _split_top(body)
        return parse_color(parts[1 if dark else 0], dark) if len(parts) == 2 else None
    if fn == "color-mix":
        parts = _split_top(body)
        if len(parts) != 3:
            return None
        space = parts[0].replace("in ", "").strip()
        items = []
        for p in parts[1:]:
            pm = re.search(r"(?:^|\s)([\d.]+)%(?:\s|$)", p)
            col = parse_color(re.sub(r"(?:^|\s)[\d.]+%(?:\s|$)", " ", p).strip(), dark)
            if col is None:
                return None
            items.append((col, float(pm.group(1)) / 100 if pm else None))
        (c1, p1), (c2, p2) = items
        if p1 is None and p2 is None:
            p1 = p2 = 0.5
        elif p1 is None:
            p1 = 1 - p2
        elif p2 is None:
            p2 = 1 - p1
        tot = p1 + p2
        if tot <= 0:
            return None
        w1, w2 = p1 / tot, p2 / tot
        a1, a2 = c1[3] * w1, c2[3] * w2  # mistura com alfa pré-multiplicado
        alpha = (a1 + a2) * min(1.0, tot)
        if a1 + a2 <= 0:
            return (0, 0, 0, 0.0)
        if space == "srgb":
            return (*(int(round((c1[i] * a1 + c2[i] * a2) / (a1 + a2))) for i in range(3)), alpha)
        if space in ("oklab", "oklch"):  # oklch é aproximado: interpola em oklab, sem girar o matiz
            l1, l2 = rgb_to_oklab(c1), rgb_to_oklab(c2)
            return oklab_to_rgb(*((l1[i] * a1 + l2[i] * a2) / (a1 + a2) for i in range(3)), alpha)
        return None
    if "calc(" in body or "var(" in body or "from " in body:
        return None
    main, _, al = body.partition("/")
    toks = [t for t in re.split(r"[\s,]+", main.strip()) if t]
    alpha = 1.0
    if al.strip():
        alpha = _num(al)
    elif fn in ("rgb", "rgba", "hsl", "hsla") and len(toks) == 4:
        alpha = _num(toks.pop())
    if alpha is None:
        return None
    alpha = min(1.0, max(0.0, alpha))
    if fn == "color":
        if len(toks) != 4 or toks[0] not in ("srgb", "display-p3", "srgb-linear"):
            return None
        v = [_num(t) for t in toks[1:]]
        if None in v:
            return None
        if toks[0] == "srgb":
            return (*(int(round(min(1, max(0, x)) * 255)) for x in v), alpha)
        r, g, b = v if toks[0] == "srgb-linear" else (_lin(x) for x in v)
        if toks[0] == "display-p3":
            r, g, b = (1.2249401 * r - 0.2249404 * g, -0.0420569 * r + 1.0420571 * g, -0.0196376 * r - 0.0786361 * g + 1.0982735 * b)
        return _from_linear(r, g, b, alpha)
    if len(toks) != 3:
        return None
    if fn in ("rgb", "rgba"):
        v = [_num(t, 255) for t in toks]
        return None if None in v else (*(int(round(min(255, max(0, x)))) for x in v), alpha)
    if fn in ("hsl", "hsla"):
        h, s_, l_ = _hue(toks[0]), _num(toks[1], 1), _num(toks[2], 1)
        if None in (h, s_, l_):
            return None
        if not toks[1].endswith("%"):
            s_, l_ = s_ / 100, l_ / 100
        r, g, b = colorsys.hls_to_rgb((h % 360) / 360, min(1, max(0, l_)), min(1, max(0, s_)))
        return (int(round(r * 255 + 1e-6)), int(round(g * 255 + 1e-6)), int(round(b * 255 + 1e-6)), alpha)
    if fn == "oklch":
        L, C, H = _num(toks[0], 1), _num(toks[1], 0.4), _hue(toks[2])
        if None in (L, C, H):
            return None
        return oklab_to_rgb(L, C * math.cos(math.radians(H)), C * math.sin(math.radians(H)), alpha)
    if fn == "oklab":
        L, a, b = _num(toks[0], 1), _num(toks[1], 0.4), _num(toks[2], 0.4)
        return None if None in (L, a, b) else oklab_to_rgb(L, a, b, alpha)
    return None


def find_colors(value: str, dark: bool = False) -> list[tuple]:
    value = re.sub(r"url\((?:[^()]|\([^()]*\))*\)", " ", value)
    out = []
    for m in COLOR_RE.finditer(value):
        c = parse_color(m.group(0), dark)
        if c:
            out.append(c)
    return out


def luminance(rgb) -> float:
    r, g, b = (_lin(v / 255) for v in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def dist(a, b) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def over(c, bg):
    """Compõe cor com alfa sobre o fundo."""
    a = c[3] if len(c) > 3 else 1.0
    return tuple(int(round(c[i] * a + bg[i] * (1 - a))) for i in range(3))


def saturated(rgb) -> bool:
    L, C, _ = lch(rgb)
    return C >= 0.07 and 0.25 <= L <= 0.95


def hue_gap(a, b) -> float:
    d = abs(lch(a)[2] - lch(b)[2]) % 360
    return min(d, 360 - d)


# ---------- CSS ----------
_SPECIAL = re.compile(r"[{};\"'(]")
GROUPING = {"@media", "@supports", "@layer", "@container", "@scope", "@starting-style", "@variant", "@document"}
DARK_RE = re.compile(r"(?<![\w-])\.(?:dark|escuro|dark-mode|dark-theme|theme-dark|is-dark|tema-escuro)(?![\w-])|\.[\w-]*(?:theme|mode|scheme|tema|modo)-{1,2}(?:dark|escuro)(?![\w-])|\[[\w-]+[~|^$*]?=[\"']?(?:dark|escuro)[\"']?\]")
LIGHT_RE = re.compile(r"(?<![\w-])\.(?:light|claro|light-mode|light-theme|theme-light|is-light|tema-claro)(?![\w-])|\.[\w-]*(?:theme|mode|scheme|tema|modo)-{1,2}(?:light|claro)(?![\w-])|\[[\w-]+[~|^$*]?=[\"']?(?:light|claro)[\"']?\]")
ROOTISH = {"", ":root", "html", "body", ":host", "*", "html body", ":root body", "html:root", ":root,:host", "html,body"}
COLOR_PROPS = {"color", "background", "background-color", "background-image", "fill", "stroke", "outline", "outline-color", "box-shadow",
               "text-decoration-color", "caret-color", "accent-color", "column-rule-color", "-webkit-text-fill-color"}
POS_SEL = re.compile(r"(?<![\w-])(?:a|button)(?![\w-])|btn|button|cta|primary|brand|accent|link|highlight|badge|selection|submit|active|selected|checked|hero|logo", re.I)
NEG_SEL = re.compile(r"erro|perigo|sucesso|aviso|atencao|alerta|error|danger|destructive|success|warning|warn|invalid|alert|info|toast|chart|syntax|token|hljs|prism|shiki|diff|disabled|skeleton|placeholder|(?<![\w-])(?:code|pre|kbd)(?![\w-])", re.I)
HEAD_SEL = re.compile(r"(?<![\w-])h[1-3](?![\w-])|heading|headline|(?<![\w-])\.?title|display|hero", re.I)
MONO_SEL = re.compile(r"(?<![\w-])(?:code|pre|kbd|samp|tt)(?![\w-])|mono", re.I)
SYSTEM_FONTS = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif", "ui-serif", "ui-monospace", "ui-rounded",
                "math", "emoji", "fangsong", "inherit", "initial", "unset", "revert", "-apple-system", "blinkmacsystemfont", "segoe ui",
                "helvetica neue", "helvetica", "arial", "noto sans", "liberation sans", "apple color emoji", "segoe ui emoji", "segoe ui symbol",
                "noto color emoji", "sf pro text", "sf pro display", "sf pro", "times new roman", "times", "georgia", "tahoma", "verdana",
                "cantarell", "oxygen", "ubuntu", "droid sans", "sfmono-regular", "sf mono", "menlo", "monaco", "consolas", "liberation mono",
                "courier new", "courier", "lucida console", "dejavu sans mono", "andale mono", "ubuntu mono", "lucida grande", "trebuchet ms"}


class Rule:
    __slots__ = ("sel", "decls", "ctx", "origin")

    def __init__(self, sel, decls, ctx, origin):
        self.sel, self.decls, self.ctx, self.origin = sel, decls, ctx, origin


def _nest(parent: str | None, child: str) -> str:
    if not parent:
        return child
    if parent.startswith("@"):
        return f"{parent} {child}"
    if "&" in child:
        return child.replace("&", f":is({parent})" if "," in parent else parent)
    return ", ".join(f"{p.strip()} {c.strip()}" for p in parent.split(",") for c in child.split(","))[:2000]


def parse_css(text: str, origin: str) -> list[Rule]:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    n, rules = len(text), []

    def decl(buf: str, decls: list):
        buf = buf.strip()
        if buf.startswith("@apply"):
            decls.append(("@apply", buf[6:].strip()))
        elif ":" in buf and not buf.startswith("@"):
            p, _, v = buf.partition(":")
            decls.append((p.strip().lower() if not p.strip().startswith("--") else p.strip(), v.strip()))

    def walk(i: int, sel, ctx: tuple, depth: int) -> int:
        decls, buf = [], []
        while i < n:
            m = _SPECIAL.search(text, i)
            if not m:
                buf.append(text[i:])
                i = n
                break
            j, ch = m.start(), m.group(0)
            buf.append(text[i:j])
            if ch in "\"'":
                k = j + 1
                while k < n and text[k] != ch:
                    k += 2 if text[k] == "\\" else 1
                buf.append(text[j:k + 1])
                i = k + 1
            elif ch == "(":
                k, d = j + 1, 1
                while k < n and d:
                    c = text[k]
                    if c in "\"'":
                        k += 1
                        while k < n and text[k] != c:
                            k += 2 if text[k] == "\\" else 1
                    elif c == "(":
                        d += 1
                    elif c == ")":
                        d -= 1
                    k += 1
                buf.append(text[j:k])
                i = k
            elif ch == ";":
                decl("".join(buf), decls)
                buf, i = [], j + 1
            elif ch == "{":
                head = " ".join("".join(buf).split())
                buf = []
                if depth > 40:
                    return n
                if head.startswith("@") and head.split("(")[0].split()[0].lower() in GROUPING:
                    i = walk(j + 1, sel, ctx + (head,), depth + 1)
                else:
                    i = walk(j + 1, _nest(sel, head), ctx, depth + 1)
            else:
                i = j + 1
                break
        decl("".join(buf), decls)
        if sel and decls:
            rules.append(Rule(sel, decls, ctx, origin))
        return i

    i = 0
    while i < n:
        i = walk(i, None, (), 0)
    return rules


def rule_scope(sel: str, ctx: tuple) -> str:
    c = " ".join(ctx).lower()
    if "prefers-color-scheme" in c:
        return "dark" if "dark" in c.split("prefers-color-scheme", 1)[1][:12] else "light"
    parts = [re.sub(r":not\((?:[^()]|\([^()]*\))*\)", "", p) for p in sel.split(",") if p.strip()]
    if parts and all(DARK_RE.search(p) for p in parts):
        return "dark"
    if parts and all(LIGHT_RE.search(p) for p in parts):
        return "light"
    return "base"


def _core(part: str) -> str:
    themed = DARK_RE.sub("", LIGHT_RE.sub("", part))
    p = re.sub(r":not\((?:[^()]|\([^()]*\))*\)|\[[^\]]*\]", "", themed)
    if not p.strip() and themed.strip():  # só atributo, como [data-totem]: é um componente, não a raiz
        return themed.strip().lower()
    p = re.sub(r":(?:where|is)\(\s*([^()]*)\)", r"\1", p)
    return " ".join(p.replace(">", " ").split()).strip().lower()


def norm_name(name: str) -> str:
    n = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name).lower().lstrip("-").replace(".", "-").replace("_", "-")
    segs = [s for s in n.split("-") if s]
    while len(segs) > 1 and segs[0] in {"theme", "colors", "color", "palette", "tokens", "extend", "default", "c", "clr", "tw", "vars", "css", "sys", "ref", "ds", "global", "semantic"}:
        segs.pop(0)
    if len(segs) > 1 and segs[-1] in {"default", "base", "color"}:
        segs.pop()
    return "-".join(segs)


BG_NAMES = ["background", "bg", "fundo", "fundo-pagina", "page-bg", "bg-page", "body-bg", "bg-body", "bg-base", "bg-default", "background-default", "bg-primary",
            "background-primary", "surface-page", "canvas", "page", "paper", "base-100", "surface", "bg-app", "app-bg", "background-base"]
INK_NAMES = ["foreground", "fg", "text", "ink", "texto", "tinta", "texto-principal", "text-primary", "body-color", "text-base", "text-default", "fg-default", "text-color",
             "foreground-primary", "content-primary", "base-content", "text-body", "fg-primary", "on-background", "text-main", "text-strong", "text-solid"]
MUTED_NAMES = ["muted-foreground", "text-muted", "texto-secundario", "texto-suave", "texto-2", "tinta-suave", "secundario", "fg-muted", "muted-fg", "ink-muted", "muted-text", "foreground-muted", "text-secondary",
               "foreground-secondary", "fg-secondary", "secondary-text", "content-secondary", "text-subtle", "fg-subtle", "ink-soft",
               "text-tertiary", "text-2", "text-soft", "text-subdued", "text-quiet", "subtle", "muted"]
LINE_NAMES = ["border", "line", "linha", "borda", "divisor", "divider", "separator", "hairline", "border-color", "border-default", "border-primary", "border-base",
              "border-subtle", "stroke", "rule", "outline-variant", "input"]
ACCENT_EXACT = {"primary", "brand", "accent", "acento", "marca", "acao", "destaque", "primaria", "primario", "cor-primaria", "cor-marca", "principal", "brand-primary", "primary-color", "brand-color", "accent-color", "cta", "main", "link",
                "action", "highlight", "interactive", "brand-accent", "accent-primary", "primary-brand", "brand-main"}
ACCENT_SHADE = re.compile(r"^(primary|brand|accent|acento|marca|acao)-(500|600|main|solid|solido|9|strong)$")
ACCENT_PART = re.compile(r"(?:^|-)(primary|brand|accent|cta|highlight|link|acento|marca|acao|destaque)(?:-|$)")
ACCENT_EXCL = re.compile(r"tinta|fundo|borda|texto|suave|sutil|superficie|campo|titulo|etiqueta|fraco|contraste|foreground|(?:^|-)fg(?:-|$)|(?:^|-)on-|contrast|content|text|(?:^|-)bg(?:-|$)|subtle|soft|muted|surface|background|border|ring|shadow|glow|tint|dim|sidebar|chart")
NEG_NAME = re.compile(r"erro|perigo|sucesso|aviso|atencao|alerta|(?:^|-)ok(?:-|$)|error|danger|destructive|success|warning|warn|invalid|alert|info|chart|syntax|macro|(?:^|-)(?:red|green|yellow)(?:-|$)")
COMPONENT_WORDS = {"card", "popover", "sidebar", "button", "btn", "input", "nav", "navbar", "header", "footer", "modal", "dialog", "tooltip", "code",
                   "menu", "dropdown", "badge", "chip", "table", "hover", "active", "inverse", "inverted", "on", "alt", "secondary", "tertiary",
                   "muted", "disabled", "selected", "overlay", "banner", "toast", "tab", "tabs", "panel", "hero", "accent", "primary", "brand",
                   "link", "error", "success", "warning", "danger", "info", "dark", "light", "scrollbar", "selection", "placeholder", "kbd"}
NAMESPACE_WORDS = {"color", "colors", "clr", "theme", "sys", "ref", "ds", "global", "semantic", "core", "ui", "app", "site", "token", "tokens", "palette"}
SECOND_NAMES = ["secondary", "secundaria", "acento-2", "acento-secundario", "marca-2", "accent-2", "accent2", "second", "brand-secondary", "secondary-color", "accent-secondary", "tertiary", "brand-2"]


class Sheet:
    """Regras CSS de todas as fontes, com custom properties por escopo de tema."""

    def __init__(self):
        self.rules: list[Rule] = []
        self.vars = {s: {"root": {}, "other": {}} for s in ("base", "dark", "light")}
        self.wrap: dict[str, str] = {}
        self.fontfaces: list[tuple[str, str]] = []
        self.extra: list[tuple[str, str, str, str]] = []  # (nome, valor, origem, escopo) de tailwind.config e objetos de tema
        self.tw_fonts: dict[str, tuple[list[str], str]] = {}

    def add_css(self, text: str, origin: str):
        for m in re.finditer(r"\b(rgba?|hsla?|oklch|oklab)\(\s*var\(\s*(--[\w-]+)", text):
            self.wrap.setdefault(m.group(2), m.group(1))
        for r in parse_css(text, origin):
            self.rules.append(r)
            if r.sel.startswith("@font-face"):
                d = dict(r.decls)
                if d.get("font-family"):
                    self.fontfaces.append((clean_family(d["font-family"]), origin))
                continue
            custom = [(p, v) for p, v in r.decls if p.startswith("--")]
            if not custom:
                continue
            if r.sel.startswith("@theme"):
                scope, bucket = "base", "root"
            elif r.sel.startswith("@"):
                continue
            else:
                scope = rule_scope(r.sel, r.ctx)
                bucket = "root" if any(_core(p) in ROOTISH for p in r.sel.split(",")) else "other"
            store = self.vars[scope][bucket]
            for p, v in custom:
                if re.fullmatch(r"var\(\s*" + re.escape(p) + r"\s*\)", v.strip()):  # --font-sans: var(--font-sans) no @theme inline
                    continue
                if bucket == "root" or p not in store:
                    store[p] = (v, f"{p} em `{r.sel[:60]}` ({origin})")

    def lookup(self, name: str, theme: str):
        order = [self.vars[theme]["root"], self.vars["base"]["root"], self.vars[theme]["other"], self.vars["base"]["other"]]
        for store in order:
            if name in store:
                return store[name]
        return None

    def resolve(self, value: str, theme: str) -> str | None:
        for _ in range(16):
            m = re.search(r"var\(\s*(--[\w-]+)\s*(?:,((?:[^()]|\((?:[^()]|\([^()]*\))*\))*))?\)", value)
            if not m:
                return value.replace("/ <alpha-value>", "").replace("<alpha-value>", "1")
            hit = self.lookup(m.group(1), theme)
            rep = hit[0] if hit else m.group(2)
            if rep is None:
                return None
            if hit and TRIPLET_PCT.match(rep.strip()) is None and m.group(1) in self.wrap and parse_color(rep) is None and "(" not in rep \
                    and not re.search(r"(?:rgba?|hsla?|oklch|oklab)\(\s*$", value[:m.start()]):
                rep = f"{self.wrap[m.group(1)]}({rep.strip()})"
            value = value[:m.start()] + rep.strip() + value[m.end():]
        return None

    def color(self, value: str, theme: str, name: str | None = None):
        v = self.resolve(value, theme)
        if v is None:
            return None
        v = v.strip()
        c = parse_color(v, theme == "dark")
        if c is None and TRIPLET_PCT.match(v):
            c = parse_color(f"{self.wrap.get(name or '', 'hsl')}({v})")
        if c is None and name in self.wrap and re.fullmatch(r"[\d.\s,%/]+", v):
            c = parse_color(f"{self.wrap[name]}({v})")
        return c

    def tokens(self, theme: str, root_only: bool = False):
        """(nome normalizado, rgba, origem) de tudo que tem nome: custom properties, tailwind.config e objetos de tema."""
        seen = set()
        stores = [self.vars[theme]["root"], self.vars["base"]["root"]] + ([] if root_only else [self.vars[theme]["other"], self.vars["base"]["other"]])
        for store in stores:
            for name, (val, origin) in store.items():
                if name in seen:
                    continue
                seen.add(name)
                if len(val) > 200:
                    continue
                c = self.color(val, theme, name)
                if c:
                    yield norm_name(name), c, origin
        for name, val, origin, scope in self.extra:
            if scope in ("base", theme):
                c = self.color(val, theme)
                if c:
                    yield norm_name(name), c, origin

    def by_names(self, theme: str, names: list[str], root_only: bool = False):
        """Primeiro token cujo nome é um dos papéis, ou termina nele com um prefixo de namespace (--hds-color-text-solid)."""
        toks = {}
        for n, c, o in self.tokens(theme, root_only):
            toks.setdefault(n, (c, o))
        for n in names:
            if n in toks:
                return toks[n]
        for n in names:
            for k, v in toks.items():
                if k.endswith("-" + n):
                    pre = k[: -len(n) - 1].split("-")
                    if all(seg in NAMESPACE_WORDS or (i == 0 and len(seg) <= 4 and seg not in COMPONENT_WORDS) for i, seg in enumerate(pre)):
                        return v
        return None

    def class_color(self, name: str, theme: str):
        """Nome de utilitário Tailwind (bg-NOME) -> cor, pelo que o projeto define."""
        if name.startswith("[") and name.endswith("]"):
            return parse_color(name[1:-1])
        name = name.split("/")[0]
        for var in (f"--color-{name}", f"--{name}"):
            hit = self.lookup(var, theme)
            if hit:
                c = self.color(hit[0], theme, var)
                if c:
                    return c
        for n, val, _o, scope in self.extra:
            if scope in ("base", theme) and n.startswith("tw:") and n[3:] == name:
                return self.color(val, theme)
        return {"white": (255, 255, 255, 1.0), "black": (0, 0, 0, 1.0)}.get(name)


def clean_family(raw: str) -> str:
    f = raw.strip().strip("\"'").strip()
    m = re.fullmatch(r"__(.+?)_[0-9a-f]{6}", f)
    if m:
        f = m.group(1).replace("_", " ")
    return f


def families(value: str) -> list[str]:
    out = []
    for part in _split_top(value.replace("!important", "")):
        f = clean_family(part)
        if f and "var(" not in f and "fallback" not in f.lower():
            out.append(f)
    return out


def first_real(fams: list[str]) -> str | None:
    """Primeira família da pilha, se não for fonte de sistema."""
    return fams[0] if fams and fams[0].lower() not in SYSTEM_FONTS else None


def font_shorthand(value: str) -> str | None:
    m = re.search(r"(?:^|\s)[\d.]+(?:px|rem|em|%|pt|vw)(?:\s*/\s*[\w.%]+)?\s+(.+)$", value)
    return m.group(1) if m else None


# ---------- objetos literais JS (tailwind.config, theme.ts) ----------
def parse_js_value(s: str, i: int):
    """Lê um literal JS a partir de i. Devolve (valor, fim). Expressão que não é literal vira None."""
    n = len(s)

    def ws(i):
        while i < n:
            if s[i].isspace():
                i += 1
            elif s.startswith("//", i):
                j = s.find("\n", i)
                i = n if j < 0 else j
            elif s.startswith("/*", i):
                j = s.find("*/", i)
                i = n if j < 0 else j + 2
            else:
                break
        return i

    def string(i):
        q, k, out = s[i], i + 1, []
        while k < n and s[k] != q:
            if s[k] == "\\" and k + 1 < n:
                out.append(s[k + 1])
                k += 2
            else:
                out.append(s[k])
                k += 1
        txt = "".join(out)
        return (None if q == "`" and "${" in txt else txt), k + 1

    def raw(i):
        d = 0
        while i < n:
            c = s[i]
            if c in "\"'`":
                _, i = string(i)
                continue
            if c in "([{":
                d += 1
            elif c in ")]}":
                if d == 0:
                    break
                d -= 1
            elif c == "," and d == 0:
                break
            i += 1
        return None, i

    def value(i, depth=0):
        i = ws(i)
        if i >= n or depth > 12:
            return None, n
        c = s[i]
        if c in "\"'`":
            v, j = string(i)
            k = ws(j)
            if k < n and s[k] not in ",}])":  # 'a' + b, 'x' as const...
                if s.startswith("as ", k) or s.startswith("satisfies ", k):
                    return v, raw(k)[1]
                return None, raw(k)[1]
            return v, j
        if c == "{":
            obj, i = {}, i + 1
            while True:
                i = ws(i)
                if i >= n:
                    return obj, n
                if s[i] == "}":
                    return obj, i + 1
                if s[i] == ",":
                    i += 1
                    continue
                if s.startswith("...", i):
                    _, i = raw(i)
                    continue
                if s[i] in "\"'`":
                    key, i = string(i)
                elif s[i] == "[":
                    _, i = raw(i + 1)
                    key, i = None, i + 1
                else:
                    m = re.compile(r"[\w$-]+").match(s, i)
                    if not m:
                        _, i = raw(i + 1)
                        continue
                    key, i = m.group(0), m.end()
                i = ws(i)
                if i < n and s[i] == ":":
                    v, i = value(i + 1, depth + 1)
                    if key is not None:
                        obj[key] = v
                else:
                    _, i = raw(i)
        if c == "[":
            arr, i = [], i + 1
            while True:
                i = ws(i)
                if i >= n:
                    return arr, n
                if s[i] == "]":
                    return arr, i + 1
                if s[i] == ",":
                    i += 1
                    continue
                v, i = value(i, depth + 1)
                arr.append(v)
        return raw(i)

    return value(i)


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = prefix if k == "DEFAULT" and prefix else (f"{prefix}-{k}" if prefix else str(k))
            yield from flatten(v, key)
    elif isinstance(obj, str):
        yield prefix, obj


# ---------- pixels ----------
def histogram(path: pathlib.Path) -> dict[int, tuple[tuple, float]]:
    import numpy as np
    from PIL import Image

    im = Image.open(path).convert("RGB")
    if max(im.size) > 1800:
        im.thumbnail((1800, 1800), Image.NEAREST)
    a = np.asarray(im).reshape(-1, 3).astype(np.uint32)
    vals, cnt = np.unique((a[:, 0] << 16) | (a[:, 1] << 8) | a[:, 2], return_counts=True)
    order = np.argsort(-cnt, kind="stable")
    vals, cnt = vals[order], cnt[order]
    key = (((vals >> 19) & 31) << 10) | (((vals >> 11) & 31) << 5) | ((vals >> 3) & 31)
    ukey, first, inv = np.unique(key, return_index=True, return_inverse=True)
    binc = np.bincount(inv, weights=cnt) / cnt.sum()
    out = {}
    for b in np.argsort(-binc)[:500]:
        v = int(vals[first[b]])
        out[int(ukey[b])] = (((v >> 16) & 255, (v >> 8) & 255, v & 255), float(binc[b]))
    return out


class Pixels:
    def __init__(self):
        self.files: list[str] = []
        self.bins: dict[int, list] = {}

    def add(self, path: pathlib.Path, label: str):
        h = histogram(path)
        for k, (rgb, share) in h.items():
            cur = self.bins.setdefault(k, [rgb, 0.0, share])
            cur[1] += share
            if share > cur[2]:
                cur[0], cur[2] = rgb, share
        self.files.append(label)

    def ranked(self) -> list[tuple[tuple, float]]:
        n = max(1, len(self.files))
        return sorted(((b[0], b[1] / n) for b in self.bins.values()), key=lambda t: -t[1])

    def share(self, rgb, tol: float = 16.0) -> float:
        return sum(s for c, s in self.ranked() if dist(c, rgb) <= tol)


# ---------- HTML ----------
class Page(HTMLParser):
    TRACK = {"header", "nav", "footer", "a", "div", "section", "ul", "li", "span", "main", "aside", "button", "picture", "figure", "p"}
    BAD = re.compile(r"customer|client|partner|sponsor|trusted|testimonial|logos|logo-?(?:cloud|grid|wall|strip|garden|marquee|list|row)|press|investor|backed|payment|social|carousel|slider", re.I)

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.title = ""
        self.meta: dict[str, list[tuple[str, str]]] = {}
        self.links: list[dict] = []
        self.styles: list[str] = []
        self.headings: list[tuple[str, str]] = []
        self.imgs: list[tuple[int, str, str]] = []
        self.svgs: list[tuple[int, str]] = []
        self.ld: list[str] = []
        self.html_attrs: dict = {}
        self.body_attrs: dict = {}
        self._stack: list[tuple[str, str]] = []
        self._text = None
        self._h = None
        self._svg = None
        self._svg_names: list[str] = []
        self._svg_score = 0
        self._svg_skip = 0

    def _home(self, href: str) -> bool:
        if not href:
            return False
        u = urllib.parse.urlsplit(urllib.parse.urljoin(self.base, href))
        b = urllib.parse.urlsplit(self.base)
        return u.netloc == b.netloc and (u.path in ("", "/") or u.path.rstrip("/") == b.path.rstrip("/") or bool(re.fullmatch(r"/[a-z]{2}(?:-[a-zA-Z]{2})?/?", u.path)))

    def _ctx(self, own: str):
        tags = [t for t, _ in self._stack]
        in_header = "header" in tags or "nav" in tags
        in_footer = "footer" in tags
        home = any(t == "a" and self._home(a.split("\x00")[0]) for t, a in self._stack)
        near = " ".join(a.split("\x00")[1] for _, a in self._stack[-4:])
        has_logo = bool(re.search(r"logo|wordmark|brand", own + " " + near, re.I))
        bad = bool(self.BAD.search(own + " " + near))
        score = (6 if in_header else 0) + (4 if home else 0) + (3 if has_logo else 0) - (10 if bad else 0) - (6 if in_footer else 0)
        return score, (has_logo or (in_header and home)) and not bad

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if self._svg is not None:
            raw = self.get_starttag_text() or ""
            self._svg.append(raw)
            if not raw.rstrip().endswith("/>"):
                m = re.match(r"<\s*([\w:-]+)", raw)
                self._svg_names.append(m.group(1) if m else tag)
            return
        if self._svg_skip:
            if tag == "svg":
                self._svg_skip += 1
            return
        if tag == "html":
            self.html_attrs = a
        elif tag == "body":
            self.body_attrs = a
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key:
                self.meta.setdefault(key, []).append((a.get("content", ""), a.get("media", "")))
        elif tag == "link":
            self.links.append(a)
        elif tag in ("title", "style") or (tag == "script" and "ld+json" in a.get("type", "")):
            self._text = [tag, []]
        elif tag in ("h1", "h2", "h3") and self._h is None:
            self._h = [tag, []]
        elif self._h is not None and tag in ("br", "div", "p", "li"):
            self._h[1].append(" ")
        if tag == "img":
            src = a.get("src") or a.get("data-src") or ""
            own = " ".join((src if not src.startswith("data:") else "", a.get("alt", ""), a.get("class", ""), a.get("id", "")))
            score, ok = self._ctx(own)
            if src and ok:
                self.imgs.append((score, src, a.get("alt", "")))
        elif tag == "svg":
            own = " ".join((a.get("class", ""), a.get("id", ""), a.get("aria-label", ""), a.get("aria-labelledby", "")))
            score, ok = self._ctx(own)
            if ok and len(self.svgs) < 6:
                self._svg, self._svg_names, self._svg_score = [self.get_starttag_text() or "<svg>"], ["svg"], score
            else:
                self._svg_skip = 1
        if tag in self.TRACK:
            self._stack.append((tag, a.get("href", "") + "\x00" + " ".join((a.get("class", ""), a.get("id", ""), a.get("aria-label", ""), a.get("title", "")))))

    def handle_startendtag(self, tag, attrs):
        if self._svg is not None:
            self._svg.append(self.get_starttag_text() or "")
            return
        self.handle_starttag(tag, attrs)
        if tag in self.TRACK and self._stack and self._stack[-1][0] == tag:
            self._stack.pop()
        if tag == "svg" and self._svg_skip:
            self._svg_skip -= 1

    def handle_endtag(self, tag):
        if self._svg is not None:
            if self._svg_names:
                self._svg.append(f"</{self._svg_names.pop()}>")
            if not self._svg_names:
                self.svgs.append((self._svg_score, "".join(self._svg)))
                self._svg = None
            return
        if self._svg_skip:
            if tag == "svg":
                self._svg_skip -= 1
            return
        if self._text and tag == self._text[0]:
            txt = "".join(self._text[1])
            if tag == "title":
                self.title = self.title or " ".join(txt.split())
            elif tag == "style":
                self.styles.append(txt)
            else:
                self.ld.append(txt)
            self._text = None
        if self._h and tag == self._h[0]:
            txt = " ".join("".join(self._h[1]).split())
            for k in (4, 3, 2):  # o mesmo título repetido para cada breakpoint
                unit = txt[: len(txt) // k]
                if len(unit) > 3 and (unit * k == txt or " ".join([unit.strip()] * k) == txt):
                    txt = unit.strip()
                    break
            if 2 < len(txt) <= 220:
                self.headings.append((tag, txt))
            self._h = None
        for k in range(len(self._stack) - 1, -1, -1):
            if self._stack[k][0] == tag:
                del self._stack[k:]
                break

    def handle_data(self, data):
        if self._svg is not None:
            self._svg.append(data)
        elif self._svg_skip:
            return
        elif self._text is not None:
            self._text[1].append(data)
        elif self._h is not None:
            self._h[1].append(data)

    def m(self, key: str) -> str:
        v = self.meta.get(key)
        return " ".join(v[0][0].split()) if v else ""


def pick_headlines(headings: list[tuple[str, str]]) -> list[str]:
    out = []
    for level in (("h1", "h2"), ("h3",)):
        for tag, txt in headings:
            if tag in level and txt not in out and len(out) < 5:
                out.append(txt)
        if len(out) >= 3:
            break
    return out


# ---------- coleta ----------
class Bag:
    def __init__(self, out: pathlib.Path):
        self.out = out
        self.assets = out / "assets"
        self.sheet = Sheet()
        self.pixels = Pixels()
        self.names: list[tuple[int, str, str]] = []
        self.logos: list[tuple[int, str, str]] = []  # (prioridade, caminho relativo em assets, origem)
        self.icons: list[tuple[str, str]] = []
        self.copy = {"title": None, "description": None, "headlines": []}
        self.theme_hints: list[tuple[str, str]] = []
        self.font_vars: dict[str, tuple[str, str]] = {}
        self.loaded_fonts: list[tuple[str, str]] = []
        self.body_classes: list[tuple[str, str]] = []
        self.body_font_hint: tuple[str, str] | None = None
        self.class_use: dict[tuple[str, str], int] = {}
        self.theme_color: list[tuple[tuple, str]] = []
        self.sources: list[str] = []
        self.warnings: list[str] = []
        self.shots: list[str] = []
        self.chrome: str | None = None
        self.assets_saved: list[str] = []
        self.logo_alternatives: list[str] = []

    def save(self, name: str, data: bytes) -> str:
        self.assets.mkdir(parents=True, exist_ok=True)
        (self.assets / name).write_bytes(data)
        rel = f"assets/{name}"
        if rel not in self.assets_saved:
            self.assets_saved.append(rel)
        return rel

    def warn(self, msg: str):
        if msg not in self.warnings:
            self.warnings.append(msg)
            log(f"aviso: {msg}")


def find_chromes() -> list[str]:
    found = []
    here = pathlib.Path.cwd().resolve()
    for d in [here, *here.parents]:
        base = d / "node_modules" / ".remotion" / "chrome-headless-shell"
        if base.is_dir():
            found += [str(p) for p in sorted(base.rglob("chrome-headless-shell")) if p.is_file() and os.access(p, os.X_OK)]
    for name in ("chromium", "chromium-browser", "google-chrome"):
        p = shutil.which(name)
        if p:
            found.append(p)
    return list(dict.fromkeys(found))


class Chrome:
    """Roda o Chrome pela linha de comando do próprio binário. Guarda a primeira combinação que funcionou."""

    def __init__(self, bag: "Bag", allow_no_sandbox: bool):
        self.bag = bag
        self.found = find_chromes()
        self.tries = [(c, []) for c in self.found] + ([(c, ["--no-sandbox"]) for c in self.found] if allow_no_sandbox else [])
        self.errors: list[str] = []

    def run(self, args: list[str], url: str, produced: pathlib.Path | None = None) -> str | None:
        """Devolve o stdout se funcionou (e, com `produced`, se o arquivo foi escrito), senão None."""
        for combo in list(self.tries):
            chrome, extra = combo
            with tempfile.TemporaryDirectory(prefix="brand-chrome-") as prof:
                cmd = [chrome, "--headless", *args, "--hide-scrollbars", "--virtual-time-budget=8000", "--force-device-scale-factor=1",
                       "--no-first-run", "--disable-extensions", "--mute-audio", f"--user-data-dir={prof}/p", *extra, url]
                if produced:
                    cmd.insert(2, f"--screenshot={prof}/shot.png")
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=45, cwd=prof)
                    err = ([ln for ln in (r.stderr or "").splitlines() if "FATAL" in ln or "ERROR" in ln] or [f"código {r.returncode}"])[0]
                    err = re.sub(r"^\[[^\]]*\]\s*", "", err)[:110]
                    ok = (pathlib.Path(prof) / "shot.png").is_file() if produced else "<" in r.stdout
                    if ok:
                        if produced:
                            produced.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(pathlib.Path(prof) / "shot.png", produced)
                        self.tries = [combo]
                        self.bag.chrome = " ".join([chrome, *extra])
                        if extra:
                            self.bag.warn("o Chrome rodou com --no-sandbox, a pedido (--allow-no-sandbox): a página foi aberta sem isolamento de processo")
                        return r.stdout or " "
                except subprocess.TimeoutExpired:
                    err = "tempo esgotado (45 s)"
                except OSError as e:
                    err = str(e)[:110]
            self.errors.append(f"{pathlib.Path(chrome).name}{' --no-sandbox' if extra else ''}: {err}")
            if len(self.tries) == 1:  # a combinação que já funcionou falhou nesta página: não troca de binário
                break
        return None


class Net:
    def __init__(self, bag: Bag, root_host: str):
        import requests

        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
        self.bag, self.root_host, self.count, self.seen = bag, root_host, 0, set()

    def allowed(self, url: str) -> bool:
        u = urllib.parse.urlsplit(url)
        if u.scheme not in ("http", "https") or not u.hostname:
            return False
        if u.hostname == self.root_host:
            return True
        host = u.hostname
        if host == "localhost" or host.endswith((".local", ".internal", ".localhost")):
            return False
        try:
            ip = ipaddress.ip_address(host)
            return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)
        except ValueError:
            return True

    def get(self, url: str, limit: int, what: str):
        """(bytes, content-type, url final) ou None. Um erro HTTP é registrado e não há nova tentativa."""
        import requests

        if url in self.seen or not self.allowed(url):
            return None
        self.seen.add(url)
        if self.count >= MAX_REQUESTS:
            self.bag.warn(f"limite de {MAX_REQUESTS} requisições atingido; parte dos arquivos não foi baixada")
            return None
        self.count += 1
        try:
            with self.s.get(url, timeout=TIMEOUT, stream=True) as r:
                if r.status_code >= 400:
                    self.bag.warn(f"{what}: HTTP {r.status_code} em {url[:120]}")
                    return None
                buf = bytearray()
                for chunk in r.iter_content(65536):
                    buf += chunk
                    if len(buf) > limit:
                        self.bag.warn(f"{what}: maior que {limit // 1_000_000} MB, ignorado ({url[:120]})")
                        return None
                return bytes(buf), r.headers.get("content-type", "").lower(), r.url, r.encoding
        except requests.RequestException as e:
            self.bag.warn(f"{what}: falha de rede em {url[:120]} ({type(e).__name__})")
            return None


def decode(data: bytes, enc: str | None, ctype: str) -> str:
    if "charset" not in ctype:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", data[:4096], re.I)
        enc = m.group(1).decode("ascii", "replace") if m else "utf-8"
    try:
        return data.decode(enc or "utf-8", errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def ext_of(url: str, ctype: str, data: bytes) -> str | None:
    for key, ext in (("svg", ".svg"), ("png", ".png"), ("jpeg", ".jpg"), ("jpg", ".jpg"), ("webp", ".webp"), ("x-icon", ".ico"),
                     ("vnd.microsoft.icon", ".ico"), ("gif", ".gif"), ("avif", ".avif")):
        if key in ctype:
            return ext
    if data[:8].startswith(b"\x89PNG"):
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"\x00\x00\x01\x00":
        return ".ico"
    if b"<svg" in data[:2000]:
        return ".svg"
    e = pathlib.PurePosixPath(urllib.parse.urlsplit(url).path).suffix.lower()
    return e if e in (".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".gif") else None


def name_from_title(title: str, hint: str) -> str | None:
    """Segmento do título que casa com o domínio ou o nome do pacote."""
    key = re.sub(r"[^a-z0-9]", "", hint.lower())
    segs = [s.strip() for s in re.split(r"\s[|–—·:•-]\s|\s*[|–—·•]\s*|:\s", title) if s.strip()]
    for s in segs:
        k = re.sub(r"[^a-z0-9]", "", s.lower())
        if k and key and (k == key or (len(k) >= 3 and (k in key or key in k) and len(s) <= 40)):
            return s
    return None


def collect_css_imports(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"@import\s+(?:url\(\s*)?[\"']?([^\"')\s;]+)", text)]


def google_families(url: str) -> list[str]:
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url.replace("&amp;", "&")).query)
    out = []
    for fam in q.get("family", []):
        for f in fam.split("|"):
            f = f.split(":")[0].replace("+", " ").strip()
            if f:
                out.append(f)
    return out


def from_url(bag: Bag, url: str, shots: bool, allow_no_sandbox: bool = False):
    if not re.match(r"https?://", url):
        url = "https://" + url
    host = urllib.parse.urlsplit(url).hostname or ""
    net = Net(bag, host)
    log(f"baixando {url}")
    res = net.get(url, MAX_CSS, "página")
    today = dt.date.today().isoformat()
    final = url
    if res is None:
        bag.warn(f"não foi possível baixar {url}: sem HTML, a extração depende só do screenshot")
        page = Page(url)
    else:
        data, ctype, final, enc = res
        net.root_host = urllib.parse.urlsplit(final).hostname or host
        page = Page(final)
        try:
            page.feed(decode(data, enc, ctype))
        except Exception as e:  # HTML quebrado não derruba a extração
            bag.warn(f"HTML lido parcialmente ({type(e).__name__})")
    bag.sources.append(f"{final} ({today})")
    label = urllib.parse.urlsplit(final).hostname or host
    dom = label.removeprefix("www.").split(".")[0]

    # nome
    for prio, key in ((9, "og:site_name"), (8, "application-name"), (7, "apple-mobile-web-app-title")):
        if page.m(key):
            bag.names.append((prio, page.m(key), f"meta {key} de {label}"))
    for raw in page.ld:
        try:
            for node in _walk_json(json.loads(raw)):
                if isinstance(node, dict) and node.get("@type") in ("Organization", "WebSite", "Corporation", "Brand") and isinstance(node.get("name"), str):
                    bag.names.append((6, node["name"].strip(), f"JSON-LD {node['@type']} de {label}"))
                if isinstance(node, dict) and node.get("logo"):
                    lg = node["logo"]
                    lg = lg.get("url") if isinstance(lg, dict) else lg
                    if isinstance(lg, str):
                        page.imgs.append((12, lg, "JSON-LD logo"))
        except (ValueError, TypeError):
            pass
    title = page.title or page.m("og:title")
    if title:
        seg = name_from_title(title, dom)
        if seg:
            bag.names.append((5, seg, f"trecho do <title> que casa com o domínio {label}"))
    bag.names.append((1, dom, f"rótulo do domínio {label} (nenhum nome declarado na página)"))

    # texto
    bag.copy["title"] = bag.copy["title"] or title or None
    bag.copy["description"] = bag.copy["description"] or page.m("description") or page.m("og:description") or None
    heads = pick_headlines(page.headings)

    # tema declarado
    cls = " " + page.html_attrs.get("class", "") + " " + page.body_attrs.get("class", "") + " "
    for attr in ("data-theme", "data-mode", "data-color-mode", "data-color-scheme", "data-bs-theme"):
        v = (page.html_attrs.get(attr) or page.body_attrs.get(attr) or "").lower()
        if v in ("dark", "light"):
            bag.theme_hints.append((v, f'{attr}="{v}" no HTML'))
    if re.search(r"\s(dark|dark-mode|theme-dark)\s", cls):
        bag.theme_hints.append(("dark", "classe dark em <html> ou <body>"))
    cs = page.m("color-scheme").lower()
    if cs.startswith("dark"):
        bag.theme_hints.append(("dark", f'meta color-scheme "{cs}"'))
    for content, media in page.meta.get("theme-color", []):
        c = parse_color(content)
        if c:
            bag.theme_color.append((c, f"meta theme-color{' ' + media if media else ''}"))

    # CSS
    for n, st in enumerate(page.styles):
        bag.sheet.add_css(st, f"<style> {n + 1} de {label}")
    inline = "".join(f"{sel}{{{a.get('style')}}}" for sel, a in (("html", page.html_attrs), ("body", page.body_attrs)) if a.get("style"))
    if inline:
        bag.sheet.add_css(inline, f"atributo style de {label}")
    queue = []
    for a in page.links:
        rel = a.get("rel", "").lower().split()
        href = a.get("href", "")
        if not href:
            continue
        if "stylesheet" in rel or ("preload" in rel and a.get("as") == "style"):
            queue.append((urllib.parse.urljoin(final, href), 0))
    for st in page.styles:
        queue += [(urllib.parse.urljoin(final, u), 1) for u in collect_css_imports(st)]
    n_css = 0
    while queue and n_css < 90:
        css_url, depth = queue.pop(0)
        if "fonts.googleapis.com" in css_url:
            for f in google_families(css_url):
                bag.loaded_fonts.append((f, "Google Fonts linkado na página"))
        got = net.get(css_url, MAX_CSS, "CSS")
        if not got:
            continue
        text = decode(got[0], got[3] if "charset" in got[1] else "utf-8", "charset")
        n_css += 1
        short = urllib.parse.urlsplit(got[2])
        bag.sheet.add_css(text, f"{short.hostname}{short.path[-48:]}")
        if depth < 3:
            queue += [(urllib.parse.urljoin(got[2], u), depth + 1) for u in collect_css_imports(text)]
    log(f"CSS: {n_css} folhas, {len(page.styles)} blocos <style>, {len(bag.sheet.rules)} regras")
    if not bag.sheet.rules:
        bag.warn("nenhuma regra CSS legível (site monta o estilo por JavaScript ou bloqueou o acesso): paleta só pelos pixels")

    # ícones, logo, og:image
    icons = []
    for a in page.links:
        rel = a.get("rel", "").lower()
        if a.get("href") and "icon" in rel:
            size = max([int(x) for x in re.findall(r"\d+", a.get("sizes", ""))] or [0])
            svg = a["href"].split("?")[0].endswith(".svg") or "svg" in a.get("type", "")
            icons.append((2 if "apple-touch" in rel else (3 if svg else 1), size, urllib.parse.urljoin(final, a["href"]), rel))
    icons.sort(key=lambda t: (-t[0], -t[1]))
    done = set()
    for kind, _size, iu, rel in icons:
        base = "apple-touch-icon" if kind == 2 else "favicon"
        if base in done or (kind == 3 and "favicon" in done):
            continue
        got = net.get(iu, MAX_IMG, "ícone")
        ext = got and ext_of(got[2], got[1], got[0])
        if ext:
            done.add(base)
            bag.icons.append((bag.save(base + ext, got[0]), f'<link rel="{rel}"> de {label}'))
    if "favicon" not in done and res is not None:
        got = net.get(urllib.parse.urljoin(final, "/favicon.ico"), MAX_IMG, "favicon")
        ext = got and ext_of(got[2], got[1], got[0])
        if ext and "html" not in got[1]:
            bag.icons.append((bag.save("favicon" + ext, got[0]), f"/favicon.ico de {label}"))
    og = page.m("og:image") or page.m("twitter:image")
    if og:
        got = net.get(urllib.parse.urljoin(final, og), MAX_IMG, "og:image")
        ext = got and ext_of(got[2], got[1], got[0])
        if ext:
            bag.save("og" + ext, got[0])
    cands = [(s, "img", src, alt) for s, src, alt in page.imgs] + [(s, "svg", raw, "") for s, raw in page.svgs if _svg_ok(raw)]
    cands.sort(key=lambda t: -t[0])
    for score, kind, payload, alt in cands[:4]:
        if kind == "svg":
            raw = payload if "xmlns" in payload[:400] else payload.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
            n_var = len(re.findall(r"var\(", raw))
            raw = re.sub(r"var\(\s*--[\w-]+[^()]*\)", lambda m: (bag.sheet.resolve(m.group(0), "base") or m.group(0)).strip(), raw)
            note = "; usa currentColor, a cor vem do CSS do site" if "currentColor" in raw else ""
            note += f"; {n_var} var() trocadas pelo valor do CSS padrão" if n_var else ""
            bag.logos.append((score + 20, bag.save("logo.svg", raw.encode("utf-8")), f"SVG inline no cabeçalho de {label}{note}"))
            break
        if payload.startswith("data:"):
            m = re.match(r"data:(image/[\w.+-]+)?(;base64)?,(.*)", payload, re.S)
            if not m:
                continue
            blob = base64.b64decode(m.group(3)) if m.group(2) else urllib.parse.unquote_to_bytes(m.group(3))
            ext = ext_of("", m.group(1) or "", blob)
            src = "data URI"
        else:
            got = net.get(urllib.parse.urljoin(final, payload), MAX_IMG, "logo")
            if not got:
                continue
            blob, ext, src = got[0], ext_of(got[2], got[1], got[0]), got[2][:120]
        if ext:
            bag.logos.append((score + 20, bag.save("logo" + ext, blob), f"<img> de logo em {label} ({src}{', alt ' + repr(alt) if alt else ''})"))
            break

    # screenshots
    if shots and res is None:
        bag.warn("screenshot não tirado: a página não respondeu, e a tela de erro não é a marca")
    elif shots:
        ch = Chrome(bag, allow_no_sandbox)
        if not ch.found:
            bag.warn("Chrome não encontrado (node_modules/.remotion, chromium, chromium-browser, google-chrome): sem screenshot, paleta só pelo CSS")
        else:
            for name, w, h in (("desktop", 1440, 900), ("celular", 390, 844)):
                dest = bag.assets / f"screenshot-{name}.png"
                log(f"screenshot {name} {w}x{h}")
                if ch.run([f"--window-size={w},{h}"], final, dest) is None:
                    hint = "" if allow_no_sandbox or not any("sandbox" in e.lower() for e in ch.errors) else "; se o sandbox do Chrome não funciona nesta máquina, --allow-no-sandbox libera a execução sem ele"
                    bag.warn(f"screenshot {name} falhou ({' | '.join(ch.errors[-3:])}){hint}")
                    if bag.chrome is None:
                        break
                    continue
                rel = f"assets/screenshot-{name}.png"
                bag.assets_saved.append(rel)
                bag.shots.append(rel)
                try:
                    from PIL import Image

                    with Image.open(dest) as im:
                        if abs(im.size[0] - w) > 2:
                            bag.warn(f"screenshot {name} saiu com {im.size[0]}x{im.size[1]} em vez de {w}x{h}: este Chrome não aceita a largura pedida")
                    bag.pixels.add(dest, rel)
                except Exception as e:
                    bag.warn(f"screenshot {name} ilegível ({type(e).__name__})")
            if not heads and bag.chrome:  # página montada por JavaScript: lê os títulos do DOM renderizado
                dom_html = ch.run(["--dump-dom"], final)
                if dom_html:
                    p2 = Page(final)
                    try:
                        p2.feed(dom_html)
                    except Exception:
                        pass
                    heads = pick_headlines(p2.headings)
                    if heads:
                        bag.copy["headlines_source"] = "DOM renderizado pelo Chrome (o HTML servido não tem títulos)"
    for h in heads:
        if h not in bag.copy["headlines"] and len(bag.copy["headlines"]) < 5:
            bag.copy["headlines"].append(h)


def _svg_ok(raw: str) -> bool:
    return len(raw) > 200 and bool(re.search(r"<(path|polygon|rect|circle|g)\b", raw)) and not (re.search(r"<use\b", raw) and "<path" not in raw)


def _walk_json(node):
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk_json(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_json(v)


# ---------- repositório ----------
CSS_EXT = {".css", ".scss", ".pcss", ".postcss", ".less"}
CODE_EXT = {".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue", ".svelte", ".astro", ".html"}
IMG_EXT = {".svg", ".png", ".ico", ".jpg", ".jpeg", ".webp"}
CLASS_RE = re.compile(r"(?<![\w-])(bg|text|border|ring|fill|stroke|from|via|to|decoration|outline|divide|shadow)-(\[#[0-9a-fA-F]{3,8}\]|[a-z][a-z0-9]*(?:-[a-z0-9]+)*)")


def walk_repo(root: pathlib.Path):
    count = 0
    for dirpath, dirs, files in os.walk(root, followlinks=False):
        rel_depth = len(pathlib.Path(dirpath).relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".next") and not (d.startswith(".") and d not in (".storybook",)))
        if rel_depth >= 9:
            dirs[:] = []
        for f in sorted(files):
            count += 1
            if count > 40000:
                return
            yield pathlib.Path(dirpath) / f


def resolve_package_css(root: pathlib.Path, spec: str):
    """`@escopo/pacote/arquivo.css` -> arquivo de um pacote do mesmo workspace. "terceiro" para dependência instalada, None se não achou."""
    parts = spec.split("/")
    n = 2 if spec.startswith("@") else 1
    if len(parts) < n:
        return None
    name, sub = "/".join(parts[:n]), "/".join(parts[n:])
    pkg_dir, top = None, root
    for d in [root, *root.parents][:8]:
        cand = d / "node_modules" / name
        if cand.exists() and pkg_dir is None:
            real = cand.resolve()
            if "node_modules" in real.parts:
                return "terceiro"
            pkg_dir = real
        if (d / "pnpm-workspace.yaml").is_file() or (d / "turbo.json").is_file() or '"workspaces"' in read_text(d / "package.json", 200_000):
            top = d
            break
    if pkg_dir is None and top != root:
        for dirpath, dirs, files in os.walk(top, followlinks=False):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
            if len(pathlib.Path(dirpath).relative_to(top).parts) >= 3:
                dirs[:] = []
            if "package.json" in files and f'"name": "{name}"' in read_text(pathlib.Path(dirpath) / "package.json", 200_000):
                pkg_dir = pathlib.Path(dirpath)
                break
    if pkg_dir is None:
        return None
    targets = [sub] if sub else []
    try:
        exports = json.loads(read_text(pkg_dir / "package.json", 200_000) or "{}").get("exports")
    except ValueError:
        exports = None
    if isinstance(exports, dict):
        e = exports.get("./" + sub if sub else ".")
        if isinstance(e, dict):
            e = e.get("style") or e.get("default") or e.get("import")
        if isinstance(e, str):
            targets.insert(0, e)
    for t in targets:
        for c in (pkg_dir / t, pkg_dir / (t + ".css"), pkg_dir / "src" / t):
            if c.is_file() and c.suffix.lower() in CSS_EXT and pkg_dir in c.resolve().parents:
                return c.resolve()
    return None


def read_text(p: pathlib.Path, limit: int = 2_000_000) -> str:
    try:
        if p.is_symlink() or p.stat().st_size > limit:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def from_repo(bag: Bag, root: pathlib.Path):
    root = root.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"--repo: pasta não encontrada: {root}")
    log(f"lendo {root} (somente leitura)")
    bag.sources.append(f"{root} ({dt.date.today().isoformat()})")
    rel = lambda p: str(p.relative_to(root)) if p.is_relative_to(root) else os.path.relpath(p, root)
    files = list(walk_repo(root))
    pkg_name = None
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(read_text(pkg))
            pkg_name = data.get("name")
            if pkg_name:
                bag.names.append((3, pkg_name, f"name em {root.name}/package.json"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for d in deps:
                m = re.fullmatch(r"@fontsource(?:-variable)?/([\w-]+)", d)
                if m:
                    bag.loaded_fonts.append((m.group(1).replace("-", " ").title(), f"dependência {d} (nome deduzido do pacote)"))
        except ValueError:
            bag.warn(f"package.json ilegível em {root}")
    hint = re.sub(r"^@[^/]+/", "", pkg_name or root.name)

    css_files = [p for p in files if p.suffix.lower() in CSS_EXT]
    prio = lambda p: (0 if re.search(r"global|app|index|main|token|theme|variable|base|style", p.stem, re.I) else 1, len(p.parts), str(p))
    seen_css = set()

    def add_css_file(p: pathlib.Path, depth: int = 0):
        p = p.resolve()
        if p in seen_css or len(seen_css) > 400:
            return
        seen_css.add(p)
        text = read_text(p)
        if not text:
            return
        for imp in collect_css_imports(text):
            if "fonts.googleapis.com" in imp:
                for f in google_families(imp):
                    bag.loaded_fonts.append((f, f"@import do Google Fonts em {rel(p)}"))
            elif imp.startswith("."):
                target = (p.parent / imp).resolve()
                cands = [target, target.with_suffix(".css"), target.parent / f"_{target.name}.scss"]
                hit = next((c for c in cands if c.is_file()), None)
                if hit and depth < 6:
                    add_css_file(hit, depth + 1)
            elif not re.match(r"https?:|//|tailwindcss|tw-animate|@tailwind", imp):
                hit = resolve_package_css(root, imp)
                if isinstance(hit, pathlib.Path) and depth < 6:
                    log(f"seguindo {imp} em {hit}")
                    add_css_file(hit, depth + 1)
                elif hit is None and re.match(r"@[\w.-]+/[\w.-]+|[\w.-]+/", imp):
                    bag.warn(f"{rel(p)} importa {imp}, que não foi encontrado no workspace: se os tokens da marca estão lá, passe também --repo na pasta desse pacote")
        bag.sheet.add_css(text, rel(p))

    for p in sorted(css_files, key=prio):
        add_css_file(p)

    # tailwind.config e objetos de tema
    for p in files:
        low = p.name.lower()
        if p.suffix.lower() not in (".ts", ".js", ".mjs", ".cjs", ".tsx", ".jsx"):
            continue
        is_tw = low.startswith("tailwind.config.") or low.startswith("tailwind.preset")
        is_theme = bool(re.fullmatch(r"(theme|tokens|colors|colours|palette|brand|design-tokens|cores|tema)(\.config)?\.(ts|js|mjs|cjs|tsx|jsx)", low))
        if not (is_tw or is_theme):
            continue
        text = read_text(p, 600_000)
        if not text:
            continue
        if is_tw:
            for m in re.finditer(r"\bcolors\s*:\s*\{", text):
                obj, _ = parse_js_value(text, m.end() - 1)
                for name, val in flatten(obj):
                    if "(" in val and "var(" not in val and parse_color(val) is None:
                        continue
                    scope = "dark" if re.search(r"(?:^|-)dark(?:-|$)", name) else "base"
                    bag.sheet.extra.append((f"tw:{name}", val, f"colors.{name} em {rel(p)}", scope))
                    bag.sheet.extra.append((name, val, f"colors.{name} em {rel(p)}", scope))
                    wm = re.match(r"(rgba?|hsla?|oklch)\(\s*var\(\s*(--[\w-]+)", val)
                    if wm:
                        bag.sheet.wrap.setdefault(wm.group(2), wm.group(1))
            for m in re.finditer(r"\bfontFamily\s*:\s*\{", text):
                obj, _ = parse_js_value(text, m.end() - 1)
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        fams = [x for x in v if isinstance(x, str)] if isinstance(v, list) else ([v] if isinstance(v, str) else [])
                        if fams:
                            bag.sheet.tw_fonts.setdefault(k.lower(), (fams, f"fontFamily.{k} em {rel(p)}"))
        else:
            for m in re.finditer(r"(?:(?:const|let|var)\s+(\w+)[^=\n]*=|export\s+default)\s*(?:[\w.]+\(\s*)?\{", text):
                obj, _ = parse_js_value(text, m.end() - 1)
                for name, val in flatten(obj, m.group(1) or ""):
                    if parse_color(val) is not None:
                        scope = "dark" if re.search(r"(?:^|-)dark(?:-|$)", name.lower()) else "base"
                        bag.sheet.extra.append((name, val, f"{name} em {rel(p)}", scope))

    # fontes, layout, nome, texto e uso de classes
    layouts = []
    for p in files:
        ext = p.suffix.lower()
        if ext not in CODE_EXT:
            continue
        text = read_text(p, 800_000)
        if not text:
            continue
        for util, name in CLASS_RE.findall(text):
            bag.class_use[(util, name)] = bag.class_use.get((util, name), 0) + 1
        if "next/font" in text or "geist/font" in text:
            _next_fonts(bag, text, rel(p))
        for m in re.finditer(r"https://fonts\.googleapis\.com/css2?\?[^\"'\s)>]+", text):
            for f in google_families(m.group(0)):
                bag.loaded_fonts.append((f, f"Google Fonts em {rel(p)}"))
        for m in re.finditer(r"[\"']@fontsource(?:-variable)?/([\w-]+)", text):
            bag.loaded_fonts.append((m.group(1).replace("-", " ").title(), f"import @fontsource em {rel(p)} (nome deduzido do pacote)"))
        if re.fullmatch(r"(layout|_app|_document|root|app)\.(tsx|jsx|js|ts)|\+layout\.svelte|index\.html|app\.html", p.name, re.I):
            layouts.append((len(p.parts), p, text))
        if (ext in (".vue", ".svelte", ".astro") or (p.name == "index.html" and len(p.relative_to(root).parts) <= 2 and "public" not in p.parts)) and "<style" in text:
            for n, m in enumerate(re.finditer(r"<style[^>]*>(.*?)</style>", text, re.S)):
                if n < 3 and len(bag.sheet.rules) < 60000:
                    bag.sheet.add_css(m.group(1), rel(p))
    layouts.sort(key=lambda t: (t[0], str(t[1])))
    for _d, p, text in layouts[:4]:
        r_ = rel(p)
        for key, prio_ in (("applicationName", 8), ("siteName", 7)):
            m = re.search(key + r"\s*:\s*([\"'`])(.+?)\1", text)
            if m:
                bag.names.append((prio_, m.group(2), f"{key} em {r_}"))
        t = re.search(r"<title>([^<{]+)</title>", text) or re.search(r"\btitle\s*:\s*(?:\{\s*(?:template\s*:[^,]+,\s*)?default\s*:\s*)?([\"'`])(.+?)\1", text, re.S)
        if t:
            title = " ".join(t.group(t.lastindex).split())
            bag.copy["title"] = bag.copy["title"] or title
            seg = name_from_title(title, hint)
            if seg:
                bag.names.append((5, seg, f"trecho do título em {r_} que casa com {hint}"))
        d = re.search(r"<meta\s+name=[\"']description[\"']\s+content=[\"']([^\"']+)", text)
        dj = None if d else re.search(r"\bdescription\s*:\s*((?:\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`|[\s+])+)", text)
        if not bag.copy["description"]:
            if d:
                bag.copy["description"] = d.group(1)
            elif dj:
                parts = re.findall(r"\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`", dj.group(1))
                bag.copy["description"] = " ".join("".join(a or b or c for a, b, c in parts).split()) or None
        hm = re.search(r"<html[^>]*", text)
        if hm and re.search(r"class(?:Name)?=[\"'{`][^>]*\bdark\b", hm.group(0)):
            bag.theme_hints.append(("dark", f"classe dark em <html> ({r_})"))
        m = re.search(r"defaultTheme=[\"'{]+(dark|light)", text)
        if m:
            bag.theme_hints.append((m.group(1), f'defaultTheme="{m.group(1)}" em {r_}'))
        for bm in re.finditer(r"<(?:body|html)\b[^>]*?class(?:Name)?=(\{[^>]*?\}|\"[^\"]*\"|'[^']*')", text, re.S):
            blob = bm.group(1)
            for cls in re.findall(r"(?<![\w.$-])(?:bg|text|font)-[\w\[\]#/-]+", blob):
                bag.body_classes.append((cls, r_))
            for var in re.findall(r"\b(\w+)\.className\b", blob):
                bag.body_classes.append((f"@font:{var}", r_))
    for p in files:
        if p.name in ("manifest.json", "manifest.webmanifest", "site.webmanifest") and "public" in p.parts or p.name == "manifest.ts":
            text = read_text(p, 200_000)
            m = re.search(r"[\"']?\bname[\"']?\s*:\s*[\"']([^\"']+)[\"']", text)
            if m:
                bag.names.append((9, m.group(1), f"name em {rel(p)}"))
            m = re.search(r"[\"']?theme_color[\"']?\s*:\s*[\"']([^\"']+)[\"']", text)
            c = m and parse_color(m.group(1))
            if c:
                bag.theme_color.append((c, f"theme_color em {rel(p)}"))

    # chamadas literais no código: só da página inicial e de componentes de landing, h1 e h2 com texto puro
    def page_rank(q: pathlib.Path):
        r_ = "/".join(q.relative_to(root).parts).lower()
        if re.search(r"error|erro|not-found|offline|cookie|privac|termos|terms|politica|login|entrar|auth|admin|painel|dashboard|test|spec|stories|email", r_):
            return None
        if re.search(r"hero|landing|(^|/)home|marketing|\(site\)|(^|/)site/", r_):
            return 0
        if re.fullmatch(r"(src/)?(app/(\([\w-]+\)/)?page|pages/index|routes/\+page|routes/index|app)\.\w+|index\.html|src/app\.\w+", r_):
            return 1
        return None

    heads = []
    ranked_pages = sorted(((page_rank(q), len(q.parts), str(q), q) for q in files if q.suffix.lower() in (".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro") and page_rank(q) is not None))
    for _r, _l, _s, q in ranked_pages[:60]:
        if len(heads) >= 5:
            break
        for m in re.finditer(r"<h[12]\b[^>]*>\s*([^<>{}]{6,160}?)\s*</h[12]>", read_text(q, 400_000)):
            txt = " ".join(m.group(1).split())
            if txt not in heads and len(heads) < 5:
                heads.append(txt)
    for h in heads:
        if h not in bag.copy["headlines"] and len(bag.copy["headlines"]) < 5:
            bag.copy["headlines"].append(h)

    # logos e ícones
    cands = []
    for p in files:
        if p.suffix.lower() not in IMG_EXT:
            continue
        parts = [x.lower() for x in p.relative_to(root).parts]
        if not ({"public", "static", "assets", "app", "images", "img", "brand", "marca"} & set(parts[:-1])):
            continue
        stem = p.stem.lower()
        score = 0
        if re.search(r"logo|logotipo|wordmark|brand|marca", stem) or (parts[-2:-1] and re.search(r"logo|brand|marca", parts[-2])):
            score = 30
        elif re.fullmatch(r"icon|icone|app-icon|favicon|apple-touch-icon|apple-icon|icone?-\d+|icon-\d+(x\d+)?|android-chrome-\d+x\d+", stem):
            score = 10
        if not score or re.search(r"vercel|next|nextjs|vite|react|globe|window|file|placeholder", stem):
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > MAX_IMG or size == 0:
            continue
        score += (6 if p.suffix.lower() == ".svg" else 3 if p.suffix.lower() == ".png" else 0) - len(parts) - (4 if re.search(r"white|branco|dark|mono|maskable|small|mini", stem) else 0)
        nums = [int(x) for x in re.findall(r"\d{2,4}", stem)]
        score += min(3, max(nums) / 256) if nums else 0
        cands.append((score, p))
    cands.sort(key=lambda t: (-t[0], str(t[1])))
    others = [rel(p) for score, p in cands if score >= 20][1:7]
    if others:
        bag.logo_alternatives += others
    for score, p in cands[:1]:
        if score >= 20:
            dest = "logo" + p.suffix.lower()
            bag.logos.append((int(score), bag.save(dest, p.read_bytes()), f"{rel(p)} no repositório"))
    for score, p in [c for c in cands if c[0] < 20][:1]:
        bag.icons.append((bag.save("icon" + p.suffix.lower(), p.read_bytes()), f"{rel(p)} no repositório"))
    log(f"repositório: {len(seen_css)} arquivos CSS, {len(bag.sheet.rules)} regras, {len(bag.sheet.extra)} tokens de config, {len(cands)} imagens candidatas a logo")


def _next_fonts(bag: Bag, text: str, where: str):
    imported = {}
    for m in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*[\"']next/font/google[\"']", text):
        for part in m.group(1).split(","):
            name, _, alias = part.strip().partition(" as ")
            if name.strip():
                imported[(alias or name).strip()] = name.strip().replace("_", " ")
    for m in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*[\"']geist/font/(sans|mono)[\"']", text):
        fam = "Geist" if m.group(2) == "sans" else "Geist Mono"
        for part in m.group(1).split(","):
            ident = part.strip().split(" as ")[-1].strip()
            if ident:
                bag.loaded_fonts.append((fam, f"geist/font em {where}"))
                bag.font_vars.setdefault(f"--font-geist-{m.group(2)}", (fam, f"geist/font em {where}"))
                bag.font_vars[f"@ident:{ident}"] = (fam, f"geist/font em {where}")
    for m in re.finditer(r"(?:const|let|var)\s+(\w+)\s*=\s*(\w+)\(\s*\{", text):
        ident, fn = m.group(1), m.group(2)
        obj, _ = parse_js_value(text, m.end() - 1)
        if not isinstance(obj, dict):
            continue
        if fn in imported:
            fam, src = imported[fn], f"next/font/google em {where}"
        elif re.search(r"import\s+" + re.escape(fn) + r"\s+from\s*[\"']next/font/local[\"']", text):
            srcv = obj.get("src")
            if isinstance(srcv, list):
                srcv = next((x.get("path") for x in srcv if isinstance(x, dict) and isinstance(x.get("path"), str)), None)
            if not isinstance(srcv, str):
                continue
            stem = pathlib.PurePosixPath(srcv).stem
            fam = re.sub(r"[-_ ]?(VF|Variable|Var|Regular|Bold|Medium|Italic|\[.*\])$", "", stem, flags=re.I).replace("_", " ").strip() or stem
            src = f"next/font/local em {where} (nome deduzido do arquivo {pathlib.PurePosixPath(srcv).name})"
        else:
            continue
        bag.loaded_fonts.append((fam, src))
        bag.font_vars[f"@ident:{ident}"] = (fam, src)
        if isinstance(obj.get("variable"), str):
            bag.font_vars[obj["variable"]] = (fam, src)


def from_screens(bag: Bag, folder: pathlib.Path):
    folder = folder.expanduser().resolve()
    paths = [folder] if folder.is_file() else sorted(p for p in folder.glob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")) if folder.is_dir() else []
    if not paths:
        sys.exit(f"--screens: nenhuma imagem png, jpg ou webp em {folder}")
    bag.sources.append(f"{folder} ({len(paths)} imagens, {dt.date.today().isoformat()})")
    for p in paths[:24]:
        try:
            bag.pixels.add(p, p.name)
        except Exception as e:
            bag.warn(f"imagem ilegível: {p.name} ({type(e).__name__})")
    log(f"imagens: {len(bag.pixels.files)} lidas")


# ---------- decisão ----------
def google_font_status(fams: list[str]) -> dict | None:
    """Por família: True se existe em @remotion/google-fonts, o nome que existe (Inter para Inter Variable), ou False."""
    here = pathlib.Path.cwd().resolve()
    for d in [here, *here.parents]:
        base = d / "node_modules" / "@remotion" / "google-fonts" / "dist"
        if base.is_dir():
            has = lambda f: any((base / sub / f"{re.sub(r'[^A-Za-z0-9]', '', f)}{ext}").is_file() for sub, ext in (("cjs", ".js"), ("esm", ".mjs")))
            out = {}
            for f in fams:
                alt = re.sub(r"[\s-]*(Variable|Var|VF)$", "", f, flags=re.I).strip()
                out[f] = True if has(f) else (alt if alt and alt != f and has(alt) else False)
            return out
    return None


def decide(bag: Bag) -> dict:
    sh, px = bag.sheet, bag.pixels
    ev: dict = {}
    missing: list[str] = []
    ranked = px.ranked()
    for var, (fam, src) in bag.font_vars.items():
        if var.startswith("--") and not sh.lookup(var, "base"):
            sh.vars["base"]["root"][var] = (f'"{fam}"', src)

    # --- temas
    def body_colors(theme: str):
        bg = ink = None
        for r in sh.rules:
            if r.sel.startswith("@") or "@keyframes" in r.sel:
                continue
            sc = rule_scope(r.sel, r.ctx)
            if sc != theme:
                continue
            if not any(_core(p) in ROOTISH - {"*"} for p in r.sel.split(",")):
                continue
            for p, v in r.decls:
                if p in ("background", "background-color"):
                    cs = [c for c in (find_colors(sh.resolve(v, theme) or "", theme == "dark")) if c[3] >= 0.9]
                    if cs:
                        bg = (cs[0], f"`{p}` de `{r.sel[:50]}` ({r.origin})")
                elif p == "color":
                    c = sh.color(v, theme)
                    if c and c[3] >= 0.6:
                        ink = (c, f"`color` de `{r.sel[:50]}` ({r.origin})")
                elif p == "@apply":
                    for cls in v.split():
                        m = re.fullmatch(r"(bg|text)-([\w\[\]#/-]+)", cls)
                        c = m and sh.class_color(m.group(2), theme)
                        if c and m.group(1) == "bg":
                            bg = (c, f"`@apply {cls}` em `{r.sel[:50]}` ({r.origin})")
                        elif c:
                            ink = (c, f"`@apply {cls}` em `{r.sel[:50]}` ({r.origin})")
        return bg, ink

    themes = {}
    for theme in ("base", "dark", "light"):
        bg, ink = body_colors(theme)
        if theme == "base":
            for cls, where in bag.body_classes:
                m = re.fullmatch(r"(bg|text)-([\w\[\]#/-]+)", cls)
                c = m and sh.class_color(m.group(2), "base")
                if c and m.group(1) == "bg" and not bg:
                    bg = (c, f"classe `{cls}` em <body> ({where})")
                elif c and m.group(1) == "text" and not ink:
                    ink = (c, f"classe `{cls}` em <body> ({where})")
        has_scope = theme == "base" or bool(sh.vars[theme]["root"] or sh.vars[theme]["other"]) or bg or ink
        if not has_scope:
            continue
        if not bg or (theme != "base" and bg and themes.get("base", {}).get("bg") and bg[0] == themes["base"]["bg"][0]):
            hit = sh.by_names(theme, BG_NAMES, root_only=True)
            if hit and hit[0][3] >= 0.9:
                bg = bg if (bg and theme == "base") else hit
        if not ink or (theme != "base" and themes.get("base", {}).get("ink") and ink[0] == themes["base"]["ink"][0]):
            hit = sh.by_names(theme, INK_NAMES, root_only=True)
            if hit:
                ink = ink if (ink and theme == "base") else hit
        if theme != "base":
            b = themes.get("base", {})
            if (not bg or (b.get("bg") and bg[0][:3] == b["bg"][0][:3])) and (not ink or (b.get("ink") and ink[0][:3] == b["ink"][0][:3])):
                continue
        themes[theme] = {"bg": bg, "ink": ink}

    def tone(t):
        return None if not t.get("bg") else ("escuro" if luminance(t["bg"][0]) < 0.2 else "claro")

    chosen, why = "base", "valores sem escopo de tema (o padrão do CSS)"
    dom = ranked[0][0] if ranked else None
    if dom and any(t.get("bg") for t in themes.values()):
        best = min((k for k in themes if themes[k].get("bg")), key=lambda k: dist(themes[k]["bg"][0], dom))
        d = dist(themes[best]["bg"][0], dom)
        if d <= 60:
            chosen, why = best, f"o fundo desse tema é o mais próximo da cor dominante do screenshot ({hexof(dom)})"
        else:
            hint = "dark" if luminance(dom) < 0.2 else "light"
            alt = [k for k in themes if tone(themes[k]) == ("escuro" if hint == "dark" else "claro")]
            if alt:
                chosen, why = alt[0], f"o screenshot é {'escuro' if hint == 'dark' else 'claro'} ({hexof(dom)})"
    elif not bag.theme_hints and not themes.get("base", {}).get("bg") and themes.get("light", {}).get("bg"):
        chosen, why = "light", "o CSS só declara fundo dentro de escopos de tema e o HTML não diz qual vale; adotado o escopo light, que é o padrão do navegador"
        bag.warn("tema padrão não confirmado: sem screenshot e sem tema declarado no HTML, ficou o escopo light do CSS")
    elif bag.theme_hints:
        want = bag.theme_hints[0][0]
        if want in themes:
            chosen, why = want, bag.theme_hints[0][1]
        elif want == "dark" and tone(themes.get("base", {})) == "escuro":
            why = bag.theme_hints[0][1]
    dark = chosen == "dark"
    if len([t for t in themes.values() if t.get("bg")]) > 1 or len(themes) > 1:
        ev["themes"] = {("padrão do CSS" if k == "base" else ("escopo dark" if k == "dark" else "escopo light")):
                        {"bg": t["bg"] and hexof(t["bg"][0]), "ink": t["ink"] and hexof(t["ink"][0]), "tom": tone(t)} for k, t in themes.items()}
        ev["themes"]["escolhido"] = {"base": "padrão do CSS", "dark": "escopo dark", "light": "escopo light"}[chosen]
        ev["themes"]["motivo"] = why
    T = themes.get(chosen, {"bg": None, "ink": None})

    # --- bg
    colors: dict[str, str | None] = dict.fromkeys(("bg", "ink", "accent", "muted", "line", "second"))
    bg = None
    if dom:
        bg = dom
        ev["bg"] = f"cor dominante do screenshot ({pt(px.share(bg, 10) * 100)}% dos pixels)"
        css_bg = T.get("bg")
        if css_bg and dist(css_bg[0], bg) <= 12:
            bg = css_bg[0][:3]
            ev["bg"] += f"; confere com {css_bg[1]}"
        elif css_bg:
            ev["bg"] += f"; o CSS declara {hexof(css_bg[0])} em {css_bg[1]}, que não é o que domina a tela"
            bag.warn(f"bg: o CSS declara {hexof(css_bg[0])} para a página, mas o screenshot é dominado por {hexof(bg)}; ficou o que aparece na tela")
    elif T.get("bg"):
        bg = T["bg"][0][:3]
        ev["bg"] = T["bg"][1] + " (sem screenshot para confirmar)"
    if bg:
        colors["bg"] = hexof(bg)

    # --- ink
    ink = None
    css_ink = T.get("ink")
    if bg and css_ink and contrast(over(css_ink[0], bg), bg) >= 4.5:
        ink = over(css_ink[0], bg)
        ev["ink"] = css_ink[1]
        if css_ink[0][3] < 1:
            ev["ink"] += f"; tem alfa {pt(css_ink[0][3], 2)} e foi composta sobre bg"
        if ranked:
            s = px.share(ink, 24)
            ev["ink"] += f"; {pt(s * 100, 2)}% dos pixels do screenshot" if s > 0 else "; não aparece como cor chapada no screenshot"
    elif bg and ranked:
        pool = [(c, s) for c, s in ranked if s >= 0.0015 and contrast(c, bg) >= 4.5]
        neutral = [(c, s) for c, s in pool if lch(c)[1] < 0.06]
        pick = (neutral or pool)
        if pick:
            ink = max(pick, key=lambda t: t[1] * (1 + contrast(t[0], bg) / 21))[0]
            ev["ink"] = f"cor de alto contraste mais frequente no screenshot ({pt(px.share(ink, 10) * 100, 2)}% dos pixels)"
            if css_ink:
                ev["ink"] += f"; o CSS declara {hexof(css_ink[0])} em {css_ink[1]}, com contraste {pt(contrast(over(css_ink[0], bg), bg))} contra o bg da tela"
    elif css_ink and bg:
        ink = over(css_ink[0], bg)
        ev["ink"] = css_ink[1]
    elif css_ink:
        ink = css_ink[0][:3]
        ev["ink"] = css_ink[1]
    if ink:
        colors["ink"] = hexof(ink)

    # --- uso de cor: acento, muted, line
    score: dict[str, float] = {}
    why_acc: dict[str, list[str]] = {}
    rgb_of: dict[str, tuple] = {}
    text_use: dict[tuple, float] = {}
    border_use: dict[tuple, float] = {}
    named_best: dict[str, float] = {}

    def credit(c, pts: float, reason: str | None):
        h = hexof(c)
        rgb_of[h] = c[:3]
        score[h] = score.get(h, 0) + pts
        if reason and len(why_acc.setdefault(h, [])) < 4 and reason not in why_acc[h]:
            why_acc[h].append(reason)

    for name, c, origin in sh.tokens(chosen):
        if c[3] < 0.5 or NEG_NAME.search(name):
            continue
        w = 0.0
        if not ACCENT_EXCL.search(name):
            w = 8 if name in ACCENT_EXACT else 6 if ACCENT_SHADE.match(name) else 2 if ACCENT_PART.search(name) else 0
        if w:
            h = hexof(c)
            rgb_of[h] = c[:3]
            if w > named_best.get(h, 0):
                score[h] = score.get(h, 0) + w - named_best.get(h, 0)
                named_best[h] = w
            if len(why_acc.setdefault(h, [])) < 4:
                why_acc[h].append(origin)
    n_pos: dict[str, int] = {}
    for r in sh.rules:
        if r.sel.startswith("@") or "@keyframes" in r.sel or r.sel.startswith("@font-face"):
            continue
        sc = rule_scope(r.sel, r.ctx)
        if sc != "base" and sc != chosen:
            continue
        neg = bool(NEG_SEL.search(r.sel))
        pos = (not neg) and bool(POS_SEL.search(r.sel))
        for p, v in r.decls:
            is_border = p.startswith("border") and not p.endswith(("radius", "width", "style", "collapse", "spacing"))
            if p not in COLOR_PROPS and not is_border:
                continue
            res = sh.resolve(v, chosen)
            if not res or len(res) > 600:
                continue
            for c in find_colors(res, dark):
                if c[3] <= 0.02:
                    continue
                if p == "color" and not neg:
                    text_use[c] = text_use.get(c, 0) + 1
                if is_border and not neg:
                    border_use[c] = border_use.get(c, 0) + 1
                if c[3] < 0.5 or neg:
                    continue
                if pos:
                    credit(c, 3 if p.startswith("background") else 2 if p == "color" else 1.5, None)
                    n_pos[hexof(c)] = n_pos.get(hexof(c), 0) + 1
                else:
                    credit(c, 0.25, None)
    class_hits: dict[str, int] = {}
    for (util, name), n in bag.class_use.items():
        c = sh.class_color(name, chosen)
        if not c:
            continue
        if util == "text":
            text_use[c] = text_use.get(c, 0) + n
        elif util in ("border", "divide"):
            border_use[c] = border_use.get(c, 0) + n
        if c[3] >= 0.5 and not NEG_NAME.search(name) and util in ("bg", "text", "border", "ring", "fill", "stroke", "from", "to", "via"):
            class_hits[hexof(c)] = class_hits.get(hexof(c), 0) + n
            rgb_of[hexof(c)] = c[:3]
    for h, n in class_hits.items():
        score[h] = score.get(h, 0) + min(8.0, n * 0.1)
        why_acc.setdefault(h, []).append(f"{n} usos em classes utilitárias no código")
    for h, n in n_pos.items():
        why_acc.setdefault(h, []).append(f"{n} declarações em seletores de botão, link ou destaque")
    for c, origin in bag.theme_color:
        if saturated(c):
            credit(c, 2, origin)

    cand = []
    for h, s in score.items():
        c = rgb_of[h]
        if not saturated(c) or (bg and dist(c, bg) < 30):
            continue
        pshare = px.share(c, 18) if ranked else None
        final = s * (1 + min(3.0, pshare * 300)) if pshare else (s * 0.5 if ranked else s)
        cand.append((final, s, pshare, h))
    cand.sort(key=lambda t: -t[0])
    pix_sat = [(c, s) for c, s in ranked if saturated(c) and s >= 0.0005 and (not bg or dist(c, bg) >= 40)]
    ev["accent_candidates"] = [{"hex": h, "pontos": round(f, 1), "pixels_pct": None if p is None else round(p * 100, 3), "de": why_acc.get(h, [])[:3]} for f, s, p, h in cand[:5]]
    accent = None
    if cand and cand[0][1] >= 3:
        f, s, pshare, h = cand[0]
        accent = rgb_of[h]
        ev["accent"] = "; ".join(why_acc.get(h, [])[:3]) or "cor saturada mais usada no CSS"
        if pshare is not None:
            ev["accent"] += f"; {pt(pshare * 100, 2)}% dos pixels do screenshot" if pshare > 0 else "; não aparece na primeira tela do screenshot"
            if pshare == 0:
                extra = f"; a cor saturada mais presente no screenshot é {hexof(pix_sat[0][0])} ({pt(pix_sat[0][1] * 100, 2)}%), que pode ser foto ou ilustração" if pix_sat else ""
                bag.warn(f"accent {h} vem do CSS mas não aparece na primeira tela do screenshot: confira se é a cor que a marca usa hoje{extra}")
    elif pix_sat and not sh.rules and not sh.extra:
        accent = pix_sat[0][0]
        ev["accent"] = f"cor saturada mais frequente nos pixels ({pt(pix_sat[0][1] * 100, 2)}%); sem CSS para confirmar que é a cor de botão ou link"
    else:
        prim = sh.by_names(chosen, ["primary", "brand", "accent"])
        if prim and not saturated(prim[0]):
            bag.warn(f"accent não definido: a variável primária da marca é neutra ({hexof(prim[0])}, {prim[1]}); a marca pode ser monocromática")
        if pix_sat:
            ev["accent"] = f"sem cor saturada com papel de botão, link ou destaque no CSS; a mais presente nos pixels é {hexof(pix_sat[0][0])} ({pt(pix_sat[0][1] * 100, 2)}%), não adotada sem confirmação"
    if accent:
        colors["accent"] = hexof(accent)

    # --- second
    second = None
    if accent:
        hit = next((h_ for h_ in (sh.by_names(chosen, [n_]) for n_ in SECOND_NAMES) if h_ and saturated(h_[0]) and hue_gap(h_[0], accent) >= 25), None)
        if hit:
            second, ev["second"] = hit[0][:3], hit[1]
        else:
            for f, s, pshare, h in cand[1:]:
                if s >= 8 and hue_gap(rgb_of[h], accent) >= 30 and (pshare is None or pshare > 0):
                    second = rgb_of[h]
                    ev["second"] = "segunda cor saturada por uso, com matiz diferente do accent: " + "; ".join(why_acc.get(h, [])[:2])
                    break
    if second:
        colors["second"] = hexof(second)

    # --- muted e line
    if bg:
        ink_c = contrast(ink, bg) if ink else 21
        hit = None
        for n in MUTED_NAMES:
            tk = sh.by_names(chosen, [n])
            if tk:
                c = over(tk[0], bg)
                if 2.0 <= contrast(c, bg) < ink_c * 0.9 and (not ink or dist(c, ink) > 12):
                    hit = (c, tk[1])
                    break
        if not hit and text_use:
            pool = {}
            for c, n in text_use.items():
                o = over(c, bg)
                if lch(o)[1] < 0.05 and 3 <= contrast(o, bg) <= ink_c * 0.75 and (not ink or dist(o, ink) > 20):
                    pool[o] = pool.get(o, 0) + n
            if pool:
                o = max(pool, key=pool.get)
                hit = (o, f"cor de texto neutra mais usada depois de ink ({int(pool[o])} usos em `color`), com contraste {pt(contrast(o, bg))} contra bg")
        if hit:
            colors["muted"], ev["muted"] = hexof(hit[0]), hit[1]
        hit = None
        for n in LINE_NAMES:
            tk = sh.by_names(chosen, [n])
            if tk:
                c = over(tk[0], bg)
                if 1.03 <= contrast(c, bg) <= 4.5:
                    hit = (c, tk[1] + (f"; alfa {pt(tk[0][3], 2)} composto sobre bg" if tk[0][3] < 1 else ""))
                    break
        if not hit and border_use:
            pool = {}
            for c, n in border_use.items():
                o = over(c, bg)
                if lch(o)[1] < 0.06 and 1.03 <= contrast(o, bg) <= 3.2:
                    pool[o] = pool.get(o, 0) + n
            if pool:
                o = max(pool, key=pool.get)
                hit = (o, f"cor de borda neutra mais usada ({int(pool[o])} usos em `border`), composta sobre bg quando tem alfa")
        if hit:
            colors["line"], ev["line"] = hexof(hit[0]), hit[1]

    # --- contraste
    ev["contrast"] = {}
    if bg and ink:
        cr = contrast(ink, bg)
        ev["contrast"]["ink_bg"] = round(cr, 2)
        if cr < 4.5:
            bag.warn(f"contraste ink/bg é {pt(cr, 2)}, abaixo de 4,5 (WCAG AA): {hexof(ink)} sobre {hexof(bg)}; as cores da marca foram mantidas")
    if bg and accent:
        cr = contrast(accent, bg)
        ev["contrast"]["accent_bg"] = round(cr, 2)
        if cr < 3:
            bag.warn(f"contraste accent/bg é {pt(cr, 2)}, abaixo de 3: {hexof(accent)} sobre {hexof(bg)}; a cor da marca foi mantida, use o accent em área grande ou sobre outra superfície")
    for k, v in colors.items():
        if v and v in CLIPPED:
            bag.warn(f"{k} {v} vem de uma cor fora do sRGB (oklch ou display-p3) e foi cortada para caber; confira contra a tela")
    missing += [f"colors.{k}" for k, v in colors.items() if v is None]

    # --- fontes
    fonts: dict[str, str | None] = {"display": None, "body": None, "mono": None}
    stacks: list[str] = []

    def fam_of(value: str, origin: str):
        v = sh.resolve(value, chosen)
        if not v:
            return None
        fams = families(v)
        real = first_real(fams)
        if not real and fams:
            stacks.append(", ".join(fams[:4]))
        return (real, origin) if real else None

    def var_font(patterns: str):
        for theme_store in (sh.vars[chosen]["root"], sh.vars["base"]["root"], sh.vars[chosen]["other"], sh.vars["base"]["other"]):
            for name, (val, origin) in theme_store.items():
                if re.fullmatch(patterns, name.lstrip("-").lower()):
                    hit = fam_of(val, origin)
                    if hit:
                        return hit
        return None

    def tw_font(keys):
        for k in keys:
            if k in sh.tw_fonts:
                hit = fam_of(", ".join(sh.tw_fonts[k][0]), sh.tw_fonts[k][1])
                if hit:
                    return hit
        return None

    def rule_font(test, most_common=False):
        tally: dict[str, list] = {}
        for r in sh.rules:
            if r.sel.startswith("@") or not test(r.sel):
                continue
            for p, v in r.decls:
                val = v if p == "font-family" else font_shorthand(sh.resolve(v, chosen) or "") if p == "font" else None
                hit = val and fam_of(val, f"`{p}` de `{r.sel[:50]}` ({r.origin})")
                if hit:
                    if not most_common:
                        return hit
                    t = tally.setdefault(hit[0], [0, hit[1]])
                    t[0] += 1
        if tally:
            k = max(tally, key=lambda x: tally[x][0])
            return k, f"{tally[k][1]} e outras {tally[k][0] - 1} regras" if tally[k][0] > 1 else tally[k][1]
        return None

    body = rule_font(lambda s: any(_core(p) in ("body", "html", ":root", "html body", "html,body") for p in s.split(",")))
    if not body:
        for cls, where in bag.body_classes:
            if cls.startswith("@font:"):
                hit = bag.font_vars.get(f"@ident:{cls[6:]}")
                if hit:
                    body = (hit[0], f"{hit[1]}, aplicada em <body> ({where})")
            elif cls.startswith("font-") and not body:
                key = cls[5:]
                body = var_font(rf"font-{re.escape(key)}") or tw_font([key])
            if body:
                break
    for r in sh.rules:
        if body:
            break
        if not r.sel.startswith("@") and any(_core(p) in ("body", "html") for p in r.sel.split(",")):
            for p, v in r.decls:
                m = p == "@apply" and re.search(r"(?<![\w-])font-(sans|serif|body|display|[a-z]+)(?![\w-])", v)
                if m:
                    body = var_font(rf"font-{m.group(1)}") or tw_font([m.group(1)])
    body = body or var_font(r"(default-font-family|(?:[a-z]+-)?fonte?-(sans|body|base|primary|text|texto|corpo|regular|family-base|family-sans|family-body|family))") or tw_font(["sans", "body"])
    if not body and not stacks:
        real = []
        for f, src in bag.loaded_fonts + [(f, f"@font-face em {o}") for f, o in sh.fontfaces]:
            if f.lower() not in SYSTEM_FONTS and not re.search(r"mono|code|icon|symbol|emoji|fallback|awesome|material", f, re.I) and f not in [x[0] for x in real]:
                real.append((f, src))
        if len(real) == 1:
            body = (real[0][0], f"única fonte de texto carregada: {real[0][1]}")
    if body:
        fonts["body"], ev["fonts.body"] = body

    display = var_font(r"fonte?-(display|heading|headings|title|titles|titulo|titulos|headline|hero|brand)|(heading|display|title)-font(-family)?") or tw_font(["display", "heading", "title", "headline"]) \
        or rule_font(lambda s: bool(HEAD_SEL.search(s)), most_common=True)
    if display and (not body or display[0] != body[0]):
        fonts["display"], ev["fonts.display"] = display
    elif body:
        fonts["display"] = body[0]
        ev["fonts.display"] = "nenhuma regra de título define outra família: os títulos herdam a fonte de body"

    mono = var_font(r"(default-mono-font-family|(?:[a-z]+-)?fonte?-(mono|code|codigo|monospace|family-mono|family-code|family-monospace))") or tw_font(["mono", "code"]) or rule_font(lambda s: bool(MONO_SEL.search(s)), most_common=True)
    if not mono:
        for f, src in bag.loaded_fonts + [(f, f"@font-face em {o}") for f, o in sh.fontfaces]:
            if re.search(r"mono|code", f, re.I) and f.lower() not in SYSTEM_FONTS:
                mono = (f, src)
                break
    if mono and mono[0] in (fonts["body"], fonts["display"]):
        ev["fonts.mono"] = f"não adotada: as regras de código apontam {mono[0]}, a mesma família de título ou texto ({mono[1]})"
    elif mono:
        fonts["mono"], ev["fonts.mono"] = mono
    missing += [f"fonts.{k}" for k, v in fonts.items() if v is None]
    if not fonts["body"] and stacks:
        bag.warn(f"fonts.body: o texto usa a pilha de fontes do sistema ({stacks[0]}), sem fonte de marca")
    declared = []
    for f, _o in bag.loaded_fonts + sh.fontfaces:
        if f and f not in declared and f.lower() not in SYSTEM_FONTS and "fallback" not in f.lower():
            declared.append(f)
    if declared:
        ev["fonts_declared"] = declared[:12]
    used = [f for f in dict.fromkeys(fonts.values()) if f]
    gf = google_font_status(used) if used else None
    if used:
        ev["fonts_google"] = gf if gf is not None else "não verificado: @remotion/google-fonts não encontrado a partir da pasta atual"
        for f, ok in (gf or {}).items():
            if isinstance(ok, str):
                bag.warn(f"a fonte {f} não existe com esse nome em @remotion/google-fonts, mas {ok} existe: use {ok} no import de src/theme.ts")
            elif not ok:
                bag.warn(f"a fonte {f} não existe em @remotion/google-fonts: carregue o arquivo com @remotion/fonts (se tiver licença) ou escolha com o usuário uma substituta")

    # --- nome, logo
    name = None
    if bag.names:
        prio, name, src = max(bag.names, key=lambda t: t[0])
        ev["name"] = src
    else:
        missing.append("name")
    logo = None
    if bag.logos:
        prio, logo, src = max(bag.logos, key=lambda t: t[0])
        ev["logo"] = src
    else:
        missing.append("logo")
        if bag.icons:
            ev["logo"] = "logo não encontrado; ícone disponível em " + ", ".join(f"{p} ({o})" for p, o in bag.icons[:2])
    if bag.logo_alternatives:
        ev["logo_alternatives"] = bag.logo_alternatives
    if pix_sat:
        ev["pixels_saturated"] = [{"hex": hexof(c), "pct": round(sh_ * 100, 2)} for c, sh_ in pix_sat[:6]]
    if ranked:
        ev["pixels"] = [{"hex": hexof(c), "pct": round(s * 100, 2)} for c, s in ranked[:8]]
        ev["screens"] = px.files
    if bag.theme_hints:
        ev["theme_hints"] = [h[1] for h in bag.theme_hints[:3]]
    ev["chrome"] = bag.chrome
    ev["copy"] = bag.copy
    if not bag.copy["title"] and not bag.copy["headlines"]:
        missing.append("copy")

    return {"name": name, "colors": colors, "fonts": fonts, "logo": logo, "source": " + ".join(bag.sources),
            "evidence": ev, "missing": missing, "warnings": bag.warnings}


ROLES = {"bg": "fundo", "ink": "texto principal", "accent": "acento: botão, link e destaque", "muted": "texto secundário",
         "line": "linhas e bordas", "second": "segunda cor de apoio"}


def write_md(brand: dict, bag: Bag) -> str:
    ev = brand["evidence"]
    L = [f"# Marca: {brand['name'] or 'nome não encontrado'}", "", f"Fonte: {brand['source']}", "",
         "Gerado por `scripts/brand.py`. Os valores abaixo saíram da fonte indicada; nada foi inventado.", "", "## Paleta", "",
         "| Papel | Hex | Uso | De onde saiu |", "|---|---|---|---|"]
    for k, role in ROLES.items():
        v = brand["colors"][k]
        L.append(f"| {k} | {'`' + v + '`' if v else 'não encontrado'} | {role} | {str(ev.get(k, '')).replace('|', '/')[:240]} |")
    c = ev.get("contrast", {})
    L.append("")
    if "ink_bg" in c:
        L.append(f"Contraste ink sobre bg: {pt(c['ink_bg'], 2)} (mínimo 4,5).")
    if "accent_bg" in c:
        L.append(f"Contraste accent sobre bg: {pt(c['accent_bg'], 2)} (mínimo 3).")
    th = ev.get("themes")
    if th:
        L += ["", "### Temas do site", ""]
        for k, t in th.items():
            if isinstance(t, dict):
                L.append(f"- {k}: bg {t['bg'] or 'não declarado'}, ink {t['ink'] or 'não declarado'}{' (' + t['tom'] + ')' if t.get('tom') else ''}")
        L.append(f"- Escolhido: {th['escolhido']}, porque {th['motivo']}.")
    if ev.get("accent_candidates"):
        L += ["", "### Candidatas a acento", ""]
        for a in ev["accent_candidates"]:
            pix = "" if a["pixels_pct"] is None else f", {pt(a['pixels_pct'], 2)}% dos pixels"
            L.append(f"- `{a['hex']}`: {pt(a['pontos'])} pontos{pix}. {'; '.join(a['de'])[:260]}")
    L += ["", "## Fontes", ""]
    for k, role in (("display", "títulos"), ("body", "texto"), ("mono", "código e números")):
        v = brand["fonts"][k]
        L.append(f"- {k} ({role}): {v or 'não encontrada'}{'. ' + str(ev.get('fonts.' + k)) if ev.get('fonts.' + k) else ''}")
    if ev.get("fonts_declared"):
        L.append(f"- Famílias carregadas pela fonte analisada: {', '.join(ev['fonts_declared'])}")
    gf = ev.get("fonts_google")
    if isinstance(gf, dict):
        L.append("- Em @remotion/google-fonts: " + ", ".join(f"{f} ({'sim' if ok is True else 'como ' + ok if ok else 'não'})" for f, ok in gf.items()))
    elif gf:
        L.append(f"- Em @remotion/google-fonts: {gf}")
    L += ["", "## Logo e arquivos", "", f"- Logo: {'`' + brand['logo'] + '`' if brand['logo'] else 'não encontrado'}{'. ' + ev['logo'] if ev.get('logo') else ''}"]
    if ev.get("logo_alternatives"):
        L.append("- Outros arquivos de marca na fonte (não copiados): " + ", ".join(f"`{x}`" for x in ev["logo_alternatives"]))
    for p, o in bag.icons:
        L.append(f"- Ícone: `{p}` ({o})")
    for rel in bag.assets_saved:
        if rel != brand["logo"] and rel not in [p for p, _ in bag.icons]:
            L.append(f"- `{rel}`")
    if not bag.shots and not bag.pixels.files:
        L.append("- Sem screenshot: a paleta não foi conferida contra pixels.")
    cp = ev["copy"]
    L += ["", "## Tom do texto", "", "Citado como está na fonte, sem reescrever.", ""]
    q = lambda t: '"' + t + '"'
    L.append(f"- Título: {q(cp['title']) if cp['title'] else 'não encontrado'}")
    L.append(f"- Descrição: {q(cp['description']) if cp['description'] else 'não encontrada'}")
    if cp["headlines"]:
        L.append("- Chamadas da página, na ordem em que aparecem:")
        L += [f'  {i}. "{h}"' for i, h in enumerate(cp["headlines"], 1)]
    else:
        L.append("- Chamadas da página: não encontradas")
    L += ["", "## Não encontrado", ""]
    L += [f"- {m}" for m in brand["missing"]] or ["- Nada: todos os campos têm evidência."]
    if brand["missing"]:
        L.append("")
        L.append("Campo não encontrado fica `null` em brand.json. Decida com o dono da marca antes de usar; não preencha por conta própria.")
    L += ["", "## Avisos", ""]
    L += [f"- {w}" for w in brand["warnings"]] or ["- Nenhum."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", help="site público da marca")
    ap.add_argument("--repo", action="append", default=[], help="pasta de um projeto local (somente leitura); pode repetir")
    ap.add_argument("--screens", help="pasta de imagens (ou uma imagem)")
    ap.add_argument("-o", "--out", default="brand", help="pasta de saída (padrão: brand/)")
    ap.add_argument("--no-screenshot", action="store_true", help="não abre o Chrome no modo --url")
    ap.add_argument("--allow-no-sandbox", action="store_true", help="se o Chrome não iniciar com sandbox, tenta de novo com --no-sandbox")
    a = ap.parse_args()
    if not (a.url or a.repo or a.screens):
        ap.error("informe ao menos uma fonte: --url, --repo ou --screens")
    out = pathlib.Path(a.out).expanduser().resolve()
    for r in a.repo:
        rp = pathlib.Path(r).expanduser().resolve()
        if out == rp or rp in out.parents:
            sys.exit("-o não pode ficar dentro do repositório analisado: a análise é somente leitura")
    out.mkdir(parents=True, exist_ok=True)
    bag = Bag(out)
    if a.url:
        from_url(bag, a.url, not a.no_screenshot, a.allow_no_sandbox)
    for r in a.repo:
        from_repo(bag, pathlib.Path(r))
    if a.screens:
        from_screens(bag, pathlib.Path(a.screens))
    brand = decide(bag)
    (out / "brand.json").write_text(json.dumps(brand, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "BRAND.md").write_text(write_md(brand, bag), encoding="utf-8")
    empty = not any(brand["colors"].values()) and not any(brand["fonts"].values())
    print(json.dumps({"brand": str(out / "brand.json"), "md": str(out / "BRAND.md"), "name": brand["name"], "colors": brand["colors"],
                      "fonts": brand["fonts"], "logo": brand["logo"], "screenshots": bag.shots, "missing": brand["missing"],
                      "warnings": brand["warnings"]}, ensure_ascii=False, indent=1))
    if empty:
        sys.exit("nenhuma cor ou fonte encontrada: confira a fonte informada; brand.json foi escrito só com os campos vazios")


if __name__ == "__main__":
    main()
