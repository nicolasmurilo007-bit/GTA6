#!/usr/bin/env python3
"""Prepara um clipe para os agentes numa só passada (rápido e sem trabalho repetido).

Faz: baixa (URL de clipe da Twitch via yt-dlp) ou copia o arquivo; mede volume; transcreve com tempo
por palavra (cache); detecta rostos em vários instantes (já em coordenadas do quadro 1080x1920 final);
gera quadros de amostra e um esqueleto do config de render. Os agentes LEEM `contexto.json` em vez
de cada um transcrever de novo.

Uso (Python do mpt, que já tem faster-whisper e OpenCV):
  PY="$(uv tool dir)/mpt/bin/python"
  "$PY" tools/gta6/prepare.py --source <URL-do-clipe|arquivo.mp4> --streamer alanzoka --run-dir runs/2026-11-18_slug

Saída em <run-dir>: contexto.json, clipe.json (config do render para os agentes preencherem),
frames/amostra_*.jpg e source/ (vídeo; fica FORA do Git).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vision  # noqa: E402
from render_clip import transcribe_words  # noqa: E402

CREDITOS = "Créditos: @{handle} (twitch.tv/{handle})"


def run(cmd):
    return subprocess.run([str(c) for c in cmd], check=True, capture_output=True, text=True)


def probe_duration(path: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).stdout)


def loudness(path: Path) -> dict:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return {"lufs": float(i[-1]) if i else None, "true_peak_db": float(p[-1]) if p else None}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--streamer", default="alanzoka")
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--source-url", default=None, help="URL de origem a registrar (quando --source é um arquivo)")
    ap.add_argument("--whisper-model", default="medium")
    ap.add_argument("--face-step", type=float, default=4.0, help="a cada quantos segundos medir o rosto")
    a = ap.parse_args()

    rd = a.run_dir.resolve()
    src_dir = rd / "source"
    (rd / "frames").mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(parents=True, exist_ok=True)
    clip = src_dir / "clip.mp4"
    if a.source.startswith("http"):
        if not clip.exists():
            r = subprocess.run(["yt-dlp", "-o", str(src_dir / "clip.%(ext)s"), a.source], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit("falha no download:\n" + r.stderr[-800:])
            found = [f for f in src_dir.glob("clip.*") if f.suffix in (".mp4", ".mkv", ".webm")]
            if found and found[0] != clip:
                found[0].rename(clip)
    elif Path(a.source).resolve() != clip.resolve():
        shutil.copy(a.source, clip)

    layouts = json.loads((HERE / "layouts.json").read_text(encoding="utf-8"))
    crop = layouts.get(a.streamer, {}).get("crop")
    dur = probe_duration(clip)

    wav = src_dir / "fala.wav"
    run(["ffmpeg", "-loglevel", "error", "-y", "-i", clip, "-vn", "-ac", "1", "-ar", "16000", wav])
    words = transcribe_words(wav, "pt", a.whisper_model)

    cfg = {"sources": {"live": {"path": "clip.mp4", **({"crop": crop} if crop else {})}}}
    src = vision.source(cfg, src_dir)
    faces = []
    t = 0.5
    while t < dur - 0.3:
        f = vision.faces_at(src, round(t, 2), src_dir)
        faces.append(f if f else {"t": round(t, 2), "sem_rosto": True})
        t += a.face_step

    # quadros de amostra no layout final (preto), 8 instantes
    for k in range(8):
        tt = round((k + 0.5) * dur / 8, 2)
        x, y, w, h = src["crop"]
        run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(tt), "-i", clip, "-frames:v", "1", "-vf",
             f"crop={w}:{h}:{x}:{y},scale=1080:{src['fg_h']}:flags=lanczos,pad=1080:1920:0:{src['bar']}:color=black,scale=360:640",
             rd / "frames" / f"amostra_{k}_{tt}.jpg"])

    handle = a.streamer.split("_")[0]  # "alanzoka_jogo" -> "alanzoka"
    ctx = {
        "id": rd.name,
        "streamer": a.streamer,
        "fonte": a.source_url or (a.source if a.source.startswith("http") else str(a.source)),
        "duracao_s": round(dur, 2),
        "recorte": crop,
        "volume": loudness(clip),
        "texto": " ".join(w["text"] for w in words),
        "palavras": words,
        "rostos": faces,
        "bloco_de_creditos": CREDITOS.format(handle=handle),
        "arquivos": {"video": "source/clip.mp4", "config_render": "clipe.json", "quadros": "frames/"},
    }
    (rd / "contexto.json").write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    skeleton = {
        "mode": "corte", "language": "pt", "background": "black",
        "hook": "", "hook_seconds": 3.5, "emphasis": [],
        "sources": cfg["sources"],
        "segments": [{"src": "live", "start": 0.0, "end": round(dur, 2)}],
        "sfx": [], "zooms": [], "freezes": [], "annotations": [],
    }
    (rd / "clipe.json").write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok: {rd}/contexto.json ({len(words)} palavras, {len(faces)} medidas de rosto, {dur:.1f}s)")


if __name__ == "__main__":
    main()
