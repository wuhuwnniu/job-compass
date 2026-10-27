#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把《中华人民共和国职业分类大典（2022年版）》整理成 app/dadian.js

数据来源：GitHub leo4stone/ZHONGHUARENMINGONGHEGUOZHIYEFENLEIDADIAN
（MIT，整理自人社部《职业分类大典（2022年版）社会公示稿》），文件已下载到
data/external/dadian2022_flattened.json。

产出结构：
  window.DADIAN = {
    list: [{ c: 编码, n: 名称, d: 官方描述, w: [工种], big: 大类, mid: 中类, small: 小类, tag: 'S'|'L'|'' }],
    map: { 岗位id: [大典编码, ...] },
    cats: [{ code, name, count }]
  }
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "external" / "dadian2022_flattened.json"
APP = ROOT / "app"

# 60 个岗位 → 大典条目。第一个是主对应，其余是相近的。
# 说明：互联网行业的岗位命名（产品经理、运营、前端）在大典里往往没有同名条目，
# 这里给的是「最接近」的国家分类，界面上会如实标注。
JOB_MAP = {
    "fe-dev": ["4-04-05-01"],
    "be-dev": ["4-04-05-01", "2-02-10-05"],
    "mobile-dev": ["4-04-05-01"],
    "qa-test": ["4-04-05-02"],
    "ops-cloud": ["2-02-10-08", "2-02-38-04"],
    "data-analyst": ["2-02-30-09", "4-07-02-05"],
    "ml-engineer": ["2-02-38-01", "4-04-05-05"],
    "security-eng": ["4-04-04-02", "4-04-04-06"],
    "tech-support": ["2-02-10-08", "2-02-10-05"],
    "product-manager": ["2-02-10-05", "2-06-07-13"],
    "ui-designer": ["2-09-06-07", "4-08-08-08"],
    "ux-designer": ["2-09-06-07", "2-02-10-05"],
    "user-researcher": ["2-02-30-09", "3-01-01-03"],
    "game-planner": ["4-08-08-29", "4-14-05-06"],
    "content-ops": ["2-10-02-05", "4-13-01-05"],
    "newmedia-ops": ["4-13-01-05", "4-01-06-02"],
    "user-ops": ["4-07-02-03", "4-13-01-05"],
    "marketing-specialist": ["2-06-07-02", "4-01-02-01"],
    "brand-pr": ["3-01-02-03", "2-06-07-02"],
    "ecommerce-ops": ["4-01-06-01", "4-01-06-02"],
    "growth-marketer": ["4-01-06-02", "4-01-01-00"],
    "event-planner": ["2-06-07-05", "4-07-07-01"],
    "b2b-sales": ["4-01-02-01", "4-01-01-00"],
    "bd-specialist": ["2-06-07-01", "4-01-02-01"],
    "presales": ["2-02-10-05", "4-01-02-01"],
    "customer-success": ["4-07-02-03", "4-01-02-01"],
    "hr-specialist": ["2-06-08-01", "4-07-03-04"],
    "accountant": ["2-06-03-00"],
    "fpa-analyst": ["2-06-03-00", "2-06-02-00"],
    "legal-assistant": ["2-07-08-00"],
    "admin": ["3-01-01-01", "3-01-02-01"],
    "procurement": ["4-01-01-00", "2-02-30-11"],
    "auditor": ["2-06-04-00"],
    "bank-teller": ["4-05-01-01", "4-05-01-03"],
    "research-assistant": ["2-06-11-03", "2-06-11-07"],
    "insurance-advisor": ["4-05-03-01", "2-06-10-02"],
    "credit-risk": ["4-05-01-02", "2-06-09-04"],
    "teacher": ["2-08-02-01", "2-08-02-04"],
    "trainer": ["4-07-03-05", "2-08-02-03"],
    "curriculum-designer": ["2-01-04-01", "2-06-08-04"],
    "study-abroad": ["4-07-03-01", "2-06-08-02"],
    "nurse": ["2-05-08-01", "2-05-08-04"],
    "pharmacist": ["2-05-06-01", "2-05-06-02"],
    "medical-device-sales": ["4-01-05-02", "2-06-07-07"],
    "health-manager": ["4-14-02-02", "2-05-05-02"],
    "medical-editor": ["2-10-02-01", "2-10-02-03"],
    "mechanical-design": ["2-02-07-01", "2-02-07-06"],
    "electrical-eng": ["2-02-11-01", "2-02-12-02"],
    "process-eng": ["2-02-07-02", "2-02-07-08"],
    "quality-eng": ["2-02-29-03", "2-02-31-01"],
    "journalist": ["2-10-01-01", "2-10-01-02"],
    "video-director": ["2-09-03-05", "2-09-03-06"],
    "photographer": ["2-09-03-03", "4-13-02-09"],
    "graphic-designer": ["2-09-06-01", "4-08-08-06"],
    "translator": ["2-10-05-01"],
    "civil-servant": ["3-01-01-01", "1-02-02-00"],
    "social-worker": ["2-07-10-01", "3-01-04-01"],
    "realtor": ["4-06-02-01"],
    "hotel-mgmt": ["4-03-01-03", "4-07-04-01"],
    "headhunter": ["2-06-08-02", "2-06-08-01"],

    # ---- 新增的 90 个岗位（多数是「最接近」的国家分类）----
    "devops-eng": ["2-02-10-08", "2-02-38-04"],
    "dba": ["4-04-05-04", "2-02-38-03"],
    "embedded-eng": ["2-02-10-06"],
    "game-client": ["4-04-05-01", "4-08-08-29"],
    "it-support": ["2-02-10-08", "4-04-04-05"],
    "qa-automation": ["4-04-05-02"],
    "data-engineer": ["2-02-38-03", "2-02-30-09"],
    "ai-app-engineer": ["2-02-38-01", "4-04-05-05"],
    "tech-writer": ["2-10-02-03", "2-10-02-01"],
    "mini-program": ["4-04-05-01"],
    "product-ops": ["2-06-07-13", "4-13-01-05"],
    "visual-designer": ["2-09-06-01", "4-08-08-08"],
    "illustrator": ["2-09-06-01", "4-08-08-05"],
    "animator": ["2-09-06-03", "4-13-02-02"],
    "interior-designer": ["4-08-08-07"],
    "industrial-designer": ["2-02-34-02", "4-08-08-26"],
    "packaging-designer": ["4-08-08-09"],
    "video-editor": ["2-09-03-06", "4-13-02-09"],
    "game-artist": ["2-09-06-07", "4-13-02-02"],
    "exhibition-designer": ["4-08-08-21", "2-10-08-05"],
    "community-ops": ["4-07-02-03", "4-13-01-05"],
    "live-ops": ["4-01-06-02", "4-13-01-05"],
    "ecommerce-cs": ["4-07-02-03"],
    "seo-specialist": ["4-01-06-02", "2-06-07-02"],
    "channel-sales": ["4-01-02-01", "2-06-07-02"],
    "merchandiser": ["4-01-01-00", "4-01-06-01"],
    "market-researcher": ["2-06-07-02", "3-01-01-03"],
    "copywriter": ["2-06-07-03", "2-10-02-01"],
    "event-exec": ["4-07-07-01", "2-06-07-05"],
    "franchise-sales": ["4-01-02-01", "2-06-07-01"],
    "foreign-trade-sales": ["2-06-07-01", "4-01-02-01"],
    "foreign-trade-merchandiser": ["2-06-07-01", "4-02-05-03"],
    "freight-forwarder": ["4-02-05-03"],
    "customer-service": ["4-07-02-03"],
    "retail-sales": ["4-01-02-03", "4-01-02-01"],
    "telemarketing": ["4-01-02-01"],
    "bidding-specialist": ["2-06-07-15", "4-01-01-00"],
    "cashier": ["2-06-03-00", "3-01-01-01"],
    "tax-specialist": ["2-06-05-00", "2-06-03-00"],
    "compensation-hr": ["2-06-08-01", "4-07-03-04"],
    "recruiter": ["4-07-03-07", "2-06-08-01"],
    "compliance": ["2-06-07-14", "2-07-08-00"],
    "board-secretary": ["3-01-02-02", "2-06-11-02"],
    "archivist": ["2-10-07-00", "4-13-01-07"],
    "receptionist": ["3-01-01-01", "4-07-02-03"],
    "internal-control": ["2-06-04-00", "2-06-07-14"],
    "wealth-manager": ["4-05-01-03", "2-06-11-03"],
    "fund-ops": ["2-06-11-07", "2-06-11-02"],
    "ib-analyst": ["2-06-11-01", "2-06-11-03"],
    "claims-adjuster": ["2-06-10-03", "2-06-10-02"],
    "kindergarten-teacher": ["2-08-03-00"],
    "special-ed-teacher": ["2-08-04-00"],
    "college-counselor": ["2-08-01-01", "4-13-04-02"],
    "tutor": ["2-08-02-03", "2-08-02-04"],
    "exam-trainer": ["4-07-03-05", "2-08-02-01"],
    "pe-coach": ["2-09-07-01", "2-08-02-03"],
    "art-teacher": ["2-08-02-03", "2-09-06-06"],
    "edu-consultant": ["4-07-03-01", "2-06-08-02"],
    "scriptwriter": ["2-09-01-06", "2-09-03-01"],
    "voice-actor": ["2-10-04-01", "2-10-04-02"],
    "streamer": ["4-01-06-02", "4-13-01-05"],
    "film-post": ["2-09-03-06", "2-09-03-05"],
    "proofreader": ["2-10-03-00", "2-10-02-01"],
    "clinician": ["2-05-01-01", "2-05-01-02"],
    "dentist": ["2-05-01-07", "2-05-07-02"],
    "lab-technician": ["2-05-07-04", "2-05-07-05"],
    "rehab-therapist": ["4-14-03-07", "2-05-01-12"],
    "psych-counselor": ["2-07-10-03", "2-01-04-02"],
    "dietitian": ["4-14-02-01", "2-05-07-08"],
    "veterinarian": ["2-03-06-01", "2-03-06-03"],
    "elder-care": ["4-10-01-05", "4-10-01-01"],
    "pharma-rep": ["2-06-07-07", "4-01-05-02"],
    "imaging-tech": ["2-05-07-01"],
    "police-officer": ["3-02-01-00"],
    "firefighter": ["3-02-03-01", "2-02-28-02"],
    "courier": ["4-02-07-08", "4-02-07-11"],
    "delivery-rider": ["4-10-08-01"],
    "ride-hailing-driver": ["4-02-02-01", "4-02-02-03"],
    "tour-guide": ["4-07-04-01", "4-07-04-02"],
    "chef": ["4-03-02-01", "4-03-02-03"],
    "mold-design": ["2-02-07-06", "2-02-07-13"],
    "cnc-programmer": ["6-18-01-07", "2-02-07-02"],
    "welding-eng": ["2-02-07-09"],
    "equipment-maintenance": ["2-02-07-04", "6-31-01-03"],
    "pmc-planner": ["2-02-30-11", "2-02-07-02"],
    "safety-officer": ["2-02-28-03", "2-02-28-02"],
    "construction-supervisor": ["2-02-18-02", "6-29-01-06"],
    "cost-engineer": ["2-02-30-10"],
    "architect-designer": ["2-02-18-01", "4-08-08-22"],
    "surveyor": ["2-02-02-02", "4-08-03-04"],
}

TAG_RE = re.compile(r"(L/S|S|L)$")


def clean(text: str) -> str:
    text = text.replace("\u3000", " ").replace("，", "，")
    text = re.sub(r"(?<=[\u4e00-\u9fa5，。、；：（）]) +", "", text)
    text = re.sub(r" +(?=[\u4e00-\u9fa5，。、；：（）])", "", text)
    return text.strip()


def main() -> int:
    raw = json.loads(SRC.read_text(encoding="utf-8"))
    by_code = {x["sn"]: x for x in raw}

    def name_of(code: str):
        x = by_code.get(code)
        return x["name"] if x else None

    occ = [x for x in raw if len(x["sn"].split("-")) == 4]
    out = []
    for x in occ:
        sn = x["sn"]
        parts = sn.split("-")
        big = name_of(parts[0])
        mid = name_of("-".join(parts[:2]))
        small = name_of("-".join(parts[:3]))
        name = x["name"]
        tag = ""
        m = TAG_RE.search(name)
        if m:
            tag = m.group(1)
            name = name[: -len(m.group(1))]
        item = {
            "c": sn,
            "n": name.strip(),
            "d": clean(x.get("desc", "")),
            "big": big or "",
            "mid": mid or "",
            "small": small or "",
        }
        if tag:
            item["tag"] = tag
        wt = x.get("worktypes") or []
        if wt:
            item["w"] = wt
        out.append(item)

    codes = {x["c"] for x in out}
    bad = []
    for jid, cs in JOB_MAP.items():
        for c in cs:
            if c not in codes:
                bad.append((jid, c))
    if bad:
        print("映射里出现了不存在的大典编码：", bad)
        return 1

    cats = []
    for x in raw:
        if len(x["sn"].split("-")) == 1:
            n = sum(1 for o in out if o["c"].startswith(x["sn"] + "-"))
            cats.append({"code": x["sn"], "name": x["name"], "count": n})

    payload = {"list": out, "map": JOB_MAP, "cats": cats}
    (APP / "dadian.js").write_text(
        "window.DADIAN = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    size = (APP / "dadian.js").stat().st_size / 1024
    print(f"OK  {len(out)} 个职业, {len(cats)} 个大类, {len(JOB_MAP)} 个岗位映射")
    print(f"    app/dadian.js {size:.0f} KB")
    for c in cats:
        print(f"    {c['code']} {c['name']} ({c['count']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
