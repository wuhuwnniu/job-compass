#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 data/jobs/*.json 并合并成 app/data.js（离线可用的 window.JOB_DATA）"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JOBS_DIR = DATA / "jobs"
APP = ROOT / "app"

CATALOG = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
ALLOWED_IDS = [row["id"] for row in CATALOG]
CATALOG_TRACK = {row["id"]: row["track"] for row in CATALOG}

TRACKS = {
    "互联网/软件", "产品/设计", "运营/市场", "销售/商务", "职能/财务", "金融",
    "教育", "医疗/健康", "制造/工程", "传媒/内容", "公共服务/其他",
}

REQUIRED = ["id", "name", "aliases", "track", "tagline", "daily", "friendly", "majors",
            "skills", "salary", "growth", "in3to5", "learn", "adjacent", "reality"]


def fail(errors, msg):
    errors.append(msg)


def check_job(job, skill_ids, errors, fname):
    jid = job.get("id", "?")
    tag = f"{fname}:{jid}"
    for f in REQUIRED:
        if f not in job:
            fail(errors, f"{tag} 缺字段 {f}")
    if jid not in ALLOWED_IDS:
        fail(errors, f"{tag} id 不在清单里")
    if job.get("track") not in TRACKS:
        fail(errors, f"{tag} track 非法: {job.get('track')}")
    elif CATALOG_TRACK.get(jid) and job["track"] != CATALOG_TRACK[jid]:
        fail(errors, f"{tag} track 与目录不一致: {job['track']} / {CATALOG_TRACK[jid]}")
    if job.get("friendly") not in ("高", "中", "低"):
        fail(errors, f"{tag} friendly 非法")
    daily = job.get("daily") or []
    if not (3 <= len(daily) <= 8):
        fail(errors, f"{tag} daily 条数 {len(daily)}（应 5 条左右）")
    if any(len(d) > 80 for d in daily):
        fail(errors, f"{tag} daily 有过长句子（>80 字）")
    skills = job.get("skills") or []
    if not (5 <= len(skills) <= 12):
        fail(errors, f"{tag} skills 数量 {len(skills)}（应 6–10）")
    for s in skills:
        if s.get("id") not in skill_ids:
            fail(errors, f"{tag} 未知技能 id {s.get('id')}")
        if s.get("w") not in (1, 2, 3):
            fail(errors, f"{tag} 技能权重非法 {s.get('w')}")
    sal = job.get("salary") or {}
    for k in ("junior", "mid", "senior"):
        v = sal.get(k)
        if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
            fail(errors, f"{tag} salary.{k} 需要两个数字")
        elif v[0] > v[1]:
            fail(errors, f"{tag} salary.{k} 区间反了 {v}")
        elif not (0 < v[0] < 200 and 0 < v[1] <= 300):
            fail(errors, f"{tag} salary.{k} 数字离谱 {v}")
    if not sal.get("note"):
        fail(errors, f"{tag} salary.note 为空")
    learn = job.get("learn") or []
    if len(learn) != 3:
        fail(errors, f"{tag} learn 应为 3 阶段，实际 {len(learn)}")
    for st in learn:
        if not st.get("stage") or not st.get("goal") or not st.get("items"):
            fail(errors, f"{tag} learn 阶段不完整: {st.get('stage')}")
        if not (2 <= len(st.get("items", [])) <= 5):
            fail(errors, f"{tag} learn.items 条数异常: {st.get('stage')}")
    adj = job.get("adjacent") or []
    if not (2 <= len(adj) <= 5):
        fail(errors, f"{tag} adjacent 数量 {len(adj)}")
    for a in adj:
        if a not in ALLOWED_IDS:
            fail(errors, f"{tag} adjacent 未知 id {a}")
        if a == jid:
            fail(errors, f"{tag} adjacent 指向自己")
    if not job.get("majors"):
        fail(errors, f"{tag} majors 为空")
    for txt in (job.get("reality", ""), job.get("tagline", ""), job.get("in3to5", "")):
        if len(txt) < 8:
            fail(errors, f"{tag} 文本过短: {txt[:12]}")


def main():
    skills = json.loads((DATA / "skills.json").read_text(encoding="utf-8"))
    skill_ids = {s["id"] for s in skills}
    jobs, errors, seen = [], [], {}

    files = sorted(JOBS_DIR.glob("*.json"))
    if not files:
        print("没有找到 data/jobs/*.json", file=sys.stderr)
        return 1

    for f in files:
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{f.name} JSON 解析失败: {e}")
            continue
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            errors.append(f"{f.name} 不是数组")
            continue
        for job in payload:
            jid = job.get("id")
            if jid in seen:
                errors.append(f"重复岗位 id {jid}（{seen[jid]} 与 {f.name}）")
                continue
            seen[jid] = f.name
            check_job(job, skill_ids, errors, f.name)
            jobs.append(job)

    missing = [i for i in ALLOWED_IDS if i not in seen]
    if missing:
        errors.append("还缺这些岗位: " + " ".join(missing))

    if errors:
        print(f"校验失败，共 {len(errors)} 个问题：", file=sys.stderr)
        for e in errors[:80]:
            print("  -", e, file=sys.stderr)
        return 1

    order = {jid: i for i, jid in enumerate(ALLOWED_IDS)}
    jobs.sort(key=lambda j: order.get(j["id"], 999))

    # 岗位内技能按权重降序，便于展示
    for j in jobs:
        j["skills"].sort(key=lambda s: -s["w"])

    out = {"skills": skills, "jobs": jobs, "meta": {"count": len(jobs), "builtAt": None}}
    (APP / "data.js").write_text(
        "window.JOB_DATA = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    tracks = {}
    for j in jobs:
        tracks[j["track"]] = tracks.get(j["track"], 0) + 1
    print(f"OK  {len(jobs)} 个岗位, {len(skills)} 项技能")
    for t, n in sorted(tracks.items(), key=lambda x: -x[1]):
        print(f"    {t}: {n}")
    size = (APP / "data.js").stat().st_size / 1024
    print(f"    app/data.js {size:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
