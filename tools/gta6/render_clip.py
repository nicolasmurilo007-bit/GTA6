#!/usr/bin/env python3
"""Monta um corte vertical 9:16 com narração, ducking e legenda palavra por palavra.

Fluxo de um corte:
  1. recorta o trecho do vídeo-fonte;
  2. coloca o vídeo centralizado sobre um fundo desfocado (fonte pequena demais
     para recorte vertical);
  3. transcreve a narração (faster-whisper) para obter o tempo de cada palavra;
  4. gera a legenda (ASS) e, opcionalmente, legendas para falas originais mantidas;
  5. mixa a narração por cima do áudio original, que abaixa sozinho (sidechain
     compress) enquanto a narração toca, e normaliza para -14 LUFS.

Uso (rodar com o Python do `mpt`, que já tem faster-whisper):
  PY="$(uv tool dir)/mpt/bin/python"
  "$PY" tools/gta6/render_clip.py --config tools/gta6/teste1.json \
        --workdir <pasta com trailer.mp4 e audio/> --out <pasta de saída>

Os vídeos e áudios NÃO vão para o Git.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
FPS = 30
FONT_NAME = "Liberation Sans"
FONT_DIR = "/usr/share/fonts/truetype/liberation"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)


def duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    )
    return float(out)


def ass_time(t: float) -> str:
    t = max(t, 0.0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def transcribe_words(audio: Path, language: str, model_name: str) -> list[dict]:
    """Palavras com tempo (faster-whisper). Resultado em cache ao lado do áudio: re-renderizar é rápido."""
    cache = audio.with_name(f"{audio.name}.{model_name}.{language}.words.json")
    size = audio.stat().st_size
    if cache.exists():
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("size") == size:
                return data["words"]
        except (OSError, ValueError, KeyError):
            pass
    words = _transcribe_uncached(audio, language, model_name)
    cache.write_text(json.dumps({"size": size, "words": words}, ensure_ascii=False), encoding="utf-8")
    return words


def _transcribe_uncached(audio: Path, language: str, model_name: str) -> list[dict]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio), language=language, word_timestamps=True, vad_filter=False)
    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"text": text, "start": w.start, "end": w.end})
    return words


def _norm(token: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFD", token.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", t)


def align_to_script(script: str, heard: list[dict]) -> list[dict]:
    """Usa as palavras do ROTEIRO (sem erros de reconhecimento) com os tempos do Whisper.

    Palavras que o Whisper ouviu diferente recebem tempo interpolado entre as
    palavras vizinhas que casaram.
    """
    import difflib

    tokens = script.split()
    a = [_norm(t) for t in tokens]
    b = [_norm(w["text"]) for w in heard]
    times: list[tuple[float, float] | None] = [None] * len(tokens)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = (heard[j1 + k]["start"], heard[j1 + k]["end"])
    total_start = heard[0]["start"] if heard else 0.0
    total_end = heard[-1]["end"] if heard else 0.0
    out = []
    for idx, tok in enumerate(tokens):
        if times[idx] is None:
            prev_i = next((k for k in range(idx - 1, -1, -1) if times[k]), None)
            next_i = next((k for k in range(idx + 1, len(tokens)) if times[k]), None)
            lo = times[prev_i][1] if prev_i is not None else total_start
            hi = times[next_i][0] if next_i is not None else total_end
            gap = [k for k in range(len(tokens)) if times[k] is None and (prev_i is None or k > prev_i) and (next_i is None or k < next_i)]
            n = max(len(gap), 1)
            pos = gap.index(idx)
            step = (hi - lo) / n
            times[idx] = (lo + step * pos, lo + step * (pos + 1))
        out.append({"text": tok, "start": times[idx][0], "end": times[idx][1]})
    return out


def chunk_words(words: list[dict], max_words: int = 3) -> list[dict]:
    """Agrupa palavras em blocos curtos; quebra em pontuação forte."""
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[.!?:]$", w["text"]):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        start = c[0]["start"]
        end = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else c[-1]["end"] + 0.35
        end = max(end, c[-1]["end"])
        out.append({"start": start, "end": end, "text": " ".join(x["text"] for x in c)})
    return out


def build_ass(path: Path, narr_chunks: list[dict], delay: float, orig_lines: list[dict]) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narr,{FONT_NAME},74,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,420,1
Style: Orig,{FONT_NAME},64,&H0000E6FF,&H000000FF,&H00000000,&H64000000,-1,-1,0,0,100,100,0,0,1,6,2,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for c in narr_chunks:
        text = c["text"].upper().replace("\\", "")
        lines.append(f"Dialogue: 0,{ass_time(c['start'] + delay)},{ass_time(c['end'] + delay)},Narr,,0,0,0,,{text}\n")
    for o in orig_lines:
        lines.append(f"Dialogue: 0,{ass_time(o['t0'])},{ass_time(o['t1'])},Orig,,0,0,0,,{o['text']}\n")
    path.write_text("".join(lines), encoding="utf-8")


def render_clip(clip: dict, cfg: dict, workdir: Path, outdir: Path, model_name: str) -> Path:
    src = workdir / cfg["source"]
    narr = workdir / clip["voice"]
    src_dur = duration(src)
    narr_dur = duration(narr)
    delay = float(clip.get("narration_delay", 0.3))
    start = float(clip["start"])
    end = float(clip["end"])

    needed = delay + narr_dur + float(cfg.get("tail", 0.6))
    if end - start < needed:
        new_end = min(src_dur, start + needed)
        print(f"[{clip['id']}] narração não cabe ({needed:.1f}s > {end - start:.1f}s): estendendo fim para {new_end:.2f}s")
        end = new_end
    length = end - start
    if delay + narr_dur > length:
        print(f"[{clip['id']}] AVISO: narração termina depois do corte", file=sys.stderr)

    words = transcribe_words(narr, cfg.get("language", "pt"), model_name)
    if clip.get("text"):
        words = align_to_script(clip["text"], words)
    chunks = chunk_words(words, cfg.get("words_per_caption", 3))
    ass = workdir / f"{clip['id']}.ass"
    build_ass(ass, chunks, delay, clip.get("original_lines", []))

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{clip['id']}.mp4"
    orig_vol = float(clip.get("original_volume", 0.9))
    delay_ms = int(round(delay * 1000))

    vf = (
        f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps={FPS},split[a][b];"
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:6,eq=brightness=-0.12[bg];"
        f"[b]scale={W}:-2:flags=lanczos[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,ass={ass.name}:fontsdir={FONT_DIR},format=yuv420p[v];"
    )
    af = (
        f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,"
        f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,volume={orig_vol}[orig];"
        f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"adelay={delay_ms}|{delay_ms},apad,atrim=end={length},asplit=2[nsc][nmix];"
        f"[orig][nsc]sidechaincompress=threshold=0.015:ratio=12:attack=15:release=450:makeup=1[duck];"
        f"[duck][nmix]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    )
    run(
        [
            "ffmpeg", "-loglevel", "warning", "-y",
            "-i", src, "-i", narr,
            "-filter_complex", vf + af,
            "-map", "[v]", "-map", "[a]",
            "-t", f"{length:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart",
            out,
        ],
        cwd=workdir,  # o filtro `ass` resolve o arquivo .ass relativo a esta pasta
    )
    print(f"[{clip['id']}] ok -> {out} ({length:.1f}s)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path, help="pasta com o vídeo-fonte e os áudios")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", help="renderizar só este id de corte")
    ap.add_argument("--whisper-model", default="small")
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    for clip in cfg["clips"]:
        if args.only and clip["id"] != args.only:
            continue
        render_clip(clip, cfg, args.workdir.resolve(), args.out.resolve(), args.whisper_model)


if __name__ == "__main__":
    main()
