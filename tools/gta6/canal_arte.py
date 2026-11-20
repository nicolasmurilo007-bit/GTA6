#!/usr/bin/env python3
"""Gera a foto de perfil (800x800) e o banner (2560x1440) do canal "shorts gta6".

Arte original (sem logo da Rockstar/Twitch): pôr do sol retrô estilo Vice City, sol com faixas,
palmeiras em silhueta, grade de neon e letreiro. Saída em assets/canal/.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parents[2] / "assets" / "canal"
BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
COND = "/usr/share/fonts/opentype/inter/Inter-ExtraBoldItalic.otf"

TOP = (18, 6, 40)       # roxo quase preto
MID = (120, 20, 110)    # magenta escuro
LOW = (255, 92, 92)     # coral
SUN_A = (255, 214, 77)  # amarelo
SUN_B = (255, 60, 140)  # rosa
NEON = (0, 229, 255)    # ciano


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky(w, h, horizon):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = min(y / horizon, 1.0)
        c = lerp(TOP, MID, t / 0.6) if t < 0.6 else lerp(MID, LOW, (t - 0.6) / 0.4)
        if y > horizon:
            c = lerp((40, 8, 60), (10, 2, 20), (y - horizon) / max(h - horizon, 1))
        for x in range(w):
            px[x, y] = c
    return img


def sun(img, cx, cy, r):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(int(cy - r), int(cy + 1)):
        t = (y - (cy - r)) / r
        half = math.sqrt(max(r * r - (y - cy) ** 2, 0))
        col = lerp(SUN_A, SUN_B, t)
        # faixas horizontais na metade de baixo do sol (estilo retrô)
        band = int(t * 9)
        if t > 0.45 and (y // max(int(r * 0.06), 2)) % 2 == 0:
            continue
        d.line([(cx - half, y), (cx + half, y)], fill=col + (255,))
    glow = layer.filter(ImageFilter.GaussianBlur(r * 0.12))
    img.paste(glow, (0, 0), glow)
    img.paste(layer, (0, 0), layer)


def grid(img, horizon, color=NEON):
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(1, 14):
        y = horizon + (h - horizon) * (i / 13) ** 2
        d.line([(0, y), (w, y)], fill=color + (120,), width=max(w // 900, 2))
    for k in range(-16, 17):
        x0 = w / 2 + k * w / 30
        x1 = w / 2 + k * w / 6
        d.line([(x0, horizon), (x1, h)], fill=color + (110,), width=max(w // 900, 2))
    img.paste(layer, (0, 0), layer)


def palm(d, x, base, height, flip=1, color=(10, 2, 18)):
    # tronco curvo
    pts = []
    for i in range(21):
        t = i / 20
        pts.append((x + flip * height * 0.18 * math.sin(t * 1.4), base - height * t))
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=color, width=max(int(height * 0.045 * (1.2 - 0.5 * (pts.index(a) / 20))), 3))
    tx, ty = pts[-1]
    # folhas
    for ang in (-170, -140, -110, -70, -40, -10, 200):
        a = math.radians(ang)
        L = height * 0.42
        tip = (tx + L * math.cos(a) * flip, ty + L * math.sin(a) * 0.55 + L * 0.25)
        mid = (tx + L * 0.5 * math.cos(a) * flip, ty + L * 0.5 * math.sin(a) * 0.55 - L * 0.05)
        d.polygon([(tx, ty), mid, tip, (mid[0], mid[1] + L * 0.09)], fill=color)


def text_center(d, xy, s, font, fill, stroke, sw):
    d.text(xy, s, font=font, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=stroke)


def neon_text(img, xy, s, font, fill=(255, 255, 255), glow=SUN_B, sw=0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, s, font=font, fill=glow + (255,), anchor="mm", stroke_width=sw + 8, stroke_fill=glow + (255,))
    layer = layer.filter(ImageFilter.GaussianBlur(14))
    img.paste(layer, (0, 0), layer)
    ImageDraw.Draw(img).text(xy, s, font=font, fill=fill, anchor="mm", stroke_width=sw, stroke_fill=(20, 4, 30))


def perfil():
    S = 800
    horizon = int(S * 0.62)
    img = sky(S, S, horizon).convert("RGBA")
    sun(img, S / 2, horizon, S * 0.30)
    grid(img, horizon)
    d = ImageDraw.Draw(img)
    palm(d, S * 0.16, horizon + 10, S * 0.50, flip=1)
    palm(d, S * 0.86, horizon + 10, S * 0.42, flip=-1)
    neon_text(img, (S / 2, S * 0.27), "GTA 6", ImageFont.truetype(COND, 190), sw=6)
    neon_text(img, (S / 2, S * 0.80), "SHORTS", ImageFont.truetype(BOLD, 104), fill=SUN_A, glow=NEON, sw=5)
    img.convert("RGB").save(OUT / "perfil.png")


def banner():
    W, H = 2560, 1440
    horizon = int(H * 0.60)
    img = sky(W, H, horizon).convert("RGBA")
    sun(img, W / 2, horizon, 330)
    grid(img, horizon)
    d = ImageDraw.Draw(img)
    for x, hgt, f in ((520, 640, 1), (700, 470, 1), (2040, 620, -1), (1880, 430, -1), (260, 520, 1), (2300, 540, -1)):
        palm(d, x, horizon + 20, hgt, flip=f)
    # área segura de todos os aparelhos: 1546x423 no centro (x 507-2053, y 508-931)
    cy = H / 2
    neon_text(img, (W / 2, cy - 55), "SHORTS GTA 6", ImageFont.truetype(COND, 200), sw=7)
    neon_text(img, (W / 2, cy + 120), "OS MELHORES MOMENTOS DAS LIVES  •  TODO DIA", ImageFont.truetype(BOLD, 54),
              fill=SUN_A, glow=NEON, sw=3)
    img.convert("RGB").save(OUT / "banner.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    perfil()
    banner()
    print(OUT / "perfil.png", OUT / "banner.png")
