#!/usr/bin/env python3
"""Pipeline v2: vídeo vertical 9:16 (modos "explicativo" e "corte").

Modo "corte": clipe de live com a voz original do streamer, recorte opcional da câmera
(`crop` por fonte), gancho no topo (`hook`) e legenda de uma palavra. Ver exemplo_corte.json.

Modo "explicativo" (padrão): estilo "curiosidade com fonte".

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
    "background": "black" (padrão) | "gradient"   (cor das sobras quando o vídeo não preenche a tela),
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
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_clip import _norm, align_to_script, ass_time, duration, transcribe_words  # noqa: E402

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


def layout_chain(layout: str, src_w: int, src_h: int, background: str = "black") -> str:
    """Trecho de filtro que transforma [in] em um quadro 1080x1920 [out]."""
    if layout == "fill":
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
    fg_h = int(round(W * src_h / src_w / 2)) * 2
    bar = (H - fg_h) // 2
    if bar <= 0:
        return f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
    if background == "black":
        # fundo preto liso (decisão do usuário em 18/11/2026)
        return f"scale={W}:{fg_h}:flags=lanczos,setsar=1,pad={W}:{H}:0:{bar}:color=black"
    # "gradient": as barras esticam as bordas do próprio plano e desfocam (degradê da cor do plano)
    return (
        "split=3[t][m][b];"
        f"[m]scale={W}:{fg_h}:flags=lanczos,setsar=1[fg];"
        f"[t]crop=iw:6:0:0,scale={W}:{bar},boxblur=60:4,setsar=1[top];"
        f"[b]crop=iw:6:0:ih-6,scale={W}:{H - fg_h - bar},boxblur=60:4,setsar=1[bot];"
        "[top][fg][bot]vstack=inputs=3"
    )


MIN_WORD = 0.22   # s: menos que isso a palavra só pisca na tela
MAX_CHARS = 12    # junta palavras rápidas até este tamanho (cabe na largura com a fonte 120)
READ_CPS = 30     # caracteres por segundo que dá para ler: bloco de 12 letras fica >= 0,4 s
MAX_LAG = 0.3     # a legenda pode atrasar no máximo 0,3 s em relação à fala


def caption_timeline(words: list[dict]) -> list[dict]:
    """Tempos de tela da legenda: nunca duas palavras ao mesmo tempo, nenhuma rápida demais.

    Palavra que duraria menos de MIN_WORD é juntada com a seguinte ("O GTA", "DO SEU"),
    desde que o par caiba em MAX_CHARS e a primeira não termine frase. Depois, cada bloco
    começa quando o anterior sai (sem sobreposição) e fica no mínimo MIN_WORD.
    """
    ws = [dict(w) for w in words if w.get("text", "").strip()]
    merged, i = [], 0
    while i < len(ws):
        w = dict(ws[i])
        while (
            i + 1 < len(ws)
            and w["end"] - w["start"] < MIN_WORD
            and not re.search(r"[.!?:]$", w["text"])
            and len(w["text"]) + 1 + len(ws[i + 1]["text"]) <= MAX_CHARS
        ):
            i += 1
            w = {"text": f"{w['text']} {ws[i]['text']}", "start": w["start"], "end": ws[i]["end"]}
        merged.append(w)
        i += 1
    out, free_at = [], 0.0
    for k, w in enumerate(merged):
        if out and free_at > w["start"] + MAX_LAG:  # atraso acumulado: encurta o bloco anterior
            out[-1]["end"] = max(w["start"] + MAX_LAG, out[-1]["start"] + 0.12)
            free_at = out[-1]["end"]
        start = max(w["start"], free_at)
        nxt = merged[k + 1]["start"] if k + 1 < len(merged) else w["end"] + 0.4
        need = max(MIN_WORD, len(w["text"]) / READ_CPS)  # tempo mínimo cresce com o tamanho do texto
        end = max(min(nxt, w["end"] + 0.5), start + need)
        out.append({"text": w["text"], "start": start, "end": end})
        free_at = end
    return out


def build_ass(path: Path, words: list[dict], emphasis: set[str] | None = None, caption_y: int = CAPTION_Y) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,{FONT_NAME},120,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,-1,0,0,100,100,0,0,1,9,3,5,40,40,0,1
Style: Mark,{FONT_NAME},60,&H001E1EFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1
Style: Sub,{FONT_NAME},50,&H00FFFFFF,&H000000FF,&H96000000,&H00000000,-1,0,0,0,100,100,0,0,3,12,0,5,60,60,0,1
Style: Hook,{FONT_NAME},84,&H00000000,&H000000FF,&H004DD8FF,&H00000000,-1,-1,0,0,100,100,0,0,3,18,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for w in caption_timeline(words):
        text = w["text"].upper().replace("\\", "").replace("{", "").replace("}", "")
        # destaque (amarelo #ffd84d): números, ênfase pedida no config, palavras com ! ou ?
        hot = any(
            bool(emphasis and _norm(tok) in emphasis) or any(c.isdigit() for c in tok) or tok.endswith(("!", "?"))
            for tok in w["text"].split()
        )
        color = "\\c&H004DD8FF&" if hot else ""
        # "pop": a palavra entra 118% e assenta em 100% em 110 ms
        pop = "\\fscx118\\fscy118\\t(0,110,\\fscx100\\fscy100)"
        lines.append(f"Dialogue: 0,{ass_time(w['start'])},{ass_time(w['end'])},Word,,0,0,0,,{{\\an5\\pos({W // 2},{caption_y}){pop}{color}}}{text}\n")
    path.write_text("".join(lines), encoding="utf-8")


SFX_DIR = Path(__file__).resolve().parents[2] / "assets" / "sfx"
RED_BGR = "&H001E1EFF&"  # vermelho (BGR), usado em círculos e setas


def circle_path(rx: float, ry: float) -> str:
    """Elipse como curvas de Bézier (desenho ASS), centrada em (0, 0)."""
    k = 0.5523
    return (
        f"m 0 {-ry:.0f} b {k * rx:.0f} {-ry:.0f} {rx:.0f} {-k * ry:.0f} {rx:.0f} 0 "
        f"b {rx:.0f} {k * ry:.0f} {k * rx:.0f} {ry:.0f} 0 {ry:.0f} "
        f"b {-k * rx:.0f} {ry:.0f} {-rx:.0f} {k * ry:.0f} {-rx:.0f} 0 "
        f"b {-rx:.0f} {-k * ry:.0f} {-k * rx:.0f} {-ry:.0f} 0 {-ry:.0f}"
    )


ARROW_PATH = "m 0 0 l -64 -48 -64 -22 -210 -22 -210 22 -64 22 -64 48"  # ponta em (0,0), aponta para +x


def add_marks_to_ass(path: Path, marks: list[dict]) -> None:
    """Círculos e setas vermelhas animados, como em edição manual.

    {"type": "circle", "t": 10.0, "dur": 2.5, "x": 722, "y": 735, "rx": 115, "ry": 95}
    {"type": "arrow",  "t": 34.8, "dur": 2.8, "x": 690, "y": 830, "angle": 225, "scale": 1.0}
    Opcional "path": [[t, x, y], ...] (tempo de saída): a marca acompanha um alvo que se mexe.
    Círculo: (x, y) é o CENTRO. Seta: (x, y) é onde a PONTA aponta; `angle` em graus,
    anti-horário (0 = aponta para a direita, 225 = para baixo e à esquerda).
    Usamos \\an7 (canto superior esquerdo): assim a origem do desenho cai exatamente em \\pos.
    """
    lines = []
    for m in marks:
        t0, t1 = float(m["t"]), float(m["t"]) + float(m.get("dur", 2.5))
        kind = m.get("type", "circle")
        # trajetória: o alvo se mexe -> [[t, x, y], ...] em tempo de saída; entre pontos a marca desliza
        pts = [(float(a), float(b), float(c)) for a, b, c in m.get("path", [])] or [(t0, float(m["x"]), float(m["y"]))]
        pts = sorted(pts)
        if pts[0][0] > t0:
            pts.insert(0, (t0, pts[0][1], pts[0][2]))
        if pts[-1][0] < t1:
            pts.append((t1, pts[-1][1], pts[-1][2]))
        segs = [(a, b) for a, b in zip(pts, pts[1:]) if b[0] > a[0] and a[0] < t1 and b[0] > t0]
        for n, (a, b) in enumerate(segs):
            first, last = n == 0, n == len(segs) - 1
            sa, sb = max(a[0], t0), min(b[0], t1)
            pos = (f"\\pos({a[1]:.0f},{a[2]:.0f})" if (a[1], a[2]) == (b[1], b[2])
                   else f"\\move({a[1]:.0f},{a[2]:.0f},{b[1]:.0f},{b[2]:.0f})")
            fade = f"\\fad({90 if first else 0},{160 if last else 0})"
            if kind == "circle":
                shape = circle_path(float(m.get("rx", 140)), float(m.get("ry", 100)))
                # o traço "cresce" (borda de 2 para 12 px) e a forma assenta de 108% para 100%
                intro = "\\bord2\\fscx108\\fscy108\\t(0,220,\\bord12\\fscx100\\fscy100)" if first else "\\bord12"
                tags = f"\\an7{pos}\\p1\\1a&HFF&\\3c{RED_BGR}\\shad0{intro}{fade}"
            elif kind == "arrow":
                sc = float(m.get("scale", 1.0))
                ang = float(m.get("angle", 225))
                # "crava" no alvo: começa 160% maior e assenta em 100% com a ponta fixa
                intro = (f"\\fscx{160 * sc:.0f}\\fscy{160 * sc:.0f}\\t(0,200,\\fscx{100 * sc:.0f}\\fscy{100 * sc:.0f})"
                         if first else f"\\fscx{100 * sc:.0f}\\fscy{100 * sc:.0f}")
                tags = f"\\an7{pos}\\frz{ang:.0f}\\p1\\1c{RED_BGR}\\3c&H000000&\\bord7\\shad0{intro}{fade}"
                shape = ARROW_PATH
            else:
                continue
            lines.append(f"Dialogue: 2,{ass_time(sa)},{ass_time(sb)},Mark,,0,0,0,,{{{tags}}}{shape}{{\\p0}}\n")
    if lines:
        path.write_text(path.read_text(encoding="utf-8") + "".join(lines), encoding="utf-8")


def _mean_db(path: Path, t0: float | None = None, dur: float | None = None) -> float:
    cmd = ["ffmpeg", "-hide_banner"]
    if t0 is not None:
        cmd += ["-ss", f"{max(t0, 0.0):.3f}", "-t", f"{dur:.3f}"]
    cmd += ["-i", str(path), "-af", "volumedetect", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    return float(m.group(1)) if m else -91.0


SFX_REL_DB = -6.0     # SFX sobre fala: 6 dB abaixo da fala (aparece sem cobrir a voz)
SFX_GAP_REL_DB = -3.0  # SFX em silêncio: 3 dB abaixo da média da fala do clipe


def build_sfx_track(items: list[dict], workdir: Path, total: float, name: str, speech: Path | None = None,
                    words: list[dict] | None = None) -> Path | None:
    """Mistura os SFX numa faixa única do tamanho do vídeo.

    Volume: se o item tem `vol`, usa esse ganho fixo (legado). Se não, o ganho é calculado
    contra a fala ao redor (`speech`): o efeito fica `rel_db` (padrão -6 dB) abaixo da fala
    naquele instante; em silêncio, -3 dB abaixo da média da fala. Assim nenhum efeito some
    nem cobre a voz, qualquer que seja o volume do streamer.
    """
    if not items:
        return None
    speech_avg = _mean_db(speech) if speech else None
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    filt, labels = [], []
    for i, it in enumerate(items):
        f = SFX_DIR / f"sfx_{it['name']}.mp3"
        if not f.exists():
            raise SystemExit(f"SFX inexistente: {f}")
        cmd += ["-i", str(f)]
        ms = int(round(float(it["t"]) * 1000))
        if "vol" in it or speech is None:
            gain = f"volume={float(it.get('vol', 0.2))}"
        else:
            t = float(it["t"])
            local = _mean_db(speech, t - 0.4, 1.0)
            talking = any(w["start"] - 0.15 <= t <= w["end"] + 0.15 for w in (words or []))
            if talking or (words is None and local > speech_avg - 10):  # há fala ali
                target = local + float(it.get("rel_db", SFX_REL_DB))
            else:
                target = speech_avg + float(it.get("rel_db", SFX_GAP_REL_DB))
            g = max(min(target - _mean_db(f), 24.0), -45.0)
            it["_gain_db"] = round(g, 1)
            gain = f"volume={g:.1f}dB"
        filt.append(
            f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
            f"{gain},adelay={ms}|{ms}[s{i}]"
        )
        labels.append(f"[s{i}]")
    filt.append("".join(labels) + f"amix=inputs={len(items)}:normalize=0:duration=longest,apad,atrim=end={total:.3f}[out]")
    out = workdir / f"{name}_sfx.wav"
    cmd += ["-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", "-ac", "2", str(out)]
    subprocess.run(cmd, check=True)
    print("SFX:", ", ".join(f"{it['name']}@{it['t']} {it.get('_gain_db', it.get('vol'))}" for it in items))
    return out


def zoom_filter(zooms: list[dict], offset: float, w: int, h: int) -> str:
    """Zoom de impacto (punch-in 1,08-1,10x, ~0,4 s) no centro, em tempo de SAÍDA menos `offset`."""
    terms = []
    for z in zooms:
        a = float(z["t"]) - offset
        b = a + float(z.get("dur", 0.4))
        f = min(float(z.get("factor", 1.09)), 1.12)  # acima de 1.12x enjoa
        if b <= 0:
            continue
        terms.append(f"({f - 1:.4f})*between(it,{a:.3f},{b:.3f})*min(1,(it-{a:.3f})/0.08)")
    if not terms:
        return ""
    expr = "1+" + "+".join(terms)
    return f"zoompan=z='{expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={FPS},"


def freeze_filter(freezes: list[dict], offset: float, idx: int) -> str:
    """Quadro congelado ("pause-point"): a imagem pára por `dur` s e o áudio segue; depois a imagem volta
    já sincronizada (a duração total não muda). Tempos em tempo de SAÍDA. Feito com trim + loop + concat
    (o filtro `freezeframes` travou o ffmpeg com fonte 1440p)."""
    out = ""
    for k, z in enumerate(freezes):
        t0 = float(z["t"]) - offset
        dur = float(z.get("dur", 1.0))
        if t0 < 0:
            continue
        n = max(int(round(dur * FPS)), 1)
        t1 = t0 + dur
        u = f"fz{idx}_{k}"
        out += (
            f"split=3[{u}a][{u}b][{u}c];"
            f"[{u}a]trim=end={t0:.3f},setpts=PTS-STARTPTS[{u}p];"
            f"[{u}b]trim=start={t0:.3f}:end={t0 + 1.5 / FPS:.3f},setpts=PTS-STARTPTS,trim=end_frame=1,loop=loop={n}:size=1:start=0,setpts=N/({FPS}*TB)[{u}h];"
            f"[{u}c]trim=start={t1:.3f},setpts=PTS-STARTPTS[{u}n];"
            f"[{u}p][{u}h][{u}n]concat=n=3:v=1:a=0,"
        )
    return out


def stack_chain(panels: list[dict], k: int, s: float, e: float, freeze: str, zooms: list[dict], offset: float, i: int) -> str:
    """Layout empilhado: vários recortes da MESMA fonte, um embaixo do outro (ex.: câmera do
    streamer em cima, gameplay embaixo). `panels`: [{"crop": [x, y, w, h], "h": 668, "zoom": false}, ...];
    as alturas `h` somam 1920. O congelamento vale para tudo; o zoom só nos painéis com "zoom": true.
    """
    if sum(int(p["h"]) for p in panels) != H:
        raise SystemExit(f"stack: alturas somam {sum(int(p['h']) for p in panels)}, precisa {H}")
    n = len(panels)
    out = f"[{k}:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS,fps={FPS},{freeze}split={n}" + "".join(f"[st{i}_{j}]" for j in range(n)) + ";"
    for j, p in enumerate(panels):
        x, y, w, h = [int(c) - int(c) % 2 for c in p["crop"]]
        ph = int(p["h"])
        z = zoom_filter(zooms, offset, w, h) if p.get("zoom") else ""
        out += (f"[st{i}_{j}]crop={w}:{h}:{x}:{y},{z}scale={W}:{ph}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{ph},setsar=1[sp{i}_{j}];")
    return out + "".join(f"[sp{i}_{j}]" for j in range(n)) + f"vstack=inputs={n}[v{i}]"


def split_phrases(phrases: list[dict]) -> list[dict]:
    """Frase com início/fim -> palavras com tempo proporcional ao tamanho (para falas lidas à mão,
    ex.: na legenda queimada da Twitch, quando o Whisper não separa a voz do streamer do jogo)."""
    out = []
    for ph in phrases:
        toks = ph["text"].split()
        if not toks:
            continue
        t, span = float(ph["start"]), float(ph["end"]) - float(ph["start"])
        weights = [len(x) + 2 for x in toks]
        for tok, wgt in zip(toks, weights):
            d = span * wgt / sum(weights)
            out.append({"text": tok, "start": t, "end": t + d})
            t += d
    return out


def add_subs_to_ass(path: Path, subs: list[dict], y: int = 1480) -> None:
    """Legenda de diálogo do JOGO (NPC), menor e em caixa, para não competir com a fala do streamer."""
    lines = []
    for sb in subs:
        text = wrap_hook(sb["text"].replace("{", "").replace("}", ""), 34)
        lines.append(f"Dialogue: 1,{ass_time(float(sb['start']))},{ass_time(float(sb['end']))},Sub,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\fad(80,80)}}{text}\n")
    if lines:
        path.write_text(path.read_text(encoding="utf-8") + "".join(lines), encoding="utf-8")


def wrap_hook(text: str, width: int = 20) -> str:
    """Quebra o gancho em linhas curtas (\\N do ASS)."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines)


def add_hook_to_ass(path: Path, hook: str, seconds: float, y: int = 300) -> None:
    """Acrescenta o gancho (texto no topo, primeiros segundos) a um .ass já criado."""
    text = wrap_hook(hook.upper().replace("\\", "").replace("{", "").replace("}", ""))
    line = f"Dialogue: 1,{ass_time(0.0)},{ass_time(seconds)},Hook,,0,0,0,,{{\\an8\\pos({W // 2},{y})}}{text}\n"
    path.write_text(path.read_text(encoding="utf-8") + line, encoding="utf-8")


def render(cfg: dict, workdir: Path, out: Path, whisper_model: str) -> None:
    mode = cfg.get("mode", "explicativo")

    # fontes de vídeo: "nome": "arquivo.mp4"  ou  "nome": {"path": "...", "crop": [x, y, w, h]}
    src_names = list(cfg["sources"].keys())
    src_idx = {name: i for i, name in enumerate(src_names)}
    src_path, src_crop, src_sizes = {}, {}, {}
    for n in src_names:
        v = cfg["sources"][n]
        src_path[n] = workdir / (v["path"] if isinstance(v, dict) else v)
        src_crop[n] = v.get("crop") if isinstance(v, dict) else None
        if src_crop[n]:
            # vídeo 4:2:0 exige medidas pares: recortes ímpares travam o ffmpeg
            src_crop[n] = [int(c) - (int(c) % 2) for c in src_crop[n]]
            src_sizes[n] = (int(src_crop[n][2]), int(src_crop[n][3]))
        else:
            src_sizes[n] = probe_size(src_path[n])

    if mode == "corte":
        # corte de live: voz original do streamer, sem narração nova, sem cortes rápidos
        shots = [
            {"src": sg["src"], "start": float(sg["start"]), "dur": float(sg["end"]) - float(sg["start"])}
            for sg in cfg["segments"]
        ]
        total = sum(sh["dur"] for sh in shots)
        wav = workdir / (out.stem + "_fala.wav")
        first = shots[0]
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-ss", str(first["start"]), "-t", str(total), "-i", str(src_path[first["src"]]), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
            check=True,
        )
        narr = wav
    else:
        narr = workdir / cfg["narration"]
        total = duration(narr) + float(cfg.get("tail", 0.5))
        shots = build_shots(cfg["segments"], total, float(cfg.get("shot_seconds", 2.2)))
    print(f"{len(shots)} planos para {total:.1f}s de vídeo (modo {mode})")

    # legenda: palavras do roteiro (ou do Whisper) com tempos do Whisper
    if cfg.get("words_from"):  # reaproveita a transcrição do prepare.py (contexto.json)
        words = json.loads((workdir / cfg["words_from"]).read_text(encoding="utf-8"))["palavras"]
    else:
        words = transcribe_words(narr, cfg.get("language", "pt"), whisper_model)
    if cfg.get("text"):
        words = align_to_script(cfg["text"], words)
    manual = (cfg.get("words_manual") or []) + split_phrases(cfg.get("speech_manual") or [])
    if cfg.get("words_mode") == "manual":  # Whisper só ouviu o jogo: usa só as falas marcadas à mão
        words = []
    if manual and words:  # falas que o Whisper não pegou (ex.: o streamer por cima do áudio do jogo): têm prioridade
        lo, hi = min(m["start"] for m in manual), max(m["end"] for m in manual)
        words = [w for w in words if not (lo - 0.05 <= w["start"] <= hi)] + [dict(m) for m in manual]
        words.sort(key=lambda w: w["start"])
    elif manual:
        words = sorted((dict(m) for m in manual), key=lambda w: w["start"])
    ass = workdir / (out.stem + ".ass")
    build_ass(ass, words, {_norm(x) for x in cfg.get("emphasis", [])}, int(cfg.get("caption_y", CAPTION_Y)))
    if cfg.get("hook"):
        add_hook_to_ass(ass, cfg["hook"], float(cfg.get("hook_seconds", 3.5)), int(cfg.get("hook_y", 300)))
    add_marks_to_ass(ass, cfg.get("annotations", []))
    add_subs_to_ass(ass, cfg.get("subs", []), int(cfg.get("subs_y", 1480)))
    sfx_track = build_sfx_track(cfg.get("sfx", []), workdir, total, out.stem, narr, words)

    layout_pref = cfg.get("layout", "auto")
    vparts, aparts = [], []
    shot_off = 0.0
    for i, sh in enumerate(shots):
        k = src_idx[sh["src"]]
        sw, shh = src_sizes[sh["src"]]
        layout = layout_pref if layout_pref != "auto" else ("fill" if shh >= 1080 else "gradient")
        chain = layout_chain(layout, sw, shh, cfg.get("background", "black"))
        cr = src_crop[sh["src"]]
        crop = f"crop={cr[2]}:{cr[3]}:{cr[0]}:{cr[1]}," if cr else ""
        s, e = sh["start"], sh["start"] + sh["dur"]
        zoom = freeze_filter(cfg.get("freezes", []), shot_off, i) + zoom_filter(cfg.get("zooms", []), shot_off, sw, shh)
        shot_off += sh["dur"]
        if cfg.get("stack"):
            vparts.append(stack_chain(cfg["stack"], k, s, e, freeze_filter(cfg.get("freezes", []), shot_off - sh["dur"], i),
                                      cfg.get("zooms", []), shot_off - sh["dur"], i))
        else:
            vparts.append(f"[{k}:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS,fps={FPS},{crop}{zoom}{chain}[v{i}]")
        aparts.append(
            f"[{k}:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS,"
            f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]"
        )
    n = len(shots)
    vconcat = "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,ass={ass.name}:fontsdir={FONT_DIR},format=yuv420p[v]"
    if mode == "corte":
        # voz original do streamer: volume cheio, só normaliza
        base = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1"
        if sfx_track:
            amix = base + f"[orig];[orig][{len(src_names)}:a]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-12.8:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.8:level=disabled:attack=2:release=40[a]"
            extra_inputs = ["-i", str(sfx_track)]
        else:
            amix = base + ",loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.8:level=disabled:attack=2:release=40[a]"
            extra_inputs = []
        graph = ";".join(vparts + aparts + [vconcat, amix])
    else:
        aconcat = "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,volume={float(cfg.get('game_audio_volume', 0.2))}[game]"
        nar_idx = len(src_names)
        mix = (
            f"[{nar_idx}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,apad,atrim=end={total:.3f},asplit=2[nsc][nmix];"
            "[game][nsc]sidechaincompress=threshold=0.012:ratio=10:attack=15:release=400:makeup=1[duck];"
            "[duck][nmix]amix=inputs=2:normalize=0:duration=first[m];"
            + (f"[m][{nar_idx + 1}:a]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.8:level=disabled:attack=2:release=40[a]" if sfx_track else "[m]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.8:level=disabled:attack=2:release=40[a]")
        )
        graph = ";".join(vparts + aparts + [vconcat, aconcat, mix])
        extra_inputs = ["-i", str(narr)] + (["-i", str(sfx_track)] if sfx_track else [])
    graph_file = workdir / (out.stem + ".filtergraph")
    graph_file.write_text(graph, encoding="utf-8")

    cmd = ["ffmpeg", "-loglevel", "warning", "-y"]
    for name in src_names:
        cmd += ["-i", str(src_path[name])]
    cmd += extra_inputs + ["-filter_complex_script", str(graph_file), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}"]
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
