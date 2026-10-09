#!/usr/bin/env python3
"""Decisão de voz: mede o hardware e monta as três opções da pergunta obrigatória.

  python3 scripts/voice.py                 # relatório legível + opções da pergunta
  python3 scripts/voice.py --json          # o mesmo, em JSON
  python3 scripts/voice.py --check-key     # valida ELEVENLABS_API_KEY sem gastar créditos
  python3 scripts/voice.py --bench         # mede o Kokoro nesta máquina (fator de tempo real e pico de RAM)
  python3 scripts/voice.py --audition "Primeira frase do roteiro." -o out/vozes   # uma amostra por voz

Só biblioteca padrão: roda com python3 puro em qualquer agente. A recomendação usa memória LIVRE
(VRAM livre da GPU, RAM disponível), não a nominal: um modelo que cabe no papel e estoura na prática
é o erro que este script existe para evitar.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


def load_env(path: str = ".env") -> None:
    """Lê KEY=valor de um .env na pasta atual, sem sobrescrever o ambiente."""
    f = pathlib.Path(path)
    if not f.is_file():
        return
    for line in f.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip("'\""))


MODELS = json.loads((pathlib.Path(__file__).resolve().parent.parent / "assets" / "tts-models.json").read_text(encoding="utf-8"))


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _ram_gb() -> tuple[float, float]:
    """(total, disponível) em GB."""
    sysname = platform.system()
    if sysname == "Linux":
        info = {}
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            info[k] = int(v.split()[0]) / 1048576
        return info.get("MemTotal", 0), info.get("MemAvailable", info.get("MemFree", 0))
    if sysname == "Darwin":
        total = int(_run(["sysctl", "-n", "hw.memsize"]) or 0) / 2**30
        free = 0.0
        for line in _run(["vm_stat"]).splitlines():
            if line.startswith(("Pages free", "Pages inactive", "Pages speculative")):
                free += int(line.split(":")[1].strip().rstrip(".")) * 16384 / 2**30
        return total, free or total * 0.5
    if sysname == "Windows":
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
                (n, ctypes.c_ulonglong) for n in ("ullTotalPhys", "ullAvailPhys", "a", "b", "c", "d", "e")
            ]

        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullTotalPhys / 2**30, m.ullAvailPhys / 2**30
    return 0.0, 0.0


def detect() -> dict:
    total, avail = _ram_gb()
    hw = {
        "os": platform.system(),
        "arch": platform.machine(),
        "threads": os.cpu_count() or 1,
        "ram_gb": round(total, 1),
        "ram_free_gb": round(avail, 1),
        "gpu": None,
        "vram_gb": 0.0,
        "vram_free_gb": 0.0,
        "accel": "cpu",
        "disk_free_gb": round(shutil.disk_usage(pathlib.Path.home()).free / 2**30, 1),
        "elevenlabs_key": bool(os.environ.get("ELEVENLABS_API_KEY")),
    }
    q = _run(["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"])
    if q:
        name, tot, free = [x.strip() for x in q.splitlines()[0].split(",")]
        hw.update(gpu=name, vram_gb=round(int(tot) / 1024, 1), vram_free_gb=round(int(free) / 1024, 1), accel="cuda")
    elif hw["os"] == "Darwin" and hw["arch"] == "arm64":
        # Memória unificada: a GPU usa a RAM do sistema.
        hw.update(gpu="Apple Silicon", vram_gb=hw["ram_gb"], vram_free_gb=hw["ram_free_gb"], accel="mps")
    return hw


def fits(m: dict, hw: dict) -> tuple[bool, str]:
    """Cabe com folga? Devolve (sim/não, motivo)."""
    if hw["disk_free_gb"] < m["disk_gb"] + 2:
        return False, f"precisa de {m['disk_gb']} GB de disco, há {hw['disk_free_gb']} livres"
    if m.get("accel_only") and hw["accel"] not in m["accel_only"]:
        return False, f"só roda em {'/'.join(m['accel_only'])}"
    if m["cpu_ok"] and hw["ram_free_gb"] >= m["ram_gb"] and hw["threads"] >= m.get("threads", 2):
        return True, f"CPU: pede {m['ram_gb']} GB de RAM, há {hw['ram_free_gb']} GB disponíveis"
    if hw["accel"] != "cpu" and hw["vram_free_gb"] >= m["vram_gb"]:
        return True, f"GPU: pede {m['vram_gb']} GB, há {hw['vram_free_gb']} GB livres"
    if hw["accel"] != "cpu":
        why = f"pede {m['vram_gb']} GB de VRAM, há {hw['vram_free_gb']} GB livres"
    else:
        why = "sem GPU compatível"
    if not m["cpu_ok"]:
        why += "; em CPU fica lento demais para iterar"
    else:
        why += f"; em CPU pede {m['ram_gb']} GB de RAM e {m.get('threads', 2)} threads"
    return False, why


def recommend(hw: dict, lang: str = "pt-br", commercial: bool = True) -> dict:
    ok, out = [], []
    for m in MODELS["models"]:  # a ordem do arquivo é a ordem de preferência (qualidade primeiro)
        if lang.startswith("pt") and not m["pt"]:
            out.append({"id": m["id"], "why": "sem português declarado pelo autor"})
            continue
        if commercial and not m["commercial"]:
            why = "uso comercial não confirmado" if m["commercial"] is None else "não permite uso comercial"
            out.append({"id": m["id"], "why": f"{m['license']}: {why} (--any-license inclui)"})
            continue
        good, why = fits(m, hw)
        (ok if good else out).append({**m, "why": why} if good else {"id": m["id"], "why": why})
    return {"recommended": ok[0] if ok else None, "alternative": ok[1] if len(ok) > 1 else None, "also_fit": [m["id"] for m in ok[2:]], "excluded": out}


def check_key() -> dict:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return {"ok": False, "detail": "ELEVENLABS_API_KEY não está definida neste shell"}
    req = urllib.request.Request(MODELS["elevenlabs"]["check_url"], headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:200]
        hint = "chave inválida ou revogada" if e.code == 401 else "chave sem a permissão necessária" if e.code == 403 else "erro da API"
        return {"ok": False, "detail": f"HTTP {e.code}: {hint}", "body": body}
    except OSError as e:
        return {"ok": False, "detail": f"sem rede até api.elevenlabs.io: {e}"}
    voices = j.get("voices", [])
    return {"ok": True, "detail": f"chave válida; {len(voices)} vozes na conta", "voices": [{"id": v.get("voice_id"), "name": v.get("name")} for v in voices[:8]]}


def bench() -> dict:
    """Roda o Kokoro numa frase e mede fator de tempo real e pico de RAM do processo filho."""
    import resource
    import tempfile
    import time

    here = pathlib.Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as d:
        txt = pathlib.Path(d) / "t.txt"
        txt.write_text("Este é um teste de voz para medir a velocidade desta máquina antes de narrar o vídeo.", encoding="utf-8")
        t0 = time.time()
        p = subprocess.run(["uv", "run", str(here / "tts.py"), str(txt), "-o", str(pathlib.Path(d) / "b")], capture_output=True, text=True)
        wall = time.time() - t0
        if p.returncode != 0:
            return {"ok": False, "detail": p.stderr.strip()[-300:]}
        dur = json.loads(p.stdout.strip().splitlines()[-1])["duration"]
    # ru_maxrss vem em bytes no macOS e em KB no Linux.
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / (2**30 if sys.platform == "darwin" else 2**20)
    return {"ok": True, "audio_sec": dur, "wall_sec": round(wall, 1), "rtf": round(wall / dur, 2), "peak_ram_gb": round(peak, 2), "note": "rtf inclui carregar o modelo; abaixo de 1 é mais rápido que tempo real"}


def audition(text: str, out_dir: str, lang: str) -> dict:
    """Mesma frase do roteiro em cada voz do Kokoro, para o usuário escolher ouvindo."""
    here = pathlib.Path(__file__).resolve().parent
    voices = ["pf_dora", "pm_alex", "pm_santa"] if lang.startswith("pt") else ["af_heart", "af_bella", "am_michael"]
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for v in voices:
        p = subprocess.run(["uv", "run", str(here / "tts.py"), "-", "-o", str(out / v), "--voice", v, "--lang", lang], input=text, capture_output=True, text=True)
        if p.returncode != 0:
            return {"ok": False, "detail": p.stderr.strip()[-300:]}
        files.append(str(out / f"{v}.wav"))
    return {"ok": True, "files": files}


def options(hw: dict, rec: dict) -> list[dict]:
    el = MODELS["elevenlabs"]
    local = rec["recommended"]
    alt = rec["alternative"]
    return [
        {"label": "Sem voz", "detail": "Só trilha, SFX e texto na tela. O vídeo precisa funcionar mudo: tipografia carrega a mensagem."},
        {
            "label": "Voz com ElevenLabs",
            "detail": ("Chave já definida neste shell: rode --check-key." if hw["elevenlabs_key"] else f"Precisa de chave. {el['key_steps']}")
            + f" Custo: {el['cost_note']}",
        },
        {
            "label": f"Voz local: {local['name']}" if local else "Voz local: indisponível nesta máquina",
            "detail": (
                f"{local['why']}. Licença {local['license']}. {local['note']}"
                + (f" Alternativa: {alt['name']} ({alt['note']})" if alt else "")
            )
            if local
            else "Nenhum modelo coube com folga. Use ElevenLabs ou siga sem voz.",
        },
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lang", default="pt-br")
    ap.add_argument("--any-license", action="store_true", help="inclui modelos sem licença comercial (uso pessoal)")
    ap.add_argument("--check-key", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--audition", default=None, metavar="FRASE", help="gera a frase em cada voz do Kokoro")
    ap.add_argument("-o", "--out", default="out/vozes", help="pasta das amostras do --audition")
    a = ap.parse_args()
    load_env()

    if a.check_key:
        r = check_key()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r["ok"] else 1)
    if a.bench or a.audition:
        r = audition(a.audition, a.out, a.lang) if a.audition else bench()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        sys.exit(0 if r["ok"] else 1)

    hw = detect()
    rec = recommend(hw, a.lang, commercial=not a.any_license)
    opts = options(hw, rec)
    if a.json:
        print(json.dumps({"hardware": hw, "question": MODELS["question"], "options": opts, **rec}, ensure_ascii=False, indent=1))
        return
    gpu = f"{hw['gpu']} ({hw['vram_free_gb']} de {hw['vram_gb']} GB livres)" if hw["gpu"] else "sem GPU NVIDIA ou Apple Silicon"
    print(f"Hardware: {hw['threads']} threads, RAM {hw['ram_free_gb']} de {hw['ram_gb']} GB disponíveis, {gpu}, disco {hw['disk_free_gb']} GB livres\n")
    print(f"Pergunta ao usuário: {MODELS['question']}")
    for i, o in enumerate(opts, 1):
        print(f"  {i}. {o['label']}\n     {o['detail']}")
    for key, title in (("recommended", "Recomendado"), ("alternative", "Alternativa")):
        m = rec[key]
        if m:
            how = "integrado: tts.py --provider " + m["provider"] if m.get("provider") else "fora do tts.py: gere o WAV e rode align.py"
            print(f"\n{title}: {m['name']} [{m['hf']}]\n  {how}\n  instalar: {m['install']}\n  tempos por palavra: {m['timestamps']}")
    if rec["excluded"]:
        print("\nDescartados nesta máquina:")
        for e in rec["excluded"]:
            print(f"  - {e['id']}: {e['why']}")


if __name__ == "__main__":
    main()
