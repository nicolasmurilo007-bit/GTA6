#!/usr/bin/env python3
"""Auditoria detalhada de um clipe renderizado: legenda, áudio, efeitos e marcações.

Complementa o qa.py (que só mede o arquivo). Aqui o vídeo é conferido CONTRA o config:
  1. legenda: palavras sobrepostas, rápidas demais para ler, texto x o que se ouve no áudio
     final (nova transcrição do próprio final.mp4), buracos longos sem legenda durante fala;
  2. áudio: cada SFX — se cai em cima de fala, quanto mais alto que a fala, se tem efeito
     colado em outro; volume por trecho (picos/buracos);
  3. visual: folhas de quadros para revisar a olho — gancho, cada marcação (início, meio, fim:
     o alvo continua dentro do círculo / na ponta da seta?), zoom, congelamento, e o clipe
     inteiro a cada 2 s.

Uso (Python do mpt):
  "$(uv tool dir)/mpt/bin/python" tools/gta6/auditoria.py --config <clipe.json> \
      --workdir <pasta das fontes> --video <final.mp4> --out <pasta de saída>
Gera auditoria.json, auditoria.md e folhas *.png na pasta de saída.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_clip import _norm, transcribe_words  # noqa: E402

MIN_WORD = 0.20   # s: abaixo disso a palavra pisca (ilegível)
MAX_CPS = 22      # caracteres por segundo acima disso não dá para ler
SFX_SPEECH_DB = -3.0  # SFX sobre fala não deve passar da fala menos 3 dB


def ass_events(path: Path, style: str) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if parts[3] != style:
            continue
        def t(s):
            h, m, sec = s.split(":")
            return int(h) * 3600 + int(m) * 60 + float(sec)
        text = re.sub(r"\{[^}]*\}", "", parts[9]).replace("\\N", " ")
        out.append({"start": t(parts[1]), "end": t(parts[2]), "text": text})
    return out


def check_captions(words: list[dict], heard: list[dict]) -> list[dict]:
    issues = []
    for a, b in zip(words, words[1:]):
        if b["start"] < a["end"] - 0.01:
            issues.append({"tipo": "legenda_sobreposta", "t": round(b["start"], 2),
                           "detalhe": f"'{a['text']}' ainda na tela quando '{b['text']}' entra"})
    for w in words:
        d = w["end"] - w["start"]
        if d < MIN_WORD:
            issues.append({"tipo": "legenda_rapida", "t": round(w["start"], 2),
                           "detalhe": f"'{w['text']}' fica {d:.2f}s (mín. {MIN_WORD}s)"})
        elif len(w["text"]) / max(d, 0.01) > MAX_CPS:
            issues.append({"tipo": "legenda_rapida", "t": round(w["start"], 2),
                           "detalhe": f"'{w['text']}' {len(w['text']) / d:.0f} car/s"})
    # texto: o que está escrito x o que se ouve no final
    cap = [t for w in words for t in w["text"].split()]
    cap_t = [w["start"] for w in words for _ in w["text"].split()]
    a = [_norm(x) for x in cap]
    b = [_norm(h["text"]) for h in heard]
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        escrito = " ".join(cap[i1:i2])
        ouvido = " ".join(h["text"] for h in heard[j1:j2])
        t = cap_t[i1] if i1 < len(cap_t) else (heard[j1]["start"] if j1 < len(heard) else 0)
        issues.append({"tipo": "legenda_texto", "t": round(t, 2),
                       "detalhe": f"escrito '{escrito}' | ouvido '{ouvido}'"})
    # fala sem legenda: palavra ouvida sem nenhuma legenda na tela por perto
    for h in heard:
        mid = (h["start"] + h["end"]) / 2
        if not any(w["start"] - 0.3 <= mid <= w["end"] + 0.3 for w in words):
            issues.append({"tipo": "fala_sem_legenda", "t": round(h["start"], 2), "detalhe": f"'{h['text']}'"})
    return issues


def rms_db(wav: Path, t0: float, dur: float) -> float:
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-ss", f"{max(t0, 0):.3f}", "-t", f"{dur:.3f}", "-i", str(wav),
         "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else -91.0


def check_sfx(cfg: dict, words: list[dict], fala: Path | None, sfx_wav: Path | None) -> list[dict]:
    issues = []
    items = sorted(cfg.get("sfx", []), key=lambda s: float(s["t"]))
    for a, b in zip(items, items[1:]):
        if float(b["t"]) - float(a["t"]) < 0.35:
            issues.append({"tipo": "sfx_colado", "t": float(b["t"]),
                           "detalhe": f"{a['name']} e {b['name']} a {float(b['t']) - float(a['t']):.2f}s: vira um barulho só"})
    for s in items:
        t = float(s["t"])
        speaking = [w["text"] for w in words if w["start"] - 0.1 <= t <= w["end"] + 0.1]
        rec = {"tipo": "sfx_info", "t": t, "detalhe": f"{s['name']} vol {s.get('vol', 0.2)}"}
        if fala and sfx_wav:
            sp, fx = rms_db(fala, t, 0.5), rms_db(sfx_wav, t, 0.5)
            rec["detalhe"] += f" | SFX {fx:.1f} dB x fala {sp:.1f} dB"
            if speaking and fx > sp + SFX_SPEECH_DB:
                issues.append({"tipo": "sfx_cobre_fala", "t": t,
                               "detalhe": f"{s['name']} {fx - sp:+.1f} dB acima da fala durante '{' '.join(speaking)}'"})
        issues.append(rec)
    return issues


def frame(video: Path, t: float, out: Path, crop: tuple[int, int, int, int] | None = None, w: int = 360) -> Path:
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "") + f"scale={w}:-2"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                    "-vf", vf + f",drawtext=text='{t:.1f}s':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black",
                    str(out)], check=True)
    return out


def sheet(frames: list[Path], out: Path, cols: int) -> Path:
    if not frames:
        return out
    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for f in frames:
        cmd += ["-i", str(f)]
    n = len(frames)
    rows = (n + cols - 1) // cols
    while len(frames) < rows * cols:  # completa a grade
        frames.append(frames[-1])
        cmd += ["-i", str(frames[-1])]
    # xstack precisa de posições em pixels: usa larguras/alturas do primeiro quadro
    layout = "|".join(f"{'+'.join(['w0'] * (i % cols)) or '0'}_{'+'.join(['h0'] * (i // cols)) or '0'}" for i in range(rows * cols))
    cmd += ["-filter_complex", f"xstack=inputs={rows * cols}:layout={layout}", str(out)]
    subprocess.run(cmd, check=True)
    return out


def visual_sheets(cfg: dict, video: Path, total: float, out: Path) -> dict:
    tmp = out / "_q"
    tmp.mkdir(parents=True, exist_ok=True)
    sheets = {}
    # marcações: 4 instantes ao longo da duração, recorte 600x600 em volta do alvo
    fr = []
    for k, a in enumerate(cfg.get("annotations", [])):
        t0, d = float(a["t"]), float(a.get("dur", 2.5))
        x, y = int(a["x"]), int(a["y"])
        c = (min(max(x - 300, 0), 480), min(max(y - 300, 0), 1320), 600, 600)
        for j, f in enumerate((0.05, 0.35, 0.65, 0.95)):
            fr.append(frame(video, t0 + d * f, tmp / f"m{k}_{j}.png", c, 300))
    if fr:
        sheets["marcacoes"] = str(sheet(fr, out / "folha_marcacoes.png", 4))
    # gancho, zoom e congelamento
    fr = []
    if cfg.get("hook"):
        hs = float(cfg.get("hook_seconds", 3.5))
        fr += [frame(video, 0.2, tmp / "h0.png"), frame(video, hs - 0.2, tmp / "h1.png")]
    for k, z in enumerate(cfg.get("zooms", [])):
        fr += [frame(video, float(z["t"]) - 0.1, tmp / f"z{k}a.png"), frame(video, float(z["t"]) + 0.2, tmp / f"z{k}b.png")]
    for k, z in enumerate(cfg.get("freezes", [])):
        fr += [frame(video, float(z["t"]) + 0.1, tmp / f"f{k}a.png"), frame(video, float(z["t"]) + float(z.get("dur", 1)) - 0.1, tmp / f"f{k}b.png")]
    if fr:
        sheets["efeitos"] = str(sheet(fr, out / "folha_efeitos.png", 4))
    # clipe inteiro a cada 2 s
    fr = [frame(video, t, tmp / f"g{int(t * 10)}.png", w=216) for t in [x * 2.0 + 0.5 for x in range(int(total // 2))]]
    sheets["geral"] = str(sheet(fr, out / "folha_geral.png", 8))
    return sheets


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--whisper-model", default="medium")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.video.stem
    ass = args.workdir / f"{stem}.ass"
    words = ass_events(ass, "Word")
    fala = args.workdir / f"{stem}_fala.wav"
    sfx_wav = args.workdir / f"{stem}_sfx.wav"
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(args.video)]))

    # o que se ouve no FINAL (voz + jogo + sfx), não na fonte
    heard_wav = args.out / f"{stem}_ouvido.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(args.video), "-vn", "-ac", "1", "-ar", "16000", str(heard_wav)], check=True)
    heard = transcribe_words(heard_wav, cfg.get("language", "pt"), args.whisper_model)

    issues = check_captions(words, heard)
    issues += check_sfx(cfg, words, fala if fala.exists() else None, sfx_wav if sfx_wav.exists() else None)
    sheets = visual_sheets(cfg, args.video, total, args.out)
    issues.sort(key=lambda i: i["t"])
    rep = {"video": str(args.video), "duracao": total, "palavras_legenda": len(words), "palavras_ouvidas": len(heard),
           "problemas": [i for i in issues if i["tipo"] != "sfx_info"], "sfx": [i for i in issues if i["tipo"] == "sfx_info"],
           "folhas": sheets}
    (args.out / "auditoria.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    md = [f"# Auditoria {args.video.name} ({total:.1f}s)", ""]
    from collections import Counter
    md.append("Resumo: " + ", ".join(f"{k} {v}" for k, v in Counter(i["tipo"] for i in rep["problemas"]).items()))
    md += ["", "| t (s) | tipo | detalhe |", "|---|---|---|"]
    md += [f"| {i['t']:.2f} | {i['tipo']} | {i['detalhe']} |" for i in rep["problemas"] + rep["sfx"]]
    (args.out / "auditoria.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:3]))
    print(f"-> {args.out / 'auditoria.md'}")


if __name__ == "__main__":
    main()
