#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成应用图标（PWA / 桌面快捷方式）"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "app" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

BG = (31, 27, 23, 255)        # 墨色
CREAM = (247, 244, 238, 255)
ACCENT = (216, 122, 61, 255)  # 暖橙
SOFT = (122, 113, 104, 255)


def draw_icon(size: int, pad_ratio: float = 0.0) -> Image.Image:
    """画一个罗盘：外圈 + 指针。pad_ratio 用于 maskable 安全区（内容缩进）。"""
    ss = 4  # 超采样
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r = S * (0.5 - pad_ratio)
    cx = cy = S / 2
    d.rounded_rectangle([cx - r, cy - r, cx + r, cy + r], radius=r * 0.42, fill=BG)

    ring = r * 0.62
    lw = max(2, int(r * 0.055))
    d.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], outline=CREAM, width=lw)
    for a in (0, 90, 180, 270):
        # 刻度
        import math
        rad = math.radians(a)
        x1, y1 = cx + math.cos(rad) * ring * 0.86, cy + math.sin(rad) * ring * 0.86
        x2, y2 = cx + math.cos(rad) * ring * 1.06, cy + math.sin(rad) * ring * 1.06
        d.line([x1, y1, x2, y2], fill=CREAM, width=max(2, lw // 2))

    # 指针（上橙下灰）
    nr = ring * 0.66
    d.polygon([(cx, cy - nr), (cx + nr * 0.34, cy), (cx - nr * 0.34, cy)], fill=ACCENT)
    d.polygon([(cx, cy + nr), (cx + nr * 0.34, cy), (cx - nr * 0.34, cy)], fill=SOFT)
    d.ellipse([cx - r * 0.06, cy - r * 0.06, cx + r * 0.06, cy + r * 0.06], fill=CREAM)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    for size in (192, 512):
        draw_icon(size).save(OUT / f"icon-{size}.png")
    # maskable：内容缩进到 80% 安全区，背景铺满
    for size in (512,):
        base = Image.new("RGBA", (size, size), BG)
        inner = draw_icon(int(size * 0.72), pad_ratio=0.0).resize((int(size * 0.72),) * 2, Image.LANCZOS)
        # 去掉内层自带的圆角背景，只保留图案：重新画一版透明底
        pad = (size - inner.size[0]) // 2
        base.paste(inner, (pad, pad))
        base.save(OUT / f"icon-maskable-{size}.png")
    # 小尺寸 favicon
    draw_icon(64).save(OUT / "icon-64.png")
    print("icons:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
