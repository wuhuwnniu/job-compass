#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""不用 Gradle，直接用 Android SDK 的 aapt2 / d8 / zipalign / apksigner 打一个 APK。

前置：tools/jdk17（JDK 17+）、tools/android-sdk（含 platforms/android-34、build-tools/*）。
运行：
    python scripts/build_apk.py
产物：
    dist/岗位罗盘.apk
"""
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID = ROOT / "android"
APP_SRC = ROOT / "app"
BUILD = ROOT / "build" / "apk"
DIST = ROOT / "dist"
TOOLS = ROOT / "tools"

PKG = "com.jobcompass.app"
OUT_NAME = "岗位罗盘.apk"


def find_java_home() -> Path:
    candidates = [TOOLS / "jdk"]
    for c in candidates:
        if (c / "bin" / "javac.exe").exists():
            return c
    jh = os.environ.get("JAVA_HOME")
    if jh and (Path(jh) / "bin" / "javac.exe").exists():
        return Path(jh)
    raise SystemExit("找不到 JDK：请解压到 tools/jdk 或设置 JAVA_HOME")


def find_sdk() -> Path:
    for c in [TOOLS / "android-sdk"]:
        if (c / "platform-tools").exists() or (c / "build-tools").exists():
            return c
    raise SystemExit("找不到 Android SDK：请放到 tools/android-sdk")


def newest(dir_path: Path) -> Path:
    items = sorted([p for p in dir_path.iterdir() if p.is_dir()])
    if not items:
        raise SystemExit(f"{dir_path} 为空")
    return items[-1]


def run(cmd, cwd=None):
    print("  $", " ".join(str(c) for c in cmd[:4]), "..." if len(cmd) > 4 else "")
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=ENV)
    if p.returncode != 0:
        print(p.stdout[-4000:])
        print(p.stderr[-4000:], file=sys.stderr)
        raise SystemExit(f"命令失败：{cmd[0]}")
    return p.stdout


ENV = dict(os.environ)


def prepare_assets():
    assets = BUILD / "assets"
    if assets.exists():
        shutil.rmtree(assets)
    assets.mkdir(parents=True)
    for item in APP_SRC.iterdir():
        if item.name.startswith("_"):
            continue
        dst = assets / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    # APK 里不需要 Service Worker / manifest（file:// 下用不到）
    for junk in ("sw.js", "manifest.webmanifest"):
        p = assets / junk
        if p.exists():
            p.unlink()
    html = (assets / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", html)
    (assets / "index.html").write_text(html, encoding="utf-8")
    total = sum(f.stat().st_size for f in assets.rglob("*") if f.is_file())
    print(f"    assets: {len(list(assets.rglob('*')))} 项, {total/1024/1024:.1f} MB")


def main() -> int:
    java_home = find_java_home()
    sdk = find_sdk()
    build_tools = newest(sdk / "build-tools")
    platform = newest(sdk / "platforms")
    android_jar = platform / "android.jar"
    if not android_jar.exists():
        raise SystemExit(f"缺少 {android_jar}")

    env_java = java_home / "bin"
    ENV["JAVA_HOME"] = str(java_home)
    ENV["PATH"] = str(env_java) + os.pathsep + ENV.get("PATH", "")
    print(f"JDK      {java_home}")
    print(f"build-tools {build_tools.name}")
    print(f"platform  {platform.name}")

    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)

    print("[1/6] 准备 assets")
    prepare_assets()

    print("[2/6] aapt2 compile")
    res_zip = BUILD / "res.zip"
    run([str(build_tools / "aapt2.exe"), "compile", "--dir", str(ANDROID / "res"), "-o", str(res_zip)])

    print("[3/6] aapt2 link（含 assets）")
    gen = BUILD / "gen"
    gen.mkdir()
    unsigned = BUILD / "unsigned.apk"
    run([
        str(build_tools / "aapt2.exe"), "link",
        "-o", str(unsigned),
        "-I", str(android_jar),
        "--manifest", str(ANDROID / "AndroidManifest.xml"),
        "-A", str(BUILD / "assets"),
        "--java", str(gen),
        "--auto-add-overlay",
        str(res_zip),
    ])

    print("[4/6] javac + d8")
    classes = BUILD / "classes"
    classes.mkdir()
    java_files = [str(p) for p in (ANDROID / "java").rglob("*.java")] + [str(p) for p in gen.rglob("*.java")]
    run([str(env_java / "javac.exe"), "-source", "1.8", "-target", "1.8",
         "-encoding", "utf-8", "-nowarn",
         "-classpath", str(android_jar), "-d", str(classes)] + java_files)
    dex_out = BUILD / "dex"
    dex_out.mkdir()
    run([str(env_java / "java.exe"), "-cp", str(build_tools / "lib" / "d8.jar"),
         "com.android.tools.r8.D8", "--lib", str(android_jar),
         "--min-api", "21", "--output", str(dex_out)] +
        [str(p) for p in classes.rglob("*.class")])

    print("[5/6] 打包 classes.dex + 对齐")
    with zipfile.ZipFile(unsigned, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(dex_out / "classes.dex", "classes.dex")
    aligned = BUILD / "aligned.apk"
    run([str(build_tools / "zipalign.exe"), "-f", "4", str(unsigned), str(aligned)])

    print("[6/6] 签名")
    keystore = TOOLS / "jobcompass.keystore"
    if not keystore.exists():
        run([str(env_java / "keytool.exe"), "-genkeypair", "-v",
             "-keystore", str(keystore), "-alias", "jobcompass",
             "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
             "-storepass", "jobcompass", "-keypass", "jobcompass",
             "-dname", "CN=Job Compass, OU=App, O=JobCompass, L=Local, C=CN"])
    DIST.mkdir(exist_ok=True)
    out = DIST / OUT_NAME
    run([str(build_tools / "apksigner.bat"), "sign",
         "--ks", str(keystore), "--ks-pass", "pass:jobcompass",
         "--key-pass", "pass:jobcompass", "--ks-key-alias", "jobcompass",
         "--out", str(out), str(aligned)])
    run([str(build_tools / "apksigner.bat"), "verify", "--verbose", str(out)])

    size = out.stat().st_size / 1024 / 1024
    print(f"\nOK  {out}  ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
