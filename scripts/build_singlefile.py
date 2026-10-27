#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 app/ 打包成一个可以双击打开的单文件 HTML（放进 dist/）。

手机上也可以直接把这个 html 存到本地用浏览器打开（不依赖网络）。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
DIST = ROOT / "dist"
OUT_NAME = "岗位罗盘.html"


def main() -> int:
    html = (APP / "index.html").read_text(encoding="utf-8")
    css = (APP / "styles.css").read_text(encoding="utf-8")
    data = (APP / "data.js").read_text(encoding="utf-8")
    dadian = (APP / "dadian.js").read_text(encoding="utf-8")
    js = (APP / "app.js").read_text(encoding="utf-8")

    if not (APP / "data.js").exists():
        print("缺少 app/data.js，先跑 scripts/build_data.py")
        return 1
    if not (APP / "dadian.js").exists():
        print("缺少 app/dadian.js，先跑 scripts/build_dadian.py")
        return 1

    # 去掉 PWA 相关引用（file:// 下用不到，single-file 也没有独立文件）
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="icon"[^>]*>', "", html)
    html = html.replace(
        '<link rel="stylesheet" href="styles.css">',
        "<style>\n" + css + "\n</style>",
    )
    html = html.replace(
        '<script src="data.js"></script>',
        "<script>\n" + data + "\n</script>",
    )
    html = html.replace(
        '<script src="dadian.js"></script>',
        "<script>\n" + dadian + "\n</script>",
    )
    html = html.replace(
        '<script src="app.js"></script>',
        "<script>\n" + js + "\n</script>",
    )

    if "styles.css" in html or 'src="app.js"' in html or 'src="data.js"' in html or 'src="dadian.js"' in html:
        print("内联不完整，检查 index.html 的引用写法")
        return 1

    DIST.mkdir(exist_ok=True)
    out = DIST / OUT_NAME
    out.write_text(html, encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"OK  {out}  ({kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
