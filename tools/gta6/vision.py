#!/usr/bin/env python3
"""Visão para posicionar efeitos (círculos, setas) sem chute.

Comandos (todos leem o mesmo JSON do `render_video.py`):
  faces  --times 10,35        rostos no quadro FINAL 1080x1920 (centro e caixa)
  arrow  --t 34.8             sugere o bloco `annotations` de uma seta apontando para o rosto
  grid   --times 10.6,35      quadros finais com GRADE de coordenadas (para ler x/y de objetos)
  check  --video out.mp4      quadros do vídeo renderizado nos instantes das marcações

Rodar (OpenCV < 5 tem a API do detector):
  uv run --no-project --python 3.11 --with "opencv-python-headless<5" --with numpy \\
      python tools/gta6/vision.py faces --config tools/gta6/exemplo_corte.json \\
      --workdir <pasta> --times 10,35

Vale para fonte única com `crop` (corte de live). O mapeamento é o mesmo do render
(escala = 1080/largura do recorte; sobras pretas em cima e embaixo).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

W, H = 1080, 1920
MODEL = Path(__file__).resolve().parents[2] / "assets" / "models" / "yunet.onnx"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def source(cfg: dict, workdir: Path) -> dict:
    name = next(iter(cfg["sources"]))
    v = cfg["sources"][name]
    path = workdir / (v["path"] if isinstance(v, dict) else v)
    crop = v.get("crop") if isinstance(v, dict) else None
    if crop:
        crop = [int(c) - (int(c) % 2) for c in crop]
    else:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)]
        ).decode().strip().split(",")
        crop = [0, 0, int(out[0]), int(out[1])]
    scale = W / crop[2]
    fg_h = int(round(W * crop[3] / crop[2] / 2)) * 2
    return {"path": path, "crop": crop, "scale": scale, "fg_h": fg_h, "bar": (H - fg_h) // 2}


def grab(src: dict, t: float, out_png: Path) -> None:
    x, y, w, h = src["crop"]
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t}", "-i", str(src["path"]), "-frames:v", "1", "-vf", f"crop={w}:{h}:{x}:{y}", str(out_png)],
        check=True,
    )


def detect_faces(img_path: Path) -> list[list[float]]:
    import cv2

    img = cv2.imread(str(img_path))
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), 0.6, 0.3, 5000)
    _, faces = det.detect(img)
    return [] if faces is None else [[float(v) for v in f[:4]] + [float(f[-1])] for f in faces]


def to_canvas(box: list[float], src: dict) -> dict:
    s, bar = src["scale"], src["bar"]
    x, y, w, h = box[0] * s, bar + box[1] * s, box[2] * s, box[3] * s
    return {"x": round(x), "y": round(y), "w": round(w), "h": round(h), "cx": round(x + w / 2), "cy": round(y + h / 2)}


def faces_at(src: dict, t: float, tmp: Path) -> dict | None:
    png = tmp / f"_face_{t}.png"
    grab(src, t, png)
    found = sorted(detect_faces(png), key=lambda f: f[2] * f[3], reverse=True)
    return None if not found else {"t": t, "score": round(found[0][4], 2), **to_canvas(found[0], src)}


def suggest_arrow(face: dict, t: float, dur: float = 2.8) -> dict:
    """Seta vinda de cima, do lado com mais espaço, com a ponta na lateral do rosto."""
    import math

    fw = face["w"]
    for ang in (225, 315):  # 225: aponta p/ baixo-esquerda (vem da direita); 315: p/ baixo-direita (vem da esquerda)
        dx, dy = math.cos(math.radians(ang)), -math.sin(math.radians(ang))
        side = 1 if ang == 225 else -1
        tipx, tipy = face["cx"] + side * (fw / 2 + 28), face["cy"] - face["h"] * 0.35
        tailx, taily = tipx - 215 * dx, tipy - 215 * dy
        if 20 < tailx < W - 20 and taily > 20:
            return {"type": "arrow", "t": t, "dur": dur, "x": round(tipx), "y": round(tipy), "angle": ang}
    return {"type": "arrow", "t": t, "dur": dur, "x": face["cx"], "y": face["y"] - 30, "angle": 270}


def grid_filter(src: dict) -> str:
    x, y, w, h = src["crop"]
    f = [f"crop={w}:{h}:{x}:{y}", f"scale={W}:{src['fg_h']}:flags=lanczos", f"pad={W}:{H}:0:{src['bar']}:color=black"]
    f.append("drawgrid=width=100:height=100:thickness=1:color=white@0.35")
    for gx in range(0, W, 100):
        f.append(f"drawtext=fontfile={FONT}:text='{gx}':x={gx + 3}:y=4:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6")
    for gx in range(0, W, 100):  # segunda linha de x, logo abaixo do topo da câmera (fácil de ler sobre a imagem)
        f.append(f"drawtext=fontfile={FONT}:text='{gx}':x={gx + 3}:y={src['bar'] + 8}:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6")
    for gy in range(100, H, 100):
        f.append(f"drawtext=fontfile={FONT}:text='{gy}':x=3:y={gy + 3}:fontsize=26:fontcolor=cyan:box=1:boxcolor=black@0.6")
    return ",".join(f)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["faces", "arrow", "grid", "check"])
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--times", default="")
    ap.add_argument("--t", type=float)
    ap.add_argument("--video", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text(encoding="utf-8"))
    wd = a.workdir.resolve()
    out = (a.out or wd / "vision").resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = source(cfg, wd)
    times = [float(x) for x in a.times.split(",") if x]

    if a.cmd == "faces":
        print(json.dumps([faces_at(src, t, out) for t in times], ensure_ascii=False, indent=2))
    elif a.cmd == "arrow":
        face = faces_at(src, a.t, out)
        if not face:
            raise SystemExit(f"nenhum rosto em t={a.t}s")
        print(json.dumps(suggest_arrow(face, a.t), ensure_ascii=False))
    elif a.cmd == "grid":
        for t in times:
            png = out / f"grid_{t}.png"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t}", "-i", str(src["path"]), "-frames:v", "1", "-vf", grid_filter(src), str(png)], check=True)
            print(png)
    elif a.cmd == "check":
        if not a.video:
            raise SystemExit("--video é obrigatório em check")
        for i, m in enumerate(cfg.get("annotations", [])):
            png = out / f"check_{i}_{m['type']}_{m['t']}.png"
            tt = float(m["t"]) + 0.7
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{tt}", "-i", str(a.video), "-frames:v", "1", "-vf", "scale=540:960", str(png)], check=True)
            print(png)


if __name__ == "__main__":
    main()
