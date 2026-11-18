#!/usr/bin/env python3
"""Controle de qualidade automático do vídeo final (números do guia de layout).

Uso: python tools/gta6/qa.py <video.mp4> [--out qa.json]
Sai com código 0 se APROVADO e 1 se REPROVADO. `atencao` não reprova.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", *args], capture_output=True, text=True).stderr


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    v = str(a.video)
    items = []

    def add(nome, estado, detalhe):
        items.append({"item": nome, "estado": estado, "detalhe": detalhe})

    pr = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", v]))
    vs = [s for s in pr["streams"] if s["codec_type"] == "video"]
    au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    dur = float(pr["format"]["duration"])
    add("resolução 1080x1920", "ok" if vs and (vs[0]["width"], vs[0]["height"]) == (1080, 1920) else "falha", f'{vs[0]["width"]}x{vs[0]["height"]}' if vs else "sem vídeo")
    add("áudio presente", "ok" if au else "falha", "")
    add("duração 8 s a 180 s", "ok" if 8 <= dur <= 180 else "falha", f"{dur:.1f}s")

    r = ff(["-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    if lufs:
        L = float(lufs[-1])
        add("volume -15 a -13 LUFS", "ok" if -15.0 <= L <= -13.0 else ("atencao" if -16.5 <= L <= -12.0 else "falha"), f"{L} LUFS")
    if peak:
        P = float(peak[-1])
        add("pico real <= -1,5 dBTP", "ok" if P <= -1.45 else "falha", f"{P} dBTP")

    r = ff(["-i", v, "-vf", "blackdetect=d=0.5:pic_th=0.98", "-an", "-f", "null", "-"])
    blk = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r)
    add("sem tela preta > 0,5 s", "ok" if not blk else "falha", "; ".join(f"{s}-{e}s" for s, e in blk))

    r = ff(["-i", v, "-af", "silencedetect=noise=-38dB:d=2", "-vn", "-f", "null", "-"])
    sil = re.findall(r"silence_start: ([\d.]+)", r)
    add("sem silêncio > 2 s", "ok" if not sil else "atencao", f"início em {', '.join(sil)}s" if sil else "")

    # nada claro nos 270 px do topo (zona da interface do app); o gancho fica em y>=300
    r = ff(["-i", v, "-vf", "crop=1080:270:0:0,signalstats,metadata=print:key=lavfi.signalstats.YMAX", "-an", "-f", "null", "-"])
    ymax = [float(x) for x in re.findall(r"YMAX=([\d.]+)", r)]
    add("topo (0-270 px) livre de texto/gráfico", "ok" if not ymax or max(ymax) < 60 else "atencao", f"brilho máx. {max(ymax):.0f}" if ymax else "")

    r = ff(["-v", "error", "-i", v, "-f", "null", "-"])
    add("sem erro de decodificação", "ok" if not r.strip() else "falha", r.strip()[:200])

    ver = "REPROVADO" if any(i["estado"] == "falha" for i in items) else "APROVADO"
    out = {"video": v, "veredito": ver, "itens": items}
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if a.out:
        a.out.write_text(text, encoding="utf-8")
    print(text)
    sys.exit(0 if ver == "APROVADO" else 1)


if __name__ == "__main__":
    main()
