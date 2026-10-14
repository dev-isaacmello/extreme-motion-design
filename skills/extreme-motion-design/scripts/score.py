#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "soundfile", "requests"]
# ///
"""Roteiro -> voz, partitura e marcas. Um arquivo (roteiro.json) decide o tempo de tudo.

  uv run scripts/score.py --dry            # mostra o que seria gerado e quantos caracteres pagos, sem gastar
  uv run scripts/score.py --yes            # gera só as frases que mudaram e escreve partitura e marcas
  uv run scripts/score.py                  # sem voz paga pendente: refaz partitura e marcas (pausas, cortes, SFX)
Rode na pasta do vídeo. Lê roteiro.json e escreve:
  public/audio/narration.wav + narration.words.json   voz montada frase a frase, tempos absolutos do vídeo
  public/timeline.json                                partitura: cenas, trilha, SFX, loudness
  public/cues.json                                    marcas nomeadas, frases, palavras e batidas para as cenas
Cada frase é gerada uma vez e guardada em public/audio/seg pelo hash do texto e da voz: mexer em pausa,
corte ou SFX não gasta crédito, e trocar uma frase regera só aquela. Formato do roteiro em references/score.md.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata

import numpy as np
import soundfile as sf

SKILL = pathlib.Path(__file__).resolve().parent
SR = 48000
FORMATS = {"youtube": (1920, 1080), "linkedin": (1920, 1080), "reels": (1080, 1920), "tiktok": (1080, 1920), "square": (1080, 1080)}
CUE = re.compile(r"^(word|phrase|beat|t|cue|scene)(?::([^#+]+?))?(?:#(\d+))?(\.end)?([+-]\d*\.?\d+)?$")


def die(msg):
    sys.exit(f"roteiro: {msg}")


def norm(w: str) -> str:
    w = unicodedata.normalize("NFKD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if not unicodedata.combining(c)))


def tokens(text: str) -> list[str]:
    return [w for w in text.split() if re.search(r"\w", w)]


def load_env():
    env = pathlib.Path(".env")
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip("'\""))


# ---------- voz, frase a frase ----------
def phrase_key(ph: dict, voice: dict) -> str:
    blob = json.dumps([ph["text"], ph.get("speak"), {k: voice.get(k) for k in ("provider", "voice", "model", "settings", "style", "speed", "lang")}, ph.get("seed", voice.get("seed", 7))], sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(blob.encode()).hexdigest()[:12]


def strip_tags(al: dict) -> dict:
    """Tira do alinhamento a marcação entre colchetes ([excited]) que os modelos v3 interpretam e não leem."""
    out, inside, skipped = {k: [] for k in al}, False, False
    for n, ch in enumerate(al["characters"]):
        if ch == "[":
            inside = True
        if not inside and not (skipped and ch.isspace()):
            for k in al:
                out[k].append(al[k][n])
        skipped = inside or (skipped and ch.isspace())
        if ch == "]":
            inside = False
    return out


def chars_to_words(al: dict) -> list[dict]:
    words, cur = [], None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            cur = None
            continue
        if cur is None:
            cur = {"word": "", "start": s, "end": e}
            words.append(cur)
        cur["word"] += ch
        cur["end"] = e
    return [w for w in words if re.search(r"\w", w["word"])]


def gen_elevenlabs(ph, prev, nxt, voice, attempt):
    import requests

    # v3 e v4 não aceitam contexto de texto vizinho nem style e speed, e às vezes soam depois do fim do texto.
    v3 = str(voice.get("model", "")).startswith(("eleven_v3", "eleven_v4"))
    body = {
        "text": (voice.get("style", "") + " " + ph.get("speak", ph["text"])).strip(),
        "model_id": voice.get("model", "eleven_multilingual_v2"),
        "voice_settings": voice.get("settings", {"stability": 0.5, "similarity_boost": 0.75}),
        "seed": ph.get("seed", voice.get("seed", 7)) + attempt,
        "apply_text_normalization": "auto",
    }
    # Contexto só em texto: dá a entonação de continuação sem colar o áudio no pedido vizinho.
    if prev and not v3:
        body["previous_text"] = prev
    if nxt and not ph.get("closed") and not v3:
        body["next_text"] = nxt
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice['voice']}/with-timestamps?output_format=pcm_48000",
        json=body, headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}, timeout=300,
    )
    if not r.ok:
        die(f"ElevenLabs HTTP {r.status_code}: {r.text[:300]}")
    j = r.json()
    pcm = np.frombuffer(base64.b64decode(j["audio_base64"]), dtype="<i2").astype(np.float32) / 32768
    al = strip_tags(j["alignment"])
    end = al["character_end_times_seconds"][-1]
    if v3 and len(pcm) / SR - end > 0.12:  # o v3 às vezes continua soando depois do texto: corta ali com fade
        pcm = pcm[: int((end + 0.12) * SR)].copy()
        n = int(0.05 * SR)
        pcm[-n:] *= np.linspace(1, 0, n) ** 2
    words = chars_to_words(al)
    loud = np.flatnonzero(np.abs(pcm) > 10 ** (-38 / 20))
    ts = [w["start"] for w in words]
    hole = max((b - a for a, b in zip(ts, ts[1:])), default=0)
    said = [norm(w["word"]) for w in words] == [norm(t) for t in tokens(ph.get("speak", ph["text"]))]
    clean = len(loud) > 0 and loud[0] / SR < 0.2 and (v3 or (len(pcm) - loud[-1]) / SR >= 0.15)
    why = None if (said and clean and hole < float(voice.get("max_gap", 0.8))) else f"falado={said} pontas_limpas={clean} buraco={hole:.2f}s"
    return pcm, words, int(r.headers.get("character-cost", 0) or 0), why


def gen_kokoro(ph, voice, tmp: pathlib.Path):
    txt = tmp.with_suffix(".txt")
    txt.write_text(ph.get("speak", ph["text"]), encoding="utf-8")
    cmd = ["uv", "run", str(SKILL / "tts.py"), str(txt), "-o", str(tmp), "--lang", voice.get("lang", "pt-br"), "--speed", str(voice.get("speed", 0.92))]
    if voice.get("voice"):
        cmd += ["--voice", voice["voice"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        die(f"tts.py falhou: {r.stderr[-400:]}")
    pcm, sr = sf.read(tmp.with_suffix(".wav"), dtype="float32")
    if sr != SR:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp.with_suffix(".wav")), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        pcm = np.frombuffer(raw, dtype="<f4").copy()
    words = json.loads(pathlib.Path(str(tmp) + ".words.json").read_text(encoding="utf-8"))["words"]
    for f in (txt, tmp.with_suffix(".wav"), pathlib.Path(str(tmp) + ".words.json")):
        f.unlink(missing_ok=True)
    return pcm, [{"word": w["word"], "start": w["start"], "end": w["end"], **({"ph": w["ph"]} if "ph" in w else {})} for w in words]


def voice_phrases(R: dict, pub: pathlib.Path, dry: bool, yes: bool) -> list[dict]:
    """Devolve as frases com áudio aparado e palavras relativas ao início do trecho."""
    voice = R.get("voice") or {"provider": "none"}
    prov = voice.get("provider", "none")
    flat = [(s, p) for s in R["scenes"] for p in s.get("say", [])]
    if prov in ("none", "file") or not flat:
        return []
    seg = pub / "audio" / "seg"
    seg.mkdir(parents=True, exist_ok=True)
    todo = [p for _, p in flat if not (seg / f"{phrase_key(p, voice)}.wav").exists()]
    chars = sum(len((voice.get("style", "") + " " + p.get("speak", p["text"])).strip()) for p in todo)
    paid = prov == "elevenlabs"
    report = {"provider": prov, "frases": len(flat), "a_gerar": len(todo), "caracteres": chars if paid else 0}
    if dry or (paid and todo and not yes):
        print(json.dumps(report, ensure_ascii=False))
        if not dry:
            die(f"{len(todo)} frases novas custam cerca de {chars} caracteres na ElevenLabs: diga o número ao usuário e rode de novo com --yes")
        sys.exit(0)
    spent, redone = 0, []
    texts = [p.get("speak", p["text"]) for _, p in flat]
    out = []
    for i, (_, p) in enumerate(flat):
        key = phrase_key(p, voice)
        wav, meta = seg / f"{key}.wav", seg / f"{key}.json"
        if not wav.exists():
            if prov == "elevenlabs":
                for attempt in range(4):
                    pcm, words, cost, why = gen_elevenlabs(p, " ".join(texts[max(0, i - 2):i]), texts[i + 1] if i + 1 < len(texts) else None, voice, attempt)
                    spent += cost
                    if not why:
                        break
                    redone.append(i)
                    print(f"frase {i} tentativa {attempt}: {why}", file=sys.stderr)
                else:
                    die(f"frase {i} ('{p['text'][:40]}'): quatro tentativas e o áudio continua vindo cortado ou diferente do texto")
            elif prov == "kokoro":
                pcm, words = gen_kokoro(p, voice, seg / f"tmp_{key}")
            else:
                die(f"provider '{prov}' não é gerado aqui: gere o WAV, rode align.py e use provider 'file'")
            sf.write(wav, pcm, SR)
            meta.write_text(json.dumps({"text": p["text"], "words": words}, ensure_ascii=False), encoding="utf-8")
        pcm, _ = sf.read(wav, dtype="float32")
        words = json.loads(meta.read_text(encoding="utf-8"))["words"]
        # Apara só o silêncio das pontas, com folga e fade: nada de fala é cortado.
        loud = np.flatnonzero(np.abs(pcm) > 10 ** (-50 / 20))
        a, b = max(0, loud[0] - int(0.03 * SR)), min(len(pcm), loud[-1] + int(0.12 * SR))
        clip = pcm[a:b].copy()
        # Nível igual entre frases: entrega expressiva varia de volume de uma frase para outra.
        rms = float(np.sqrt(np.mean(clip**2)))
        clip *= min(10 ** (-23 / 20) / max(rms, 1e-6), 10 ** (-1 / 20) / max(float(np.abs(clip).max()), 1e-6))
        n = int(0.012 * SR)
        clip[:n] *= np.linspace(0, 1, n)
        clip[-n:] *= np.linspace(1, 0, n)
        shown = tokens(p["text"])
        if len(shown) == len(words):  # "speak" ensina a pronúncia; na tela vale a grafia de "text"
            for w, t in zip(words, shown):
                w["word"] = t
        else:
            print(f"aviso: frase {i} tem {len(shown)} palavras na tela e {len(words)} faladas: os tempos seguem a fala", file=sys.stderr)
        out.append({"clip": clip, "words": [{**w, "start": max(0.0, w["start"] - a / SR), "end": max(0.0, w["end"] - a / SR)} for w in words]})
    report |= {"gasto_caracteres": spent, "frases_refeitas": sorted(set(redone))}
    print(json.dumps(report, ensure_ascii=False), file=sys.stderr)
    return out


def file_phrases(R: dict, pub: pathlib.Path) -> tuple[list[dict], float]:
    """Voz que já existe (gravada, de outro modelo ou a fala de uma filmagem): casa as frases com o words.json."""
    voice = R["voice"]
    wp = pub / voice.get("words", str(pathlib.Path(voice["file"]).with_suffix("")) + ".words.json")
    if not wp.exists():
        die(f"{wp} não existe: rode align.py no arquivo de voz (com o roteiro, ou --transcribe para ouvir a fala)")
    words = json.loads(wp.read_text(encoding="utf-8"))["words"]
    off, k, out = float(voice.get("start", 0)), 0, []
    for s in R["scenes"]:
        for p in s.get("say", []):
            want = [norm(t) for t in tokens(p["text"])]
            got = words[k:k + len(want)]
            if [norm(w["word"]) for w in got] != want:
                die(f"a frase '{p['text'][:50]}' não casa com a voz a partir da palavra {k} ({' '.join(w['word'] for w in got)[:60]})")
            for w, t in zip(got, tokens(p["text"])):
                w["word"] = t
            out.append({"fixed": off + got[0]["start"], "len": got[-1]["end"] - got[0]["start"], "words": [{**w, "start": w["start"] - got[0]["start"], "end": w["end"] - got[0]["start"]} for w in got]})
            k += len(want)
    return out, off


# ---------- partitura ----------
def build(R: dict, phrases: list[dict], beats: list[float], provider: str):
    fps = int(R.get("fps", 30))
    q = lambda t: round(round(t * fps) / fps, 4)  # noqa: E731  evento visual e SFX caem no mesmo frame
    cut = R.get("cut", {})
    lead, on_beat = float(cut.get("lead", 0.2)), cut.get("on", "phrase") == "beat"
    if on_beat and not beats:
        die("cut.on é 'beat' mas não há batidas: rode beats.py na trilha (gera <trilha>.beats.json)")
    beat_dur = float(np.median(np.diff(beats))) if len(beats) > 1 else 0.5
    last_beat = lambda t: max([b for b in beats if b <= t + 1e-6], default=t)  # noqa: E731
    next_beat = lambda t: min([b for b in beats if b >= t - 1e-6], default=t)  # noqa: E731

    voice_end = float(R.get("start", 0.3)) - 0.35  # a primeira frase começa em "start"
    floor, k, scenes, plist, words = 0.0, 0, [], [], []
    for si, s in enumerate(R["scenes"]):
        say = s.get("say", [])
        sc = {"id": s["id"], "phrases": []}
        if say:
            for j, p in enumerate(say):
                ph = phrases[k]
                k += 1
                length = ph.get("len", len(ph.get("clip", [])) / SR)
                if "fixed" in ph:
                    t = ph["fixed"]
                elif p.get("at") is not None:
                    t = float(p["at"])
                    if t < voice_end + 0.15:
                        die(f"cena {s['id']}: a frase '{p['text'][:40]}' pede at={t} mas a anterior termina em {voice_end:.2f} s")
                else:
                    t = voice_end + float(p.get("pause", 0.35))
                    if j == 0:
                        t = max(t, floor + lead)
                if "fixed" not in ph and j == 0 and si > 0 and on_beat:
                    t = next_beat(t - lead) + lead  # o corte cai na batida e a frase entra `lead` depois
                item = {"scene": s["id"], "i": j, "start": round(t, 3), "end": round(t + length, 3), "text": p["text"], "from": len(words)}
                words += [{**w, "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in ph["words"]]
                item["to"] = len(words) - 1
                ph["t"] = t
                sc["phrases"].append(item)
                plist.append(item)
                voice_end = t + length
            first = sc["phrases"][0]["start"]
            sc["start"] = 0.0 if si == 0 else q(last_beat(first - lead) if on_beat else first - lead)
            if si and "fixed" in phrases[k - 1]:
                sc["start"] = max(sc["start"], q(floor))  # fala gravada emendada: o corte fica entre as duas frases
            if si and sc["start"] < floor - 1.5 / fps:
                die(f"cena {s['id']}: a fala começa em {first:.2f} s, antes do fim da cena anterior ({floor:.2f} s)")
            if "fixed" in phrases[k - 1] and "hold" not in s:
                # O alinhador estica o fim da última palavra até a fala seguinte: só os primeiros 60% contam como fala.
                floor = words[-1]["start"] + 0.6 * (words[-1]["end"] - words[-1]["start"])
            else:
                floor = voice_end + float(s.get("hold", 0.3))
            sc["min_end"] = floor
        else:
            sc["start"] = 0.0 if si == 0 else q(floor)
            if "beats" in s:
                b0 = next_beat(sc["start"])
                idx = beats.index(b0) + int(s["beats"]) if b0 in beats else None
                end = beats[idx] if idx is not None and idx < len(beats) else sc["start"] + int(s["beats"]) * beat_dur
            elif "dur" in s:
                end = sc["start"] + float(s["dur"])
            else:
                die(f"cena {s['id']} não tem fala: dê 'dur' em segundos ou 'beats'")
            floor = sc["min_end"] = q(end)
        scenes.append(sc)
    for a, b in zip(scenes, scenes[1:]):
        if not R["scenes"][scenes.index(b)].get("say"):
            b["start"] = q(a["min_end"])
        a["end"] = b["start"]
    total = q(max(float(R.get("duration") or 0), scenes[-1]["min_end"] + (float(R.get("tail", 1.2)) if R["scenes"][-1].get("say") else 0)))
    scenes[-1]["end"] = total

    def resolve(expr, sc, ev):
        if isinstance(expr, (int, float)):
            return sc["start"] + float(expr)
        m = CUE.match(str(expr).strip())
        if not m:
            die(f"cena {sc['id']}: marca '{expr}' não é válida (word:, phrase:, beat:, scene, t:, cue:)")
        kind, arg, nth, end, off = m.group(1), m.group(2), int(m.group(3) or 1), bool(m.group(4)), float(m.group(5) or 0)
        if kind == "scene":
            t = sc["end"] if end else sc["start"]
        elif kind == "t":
            t = float(arg)
        elif kind == "cue":
            if arg not in ev:
                die(f"cena {sc['id']}: marca '{expr}' usa '{arg}', que ainda não foi definida")
            t = ev[arg]
        elif kind == "phrase":
            if not 1 <= int(arg) <= len(sc["phrases"]):
                die(f"cena {sc['id']}: '{expr}' pede a frase {arg} e a cena tem {len(sc['phrases'])}")
            p = sc["phrases"][int(arg) - 1]
            t = p["end"] if end else p["start"]
        elif kind == "beat":
            after = [b for b in beats if b >= sc["start"] - 1e-6]
            if int(arg) > len(after):
                die(f"cena {sc['id']}: '{expr}' pede a batida {arg} e só há {len(after)} depois do início da cena")
            t = after[int(arg) - 1]
        else:
            mine = [w for p in sc["phrases"] for w in words[p["from"]:p["to"] + 1]]
            hits = [w for w in mine if norm(w["word"]) == norm(arg)]
            if len(hits) < nth:
                die(f"cena {sc['id']}: '{expr}' não achou a palavra (ocorrência {nth}). Palavras da cena: {' '.join(w['word'] for w in mine)}")
            t = hits[nth - 1]["end"] if end else hits[nth - 1]["start"]
        return t + off

    ev, sfx = {}, []
    csfx = cut.get("sfx", {"type": "whoosh", "gain_db": -18, "dur": 0.5, "lead": 0.25})
    for s, sc in zip(R["scenes"], scenes):
        for name, expr in (s.get("cues") or {}).items():
            if name in ev:
                die(f"marca '{name}' definida em duas cenas: os nomes são globais")
            ev[name] = q(resolve(expr, sc, ev))
            if not sc["start"] - 0.5 <= ev[name] <= sc["end"] + 0.5:
                print(f"aviso: a marca '{name}' cai em {ev[name]:.2f} s, fora da cena {sc['id']} ({sc['start']:.2f} a {sc['end']:.2f} s)", file=sys.stderr)
        if sc is not scenes[0] and csfx and s.get("cut_sfx", True):
            sfx.append({"at": round(max(0, sc["start"] - csfx.get("lead", 0.25)), 3), **{k: v for k, v in csfx.items() if k != "lead"}})
        for e in s.get("sfx") or []:
            at = ev[e["at"]] if e["at"] in ev else q(resolve(e["at"], sc, ev))
            sfx.append({**e, "at": round(at, 3)})
    return fps, scenes, plist, words, ev, sorted(sfx, key=lambda e: e["at"]), total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roteiro", nargs="?", default="roteiro.json")
    ap.add_argument("--dry", action="store_true", help="só informa o que seria gerado e o custo")
    ap.add_argument("--yes", action="store_true", help="autoriza gastar os caracteres informados pelo --dry")
    a = ap.parse_args()
    rp = pathlib.Path(a.roteiro)
    if not rp.exists():
        die(f"{rp} não existe: copie roteiro.json do template e edite")
    R = json.loads(rp.read_text(encoding="utf-8"))
    os.chdir(rp.resolve().parent)
    load_env()
    pub = pathlib.Path("public")
    ids = [s["id"] for s in R["scenes"]]
    if len(set(ids)) != len(ids):
        die("há cenas com o mesmo id")
    voice = R.get("voice") or {"provider": "none"}
    prov = voice.get("provider", "none")
    if prov == "none" and any(s.get("say") for s in R["scenes"]):
        die("há frases em 'say' e voice.provider é 'none': escolha a voz ou tire as frases")

    music = R.get("music") or {}
    beats = []
    if music.get("file"):
        bp = pub / (str(pathlib.Path(music["file"]).with_suffix("")) + ".beats.json")
        if bp.exists():
            off = float(music.get("start", 0)) - float(music.get("offset", 0))
            beats = [round(b + off, 3) for b in json.loads(bp.read_text(encoding="utf-8"))["beats"] if b + off >= 0]

    if prov == "file":
        phrases, _ = file_phrases(R, pub)
    else:
        phrases = voice_phrases(R, pub, a.dry, a.yes)
    fps, scenes, plist, words, ev, sfx, total = build(R, phrases, beats, prov)

    nar = None
    if prov == "file":
        nar = {"file": voice["file"], "start": float(voice.get("start", 0)), "gain_db": voice.get("gain_db", 0)}
    elif phrases:
        audio = np.zeros(int((total + 0.5) * SR), np.float32)
        for ph in phrases:
            i = int(round(ph["t"] * SR))
            audio[i:i + len(ph["clip"])] += ph["clip"][: max(0, len(audio) - i)]
        (pub / "audio").mkdir(parents=True, exist_ok=True)
        sf.write(pub / "audio" / "narration.wav", audio[: int(total * SR)], SR, subtype="PCM_16")
        spoken = sum(len(p["clip"]) for p in phrases) / SR
        meta = {"text": " ".join(p["text"] for p in plist), "provider": prov, "voice": voice.get("voice"), "model": voice.get("model"),
                "duration": round(total, 3), "wpm": round(len(words) / max(spoken, 0.1) * 60), "approx": False, "absolute": True, "words": words}
        (pub / "audio" / "narration.words.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        nar = {"file": "audio/narration.wav", "start": 0, "gain_db": voice.get("gain_db", 0)}

    if "format" in R and R["format"] not in FORMATS:
        die(f"format '{R['format']}' não existe: use {', '.join(FORMATS)}")
    w, h = FORMATS[R["format"]] if "format" in R else (int(R.get("width", 1920)), int(R.get("height", 1080)))
    tl = {"fps": fps, "width": w, "height": h, "duration": total, "audio": R.get("audio", "audio/mix.wav")}
    if nar:
        tl["narration"] = nar
    if music.get("file"):
        tl["music"] = {"gain_db": -15, "duck_db": -9 if nar else 0, "fade_in": 0.3, "fade_out": 1.6, **music}
    tl["scenes"] = [{"id": s["id"], "start": s["start"], "end": s["end"]} for s in scenes]
    tl["sfx"] = sfx
    # O AAC devolve picos até 1,5 dB acima do WAV quando a voz foi muito amplificada: a folga fica no mix.
    tl["loudness"] = R.get("loudness", {"lufs": -14, "tp": -3.0})
    if R.get("budget"):
        tl["budget"] = R["budget"]
    tl = {k: v for k, v in tl.items() if v is not None}
    (pub / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    cues = {"cuts": {s["id"]: s["start"] for s in scenes}, "ev": ev, "phrases": plist,
            "words": [{"word": x["word"], "start": x["start"], "end": x["end"], **({"ph": x["ph"]} if "ph" in x else {})} for x in words],
            "beats": [b for b in beats if b <= total]}
    (pub / "cues.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
    wps = [(s["id"], round(sum(p["to"] - p["from"] + 1 for p in s["phrases"]) / max(s["end"] - s["start"], 0.1), 1)) for s in scenes if s["phrases"]]
    print(json.dumps({"duration": total, "scenes": {s["id"]: [s["start"], s["end"]] for s in scenes}, "cues": len(ev), "sfx": len(sfx),
                      "palavras_por_segundo": dict(wps)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
