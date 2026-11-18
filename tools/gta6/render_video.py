#!/usr/bin/env python3
"""Pipeline v2: vídeo vertical 9:16 no estilo "curiosidade com fonte".

Diferenças para o render_clip.py (teste 1):
  - UMA locução contínua (mp3) em vez de trechos soltos;
  - cortes rápidos (um plano novo a cada ~2,2 s) montados a partir de segmentos;
  - enquadramento "gradient": vídeo centralizado e barras que estendem as bordas do
    próprio plano (cor do plano), ou "fill" (tela cheia) quando a fonte tem
    resolução para isso;
  - legenda de UMA palavra por vez, condensada, negrito e itálico;
  - som do jogo baixo e abaixando sob a locução (sidechain); -14 LUFS.

Uso (com o Python do `mpt`, que tem faster-whisper):
  PY="$(uv tool dir)/mpt/bin/python"
  "$PY" tools/gta6/render_video.py --config tools/gta6/exemplo_v2.json \
        --workdir <pasta com as fontes e a locução> --out <arquivo.mp4>

Config (JSON):
  {
    "narration": "audio/full.mp3",
    "text": "roteiro completo (para a legenda sair sem erro de reconhecimento)",
    "language": "pt",
    "shot_seconds": 2.2,
    "layout": "auto" | "gradient" | "fill",
    "game_audio_volume": 0.2,
    "sources": {"trailer": "trailer.mp4"},
    "segments": [ {"src": "trailer", "start": 23.3, "end": 34.1}, ... ]
  }
Os segmentos são percorridos em ordem e fatiados em planos de `shot_seconds` até
cobrir a duração da locução. Vídeos e áudios NÃO vão para o Git.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_clip import align_to_script, ass_time, duration, transcribe_words  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONT_NAME = "Liberation Sans Narrow"
FONT_DIR = "/usr/share/fonts/truetype/liberation"
CAPTION_Y = 1270  # ~66% da altura, como na referência


def probe_size(path: Path) -> tuple[int, int]:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)]
    ).decode().strip()
    w, h = out.split(",")
    return int(w), int(h)


def build_shots(segments: list[dict], total: float, shot_seconds: float) -> list[dict]:
    """Fatia os segmentos em planos curtos até cobrir `total` segundos."""
    shots: list[dict] = []
    covered = 0.0
    for seg in segments:
        t = float(seg["start"])
        end = float(seg["end"])
        while t < end - 0.4 and covered < total:
            d = min(shot_seconds, end - t, total - covered)
            if d < 0.5 and shots:  # evita plano minúsculo no fim: estende o anterior
                shots[-1]["dur"] += d
                covered += d
                break
            shots.append({"src": seg["src"], "start": t, "dur": d})
            covered += d
            t += d
        if covered >= total - 0.05:
            break
    if covered < total - 0.05:
        raise SystemExit(f"segmentos curtos demais: cobrem {covered:.1f}s de {total:.1f}s")
    # o último plano absorve qualquer sobra de arredondamento
    shots[-1]["dur"] += max(total - covered, 0.0)
    return shots


def layout_chain(layout: str, src_w: int, src_h: int) -> str:
    """Trecho de filtro que transforma [in] em um quadro 1080x1920 [out]."""
    if layout == "fill":
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
    fg_h = int(round(W * src_h / src_w / 2)) * 2
    bar = (H - fg_h) // 2
    if bar <= 0:
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
    # as barras esticam as bordas do próprio plano e desfocam (degradê da cor do plano)
    return (
        "split=3[t][m][b];"
        f"[m]scale={W}:{fg_h}:flags=lanczos,setsar=1[fg];"
        f"[t]crop=iw:6:0:0,scale={W}:{bar},boxblur=60:4,setsar=1[top];"
        f"[b]crop=iw:6:0:ih-6,scale={W}:{H - fg_h - bar},boxblur=60:4,setsar=1[bot];"
        "[top][fg][bot]vstack=inputs=3"
    )


def build_ass(path: Path, words: list[dict]) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{FONT_NAME},120,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,-1,0,0,100,100,0,0,1,9,3,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for i, w in enumerate(words):
        start = w["start"]
        nxt = words[i + 1]["start"] if i + 1 < len(words) else w["end"] + 0.4
        end = max(min(nxt, w["end"] + 0.5), start + 0.18)
        text = w["text"].upper().replace("\\", "").replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Word,,0,0,0,,{{\\an5\\pos({W // 2},{CAPTION_Y})}}{text}\n")
    path.write_text("".join(lines), encoding="utf-8")


def render(cfg: dict, workdir: Path, out: Path, whisper_model: str) -> None:
    narr = workdir / cfg["narration"]
    total = duration(narr) + float(cfg.get("tail", 0.5))
    shot_seconds = float(cfg.get("shot_seconds", 2.2))
    shots = build_shots(cfg["segments"], total, shot_seconds)
    print(f"{len(shots)} planos para {total:.1f}s de vídeo")

    # fontes de vídeo
    src_names = list(cfg["sources"].keys())
    src_idx = {name: i for i, name in enumerate(src_names)}
    src_sizes = {n: probe_size(workdir / cfg["sources"][n]) for n in src_names}

    # legenda: palavras do roteiro com tempos do Whisper
    words = transcribe_words(narr, cfg.get("language", "pt"), whisper_model)
    if cfg.get("text"):
        words = align_to_script(cfg["text"], words)
    ass = workdir / (out.stem + ".ass")
    build_ass(ass, words)

    layout_pref = cfg.get("layout", "auto")
    vparts, aparts = [], []
    for i, sh in enumerate(shots):
        k = src_idx[sh["src"]]
        sw, shh = src_sizes[sh["src"]]
        layout = layout_pref if layout_pref != "auto" else ("fill" if shh >= 1080 else "gradient")
        chain = layout_chain(layout, sw, shh)
        s, e = sh["start"], sh["start"] + sh["dur"]
        vparts.append(f"[{k}:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS,fps={FPS},{chain}[v{i}]")
        aparts.append(
            f"[{k}:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
            f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]"
        )
    n = len(shots)
    vconcat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,ass={ass.name}:fontsdir={FONT_DIR},format=yuv420p[v]"
    aconcat = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,volume={float(cfg.get('game_audio_volume', 0.2))}[game]"
    nar_idx = len(src_names)
    amix = (
        f"[{nar_idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,apad,atrim=end={total:.3f},asplit=2[nsc][nmix];"
        "[game][nsc]sidechaincompress=threshold=0.012:ratio=10:attack=15:release=400:makeup=1[duck];"
        "[duck][nmix]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    )
    graph = ";".join(vparts + aparts + [vconcat, aconcat, amix])
    graph_file = workdir / (out.stem + ".filtergraph")
    graph_file.write_text(graph, encoding="utf-8")

    cmd = ["ffmpeg", "-loglevel", "warning", "-y"]
    for name in src_names:
        cmd += ["-i", str(workdir / cfg["sources"][name])]
    cmd += ["-i", str(narr), "-filter_complex_script", str(graph_file), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True, cwd=workdir)
    print(f"ok -> {out} ({total:.1f}s)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--whisper-model", default="small")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    render(cfg, args.workdir.resolve(), args.out.resolve(), args.whisper_model)


if __name__ == "__main__":
    main()
