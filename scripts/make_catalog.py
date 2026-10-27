#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扩充技能词表 + 生成岗位总目录（catalog.json）+ 刷新 data/_SCHEMA.md

跑一次即可；后续加岗位只改 NEW_JOBS 再跑。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ---------------- 新增技能（36 项） ----------------
NEW_SKILLS = [
    ("embedded", "嵌入式开发", "技术", "在单片机上写 C，驱动传感器和外设"),
    ("networking", "网络与弱电", "技术", "布线、交换路由配置，排查断网和延迟"),
    ("illustration", "手绘与插画", "设计", "用笔或绘图板画出原创图像与角色"),
    ("motion_design", "动效设计", "设计", "做界面动效、MG 动画、转场与节奏"),
    ("rendering", "效果图与渲染", "设计", "用 SU / 3ds Max / Enscape 出接近实景的效果图"),
    ("live_stream", "直播与出镜", "运营", "面对镜头讲解、控场、促单，扛得住冷场"),
    ("community_ops", "社群运营", "运营", "建群、分层、日常互动与转化，管住几百上千人"),
    ("seo", "SEO / SEM", "运营", "关键词、内容优化、投放账户与出价"),
    ("merchandising", "选品与买手", "运营", "看数据选货、谈供货、定价格与上新节奏"),
    ("script_writing", "剧本与脚本", "内容", "写分镜、台词、短视频脚本，能让人看完"),
    ("dubbing", "配音与朗读", "内容", "声音条件、情绪表达、录音与返修"),
    ("post_production", "后期合成", "内容", "剪辑之外的调色、特效、字幕与包装"),
    ("tax", "税务实务", "职能", "报税、发票、税负测算与税务合规"),
    ("payroll", "薪酬核算", "职能", "算工资、社保公积金、个税与调薪"),
    ("compliance", "合规管理", "职能", "制度、流程、监管要求与风险自查"),
    ("rehab", "康复治疗", "健康", "评定功能、制定训练方案、手法与器械治疗"),
    ("lab_test", "医学检验", "健康", "采血、上机、质控、判断结果可不可信"),
    ("imaging", "医学影像", "健康", "拍片、摆位、设备操作与影像质量管理"),
    ("nutrition", "营养与膳食", "健康", "膳食调查、食谱设计、营养宣教"),
    ("vet", "兽医临床", "健康", "问诊、检查、用药与手术辅助，跟宠物主人沟通"),
    ("elder_care", "老年照护", "健康", "翻身、喂食、防跌倒、跟家属沟通"),
    ("first_aid", "急救", "健康", "心肺复苏、止血包扎、突发状况处置"),
    ("cnc", "数控编程", "工程", "看图纸、编程序、调机床、控公差"),
    ("welding", "焊接技术", "工程", "手工焊 / 氩弧焊，焊缝质量与变形控制"),
    ("construction", "施工技术", "工程", "看施工图、放线、工序安排与现场协调"),
    ("cost_estimation", "工程造价", "工程", "算量、组价、套定额、做预算与结算"),
    ("surveying", "工程测量", "工程", "全站仪 / 水准仪，放样与数据平差"),
    ("safety", "安全生产", "工程", "隐患排查、安全教育、应急预案与台账"),
    ("lean", "精益改善", "工程", "看节拍、找浪费、做 5S 与流程改善"),
    ("maintenance", "设备维护", "工程", "点检、保养、故障判断与备件管理"),
    ("driving", "驾驶", "服务", "有驾照并能安全熟练驾驶（含长途 / 夜间）"),
    ("store_mgmt", "门店管理", "服务", "排班、库存、陈列、业绩与人员管理"),
    ("cooking", "烹饪", "服务", "刀工火候、出品稳定、成本与卫生"),
    ("childcare", "幼儿照护", "服务", "带班、看护、处理哭闹与家长沟通"),
    ("physical_stamina", "体力与耐力", "通用", "能长时间站立、搬运或户外作业"),
]

# ---------------- 新增岗位（90 个） ----------------
NEW_JOBS = [
    ("devops-eng", "DevOps 工程师", "互联网/软件"),
    ("dba", "数据库管理员", "互联网/软件"),
    ("embedded-eng", "嵌入式开发工程师", "互联网/软件"),
    ("game-client", "游戏客户端开发", "互联网/软件"),
    ("it-support", "IT 支持工程师", "互联网/软件"),
    ("qa-automation", "自动化测试工程师", "互联网/软件"),
    ("data-engineer", "数据工程师", "互联网/软件"),
    ("ai-app-engineer", "AI 应用工程师", "互联网/软件"),
    ("tech-writer", "技术文档工程师", "互联网/软件"),
    ("mini-program", "小程序开发工程师", "互联网/软件"),
    ("product-ops", "产品运营", "产品/设计"),
    ("visual-designer", "视觉设计师", "产品/设计"),
    ("illustrator", "插画师", "产品/设计"),
    ("animator", "动画师", "产品/设计"),
    ("interior-designer", "室内设计师", "产品/设计"),
    ("industrial-designer", "工业设计师", "产品/设计"),
    ("packaging-designer", "包装设计师", "产品/设计"),
    ("video-editor", "视频剪辑师", "产品/设计"),
    ("game-artist", "游戏美术", "产品/设计"),
    ("exhibition-designer", "展陈设计师", "产品/设计"),
    ("community-ops", "社群运营", "运营/市场"),
    ("live-ops", "直播运营", "运营/市场"),
    ("ecommerce-cs", "电商客服", "运营/市场"),
    ("seo-specialist", "SEO / SEM 专员", "运营/市场"),
    ("channel-sales", "渠道销售", "运营/市场"),
    ("merchandiser", "买手 / 商品企划", "运营/市场"),
    ("market-researcher", "市场调研员", "运营/市场"),
    ("copywriter", "广告文案", "运营/市场"),
    ("event-exec", "活动执行", "运营/市场"),
    ("franchise-sales", "招商专员", "运营/市场"),
    ("foreign-trade-sales", "外贸业务员", "销售/商务"),
    ("foreign-trade-merchandiser", "外贸跟单员", "销售/商务"),
    ("freight-forwarder", "货运代理", "销售/商务"),
    ("customer-service", "客服专员", "销售/商务"),
    ("retail-sales", "门店导购", "销售/商务"),
    ("telemarketing", "电话销售", "销售/商务"),
    ("bidding-specialist", "招投标专员", "销售/商务"),
    ("cashier", "出纳", "职能/财务"),
    ("tax-specialist", "税务专员", "职能/财务"),
    ("compensation-hr", "薪酬绩效专员", "职能/财务"),
    ("recruiter", "招聘专员", "职能/财务"),
    ("compliance", "合规专员", "职能/财务"),
    ("board-secretary", "董秘 / 证券事务", "职能/财务"),
    ("archivist", "档案管理员", "职能/财务"),
    ("receptionist", "前台", "职能/财务"),
    ("internal-control", "内控专员", "职能/财务"),
    ("wealth-manager", "理财经理", "金融"),
    ("fund-ops", "基金运营", "金融"),
    ("ib-analyst", "投行分析师", "金融"),
    ("claims-adjuster", "保险理赔员", "金融"),
    ("kindergarten-teacher", "幼儿园教师", "教育"),
    ("special-ed-teacher", "特教教师", "教育"),
    ("college-counselor", "高校辅导员", "教育"),
    ("tutor", "课外辅导老师", "教育"),
    ("exam-trainer", "考公考研讲师", "教育"),
    ("pe-coach", "体育教练", "教育"),
    ("art-teacher", "美术老师", "教育"),
    ("edu-consultant", "教育咨询师", "教育"),
    ("clinician", "临床医生", "医疗/健康"),
    ("dentist", "口腔医生", "医疗/健康"),
    ("lab-technician", "医学检验师", "医疗/健康"),
    ("rehab-therapist", "康复治疗师", "医疗/健康"),
    ("psych-counselor", "心理咨询师", "医疗/健康"),
    ("dietitian", "营养师", "医疗/健康"),
    ("veterinarian", "兽医", "医疗/健康"),
    ("elder-care", "养老护理员", "医疗/健康"),
    ("pharma-rep", "医药代表", "医疗/健康"),
    ("imaging-tech", "影像技师", "医疗/健康"),
    ("mold-design", "模具设计师", "制造/工程"),
    ("cnc-programmer", "数控编程员", "制造/工程"),
    ("welding-eng", "焊接工程师", "制造/工程"),
    ("equipment-maintenance", "设备维修工程师", "制造/工程"),
    ("pmc-planner", "生产计划 PMC", "制造/工程"),
    ("safety-officer", "安全员", "制造/工程"),
    ("construction-supervisor", "施工员", "制造/工程"),
    ("cost-engineer", "造价工程师", "制造/工程"),
    ("architect-designer", "建筑设计师", "制造/工程"),
    ("surveyor", "测绘员", "制造/工程"),
    ("scriptwriter", "编剧", "传媒/内容"),
    ("voice-actor", "配音员", "传媒/内容"),
    ("streamer", "带货主播", "传媒/内容"),
    ("film-post", "影视后期", "传媒/内容"),
    ("proofreader", "校对员", "传媒/内容"),
    ("police-officer", "民警", "公共服务/其他"),
    ("firefighter", "消防员", "公共服务/其他"),
    ("courier", "快递员", "公共服务/其他"),
    ("delivery-rider", "外卖骑手", "公共服务/其他"),
    ("ride-hailing-driver", "网约车司机", "公共服务/其他"),
    ("tour-guide", "导游", "公共服务/其他"),
    ("chef", "厨师", "公共服务/其他"),
]


def load_skills():
    return json.loads((DATA / "skills.json").read_text(encoding="utf-8"))


def save_skills(skills):
    (DATA / "skills.json").write_text(
        json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extend_skills():
    skills = load_skills()
    have = {s["id"] for s in skills}
    added = 0
    for sid, name, cat, note in NEW_SKILLS:
        if sid in have:
            continue
        skills.append({"id": sid, "name": name, "cat": cat, "note": note})
        added += 1
    save_skills(skills)
    print(f"技能：新增 {added} 项，共 {len(skills)} 项")
    return skills


def existing_jobs():
    """从 app/data.js 读出已完成的 60 个岗位（id/名称/track）。"""
    text = (ROOT / "app" / "data.js").read_text(encoding="utf-8")
    payload = json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    return [(j["id"], j["name"], j["track"]) for j in payload["jobs"]]


def build_catalog():
    rows = existing_jobs() + NEW_JOBS
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)), "岗位 id 重复：" + str(
        [i for i in ids if ids.count(i) > 1])
    catalog = [{"id": i, "name": n, "track": t} for i, n, t in rows]
    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"目录：{len(catalog)} 个岗位（新增 {len(NEW_JOBS)}）")
    return catalog


def refresh_schema(skills, catalog):
    path = DATA / "_SCHEMA.md"
    md = path.read_text(encoding="utf-8")

    # 1) 技能词表段落
    by_cat = {}
    for s in skills:
        by_cat.setdefault(s["cat"], []).append(s["id"])
    skill_lines = ["## 技能词表（data/skills.json 的 id，只能用这些，共 %d 项）" % len(skills), ""]
    for cat, ids in by_cat.items():
        skill_lines.append(f"{cat}：" + ", ".join(ids))
        skill_lines.append("")
    skill_block = "\n".join(skill_lines)

    md = re.sub(r"## 技能词表.*?(?=## 岗位清单)", skill_block, md, flags=re.S)

    # 2) 岗位清单表格
    table = ["## 岗位清单（全 %d 个，adjacent 只能引用这里的 id）" % len(catalog), ""]
    table.append("| id | 名称 | 方向 | id | 名称 | 方向 |")
    table.append("|---|---|---|---|---|---|")
    half = (len(catalog) + 1) // 2
    left, right = catalog[:half], catalog[half:]
    for i in range(half):
        a = left[i]
        if i < len(right):
            b = right[i]
            table.append(f"| {a['id']} | {a['name']} | {a['track']} | {b['id']} | {b['name']} | {b['track']} |")
        else:
            table.append(f"| {a['id']} | {a['name']} | {a['track']} |  |  |  |")
    table.append("")
    md = re.sub(r"## 岗位清单.*?(?=## 输出)", "\n".join(table) + "\n", md, flags=re.S)

    md = md.replace("## 这是什么", "## 这是什么", 1)
    path.write_text(md, encoding="utf-8")
    print("已刷新 data/_SCHEMA.md")


def main():
    skills = extend_skills()
    catalog = build_catalog()
    refresh_schema(skills, catalog)


if __name__ == "__main__":
    main()
