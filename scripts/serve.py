#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在本机起一个静态服务，让手机连同一个 Wi-Fi 就能打开「岗位罗盘」。

用法：
    python scripts/serve.py            # 默认 8765 端口
    python scripts/serve.py -p 9000    # 换端口
    python scripts/serve.py --open     # 顺便在电脑浏览器打开
"""
import argparse
import http.server
import os
import socket
import socketserver
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def end_headers(self):
        # 开发期别让浏览器 / Service Worker 缓存住旧文件
        if self.path.endswith((".html", ".js", ".css", ".webmanifest")) or self.path == "/":
            self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Service-Worker-Allowed", "/")
        super().end_headers()

    def log_message(self, fmt, *args):
        if str(args[1] if len(args) > 1 else "")[:1] not in ("2", "3"):
            sys.stderr.write("  %s\n" % (fmt % args))


def lan_ips():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.add(ip)
    except OSError:
        pass
    return sorted(ips)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    if not (APP_DIR / "data.js").exists():
        print("还没生成 app/data.js，先运行：python scripts/build_data.py", file=sys.stderr)
        return 1

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", args.port), Handler) as httpd:
        print("\n  岗位罗盘已启动\n")
        print(f"  本机：  http://localhost:{args.port}/")
        for ip in lan_ips():
            print(f"  手机：  http://{ip}:{args.port}/    （手机和电脑连同一个 Wi-Fi）")
        print("\n  手机上打开后，用浏览器菜单里的「添加到主屏幕 / 添加到桌面」，"
              "之后就能像 App 一样离线打开。\n")
        print("  Ctrl+C 停止。\n")
        if args.open:
            webbrowser.open(f"http://localhost:{args.port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  已停止。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
