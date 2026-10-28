#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""维护岗位总目录（catalog.json）与技能词表（skills.json），并刷新 data/_SCHEMA.md。

幂等：以 data/catalog.json 为基准，把 NEW_JOBS / NEW_JOBS2 里还没进目录的加进去。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ---------------- 新增技能：第一批（36 项，对应 60→150） ----------------
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

# ---------------- 新增技能：第二批（36 项，对应 150→300） ----------------
NEW_SKILLS2 = [
    ("coffee", "咖啡制作", "服务", "萃取、奶泡、出品稳定与吧台节奏"),
    ("mixology", "调酒", "服务", "基酒配比、风味搭配、吧台出品速度"),
    ("baking", "烘焙", "服务", "面团、发酵、烤制曲线与配方复现"),
    ("hair", "美发", "服务", "剪烫染、脸型判断、与客人沟通需求"),
    ("beauty", "美容", "服务", "皮肤判断、手法、仪器操作与卫生规范"),
    ("nail", "美甲", "服务", "修型、上色、延长与卫生消毒"),
    ("makeup", "化妆造型", "服务", "底妆、眉眼、发型与不同场合的妆面"),
    ("fitness", "健身指导", "服务", "动作示范、训练计划、体态评估与安全保护"),
    ("yoga", "瑜伽", "服务", "体式、呼吸、课程编排与辅助手法"),
    ("massage", "推拿按摩", "健康", "经络穴位、手法力度与禁忌症判断"),
    ("pet_care", "宠物护理", "服务", "洗护、美容、保定与应激处理"),
    ("cashier_ops", "收银与门店系统", "服务", "收银、退换货、盘点与系统录单"),
    ("visual_merch", "商品陈列", "服务", "动线、堆头、色彩搭配与陈列标准"),
    ("auto_repair", "汽车维修", "工程", "读故障码、拆装、诊断与维修工艺"),
    ("forklift", "叉车操作", "工程", "叉车证、装卸、库位与安全规范"),
    ("customs", "报关与单证", "职能", "商品编码、报关单、原产地与合规"),
    ("drone", "无人机操作", "工程", "飞行、航拍、航线规划与执照要求"),
    ("elevator", "电梯维保", "工程", "维保规程、故障排查与年检要求"),
    ("plumbing", "水电维修", "工程", "水路电路、安装、检修与安全用电"),
    ("hvac", "制冷与空调", "工程", "冷媒、安装、调试与故障判断"),
    ("fire_ops", "消防设施操作", "工程", "消防控制室、设施巡检与应急处置"),
    ("gardening", "园林绿化", "工程", "苗木、修剪、养护与景观施工"),
    ("machine_ops", "机床操作", "工程", "车铣刨磨、装夹、对刀与公差控制"),
    ("injection", "注塑工艺", "工程", "模具、参数调试、缺陷分析与良率"),
    ("midwifery", "助产", "健康", "产程观察、接生、新生儿处理与急救"),
    ("optometry", "验光配镜", "健康", "验光流程、镜片选择与视功能检查"),
    ("dental_lab", "义齿制作", "健康", "模型、蜡型、CAD/CAM 与咬合调整"),
    ("speech_therapy", "言语治疗", "健康", "评估、构音训练与家庭康复指导"),
    ("early_ed", "早教", "教育", "亲子课设计、感统游戏与家长沟通"),
    ("patent", "专利实务", "职能", "检索、撰写权利要求、答复审查意见"),
    ("esg", "ESG 与可持续", "职能", "碳核算、披露报告与利益相关方沟通"),
    ("notary", "公证业务", "职能", "公证程序、文书审查与执业规范"),
    ("agronomy", "农艺", "工程", "作物栽培、病虫草害与田间管理"),
    ("livestock", "畜牧养殖", "工程", "饲喂、防疫、繁殖与养殖场管理"),
    ("interpreting", "同声传译", "内容", "边听边译、术语准备与高压专注"),
    ("data_compliance", "数据合规", "职能", "个人信息保护、数据出境与合规评估"),
]

# ---------------- 新增岗位：第一批（90 个，60→150） ----------------
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

# ---------------- 新增岗位：第二批（150 个，150→300） ----------------
NEW_JOBS2 = [
    # 餐饮 / 酒店 / 交通
    ("barista", "咖啡师", "公共服务/其他"),
    ("bartender", "调酒师", "公共服务/其他"),
    ("baker", "烘焙师", "公共服务/其他"),
    ("pastry-chef", "面点师", "公共服务/其他"),
    ("waiter", "餐厅服务员", "公共服务/其他"),
    ("tea-artist", "茶艺师", "公共服务/其他"),
    ("banquet-exec", "宴会执行", "公共服务/其他"),
    ("housekeeper", "客房服务员", "公共服务/其他"),
    ("tour-operator", "旅游计调", "公共服务/其他"),
    ("flight-attendant", "空乘", "公共服务/其他"),
    ("train-attendant", "高铁乘务员", "公共服务/其他"),
    ("airport-ground", "机场地勤", "公共服务/其他"),
    # 美业 / 健身
    ("hairstylist", "美发师", "公共服务/其他"),
    ("beautician", "美容师", "公共服务/其他"),
    ("manicurist", "美甲师", "公共服务/其他"),
    ("makeup-artist", "化妆师", "公共服务/其他"),
    ("fitness-coach", "健身教练", "公共服务/其他"),
    ("yoga-coach", "瑜伽教练", "公共服务/其他"),
    ("massage-therapist", "推拿理疗师", "医疗/健康"),
    ("pet-groomer", "宠物美容师", "公共服务/其他"),
    # 零售 / 门店
    ("store-manager", "店长", "销售/商务"),
    ("cashier-clerk", "收银员", "销售/商务"),
    ("visual-merchandiser", "陈列师", "运营/市场"),
    ("auto-sales", "汽车销售", "销售/商务"),
    ("used-car-appraiser", "二手车评估师", "销售/商务"),
    ("jewelry-sales", "珠宝销售", "销售/商务"),
    ("luxury-sales", "奢侈品销售", "销售/商务"),
    ("insurance-broker", "保险经纪人", "金融"),
    ("hotel-front-desk", "酒店前台", "公共服务/其他"),
    # 物流 / 交通
    ("warehouse-keeper", "仓储管理员", "销售/商务"),
    ("logistics-dispatcher", "物流调度", "销售/商务"),
    ("truck-driver", "货车司机", "公共服务/其他"),
    ("forklift-driver", "叉车司机", "制造/工程"),
    ("customs-broker", "报关员", "销售/商务"),
    ("express-station-mgr", "快递站点管理", "销售/商务"),
    ("cold-chain-ops", "冷链运营", "销售/商务"),
    ("drone-pilot", "无人机飞手", "制造/工程"),
    # 建筑 / 物业
    ("property-manager", "物业管家", "公共服务/其他"),
    ("elevator-tech", "电梯维保", "制造/工程"),
    ("plumber", "水电工", "制造/工程"),
    ("hvac-tech", "空调安装维修", "制造/工程"),
    ("fire-operator", "消防设施操作员", "公共服务/其他"),
    ("safety-assessor", "安全评价师", "制造/工程"),
    ("landscape-gardener", "园林绿化", "制造/工程"),
    # 制造
    ("electrician", "电工", "制造/工程"),
    ("fitter", "钳工", "制造/工程"),
    ("lathe-operator", "车工", "制造/工程"),
    ("stamping-operator", "冲压工", "制造/工程"),
    ("injection-tech", "注塑工艺", "制造/工程"),
    ("line-leader", "生产班长", "制造/工程"),
    ("robot-debug", "机器人调试", "制造/工程"),
    ("electrical-assembler", "电气装配", "制造/工程"),
    ("iqc-inspector", "来料检验", "制造/工程"),
    ("die-casting-tech", "压铸工艺", "制造/工程"),
    ("heat-treatment", "热处理", "制造/工程"),
    ("surface-treatment", "表面处理", "制造/工程"),
    # 汽修
    ("auto-mechanic", "汽车维修工", "制造/工程"),
    ("nev-tech", "新能源汽车维修", "制造/工程"),
    ("auto-detailing", "汽车美容", "制造/工程"),
    ("auto-body", "汽车钣金喷漆", "制造/工程"),
    ("auto-parts-sales", "汽配销售", "销售/商务"),
    # 医疗 / 健康
    ("midwife", "助产士", "医疗/健康"),
    ("tuina-therapist", "中医推拿师", "医疗/健康"),
    ("optometrist", "眼视光师", "医疗/健康"),
    ("dental-tech", "义齿技师", "医疗/健康"),
    ("medical-equipment-tech", "医疗器械维修", "医疗/健康"),
    ("public-health", "公共卫生医师", "医疗/健康"),
    ("pharmacy-clerk", "药店店员", "医疗/健康"),
    ("health-care-manager", "健康照护师", "医疗/健康"),
    ("sports-rehab", "运动康复师", "医疗/健康"),
    ("speech-therapist", "言语治疗师", "医疗/健康"),
    ("medical-writer", "医学写作", "医疗/健康"),
    ("cro", "临床研究协调员", "医疗/健康"),
    ("regulatory-affairs", "注册专员", "医疗/健康"),
    # 教育
    ("childcare-worker", "保育员", "教育"),
    ("early-ed-teacher", "早教老师", "教育"),
    ("after-school-tutor", "托管老师", "教育"),
    ("coding-teacher", "编程老师", "教育"),
    ("english-teacher", "英语老师", "教育"),
    ("admissions-consultant", "招生顾问", "教育"),
    ("study-abroad-writer", "留学文书", "教育"),
    ("edu-product-manager", "教育产品经理", "教育"),
    ("teaching-researcher", "教研员", "教育"),
    ("librarian", "图书馆员", "教育"),
    # 互联网
    ("pentester", "渗透测试工程师", "互联网/软件"),
    ("data-labeler", "数据标注员", "互联网/软件"),
    ("ai-trainer", "AI 训练师", "互联网/软件"),
    ("mlops-engineer", "MLOps 工程师", "互联网/软件"),
    ("av-dev", "音视频开发工程师", "互联网/软件"),
    ("test-dev", "测试开发工程师", "互联网/软件"),
    ("tech-artist", "技术美术", "互联网/软件"),
    ("game-ops", "游戏运营", "运营/市场"),
    ("game-numerical", "游戏数值策划", "产品/设计"),
    ("user-growth", "用户增长", "运营/市场"),
    ("rpa-engineer", "RPA 工程师", "互联网/软件"),
    ("low-code-impl", "低代码实施顾问", "互联网/软件"),
    ("solution-architect", "解决方案架构师", "互联网/软件"),
    ("data-viz-engineer", "数据可视化工程师", "互联网/软件"),
    ("prompt-engineer", "提示词工程师", "互联网/软件"),
    # 金融
    ("insurance-underwriter", "保险核保", "金融"),
    ("securities-broker", "证券经纪人", "金融"),
    ("fund-sales", "基金销售", "金融"),
    ("payment-ops", "支付运营", "金融"),
    ("consumer-risk", "消费金融风控", "金融"),
    ("collector", "催收专员", "金融"),
    ("ir-manager", "投资者关系", "金融"),
    ("trust-officer", "信托经理", "金融"),
    # 职能
    ("executive-assistant", "总经理助理", "职能/财务"),
    ("government-affairs", "政府事务", "职能/财务"),
    ("party-affairs", "党务专员", "职能/财务"),
    ("union-officer", "工会干事", "职能/财务"),
    ("patent-agent", "专利代理师", "职能/财务"),
    ("trademark-agent", "商标代理人", "职能/财务"),
    ("contract-admin", "合同管理", "职能/财务"),
    ("esg-specialist", "ESG 专员", "职能/财务"),
    ("hrbp", "HRBP", "职能/财务"),
    ("training-officer", "培训主管", "职能/财务"),
    ("office-manager", "行政主管", "职能/财务"),
    ("it-auditor", "IT 审计", "职能/财务"),
    ("trade-compliance", "贸易合规", "职能/财务"),
    ("data-compliance", "数据合规专员", "职能/财务"),
    # 传媒
    ("retoucher", "修图师", "传媒/内容"),
    ("director", "导演", "传媒/内容"),
    ("producer", "制片人", "传媒/内容"),
    ("script-supervisor", "场记", "传媒/内容"),
    ("lighting-tech", "灯光师", "传媒/内容"),
    ("sound-recordist", "录音师", "传媒/内容"),
    ("host", "主持人", "传媒/内容"),
    ("podcast-producer", "播客制作", "传媒/内容"),
    ("content-moderator", "内容审核员", "传媒/内容"),
    ("copyright-ops", "版权运营", "传媒/内容"),
    ("simultaneous-interpreter", "同声传译", "传媒/内容"),
    ("localization-specialist", "本地化专员", "传媒/内容"),
    # 公共服务
    ("auxiliary-police", "辅警", "公共服务/其他"),
    ("urban-management", "城管", "公共服务/其他"),
    ("notary", "公证员", "公共服务/其他"),
    ("forensic-appraiser", "司法鉴定人", "公共服务/其他"),
    ("funeral-director", "殡葬礼仪师", "公共服务/其他"),
    ("charity-officer", "慈善项目专员", "公共服务/其他"),
    ("nursing-home-manager", "养老院院长", "公共服务/其他"),
    ("lawyer", "律师", "公共服务/其他"),
    ("sign-language-interpreter", "手语翻译", "公共服务/其他"),
    # 农林
    ("agronomist", "农艺师", "制造/工程"),
    ("horticulturist", "园艺师", "制造/工程"),
    ("livestock-tech", "畜牧技术员", "制造/工程"),
    ("agri-ecommerce", "农产品电商", "运营/市场"),
    ("farm-manager", "家庭农场主", "制造/工程"),
    ("supply-planner", "供应链计划", "制造/工程"),
    ("energy-manager", "能源管理师", "制造/工程"),
    # 其他
    ("wedding-planner", "婚礼策划", "运营/市场"),
]


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def save_skills(skills):
    (DATA / "skills.json").write_text(
        json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extend_skills():
    skills = load_json(DATA / "skills.json", [])
    have = {s["id"] for s in skills}
    added = 0
    for group in (NEW_SKILLS, NEW_SKILLS2):
        for sid, name, cat, note in group:
            if sid in have:
                continue
            skills.append({"id": sid, "name": name, "cat": cat, "note": note})
            have.add(sid)
            added += 1
    save_skills(skills)
    print(f"技能：新增 {added} 项，共 {len(skills)} 项")
    return skills


def build_catalog():
    base = load_json(DATA / "catalog.json", [])
    rows = [(r["id"], r["name"], r["track"]) for r in base]
    have = {r[0] for r in rows}
    added = 0
    for jid, name, track in NEW_JOBS + NEW_JOBS2:
        if jid in have:
            continue
        rows.append((jid, name, track))
        have.add(jid)
        added += 1
    ids = [r[0] for r in rows]
    assert len(ids) == len(set(ids)), "岗位 id 重复"
    catalog = [{"id": i, "name": n, "track": t} for i, n, t in rows]
    (DATA / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"目录：{len(catalog)} 个岗位（本次新增 {added}）")
    return catalog


def refresh_schema(skills, catalog):
    path = DATA / "_SCHEMA.md"
    md = path.read_text(encoding="utf-8")

    by_cat = {}
    for s in skills:
        by_cat.setdefault(s["cat"], []).append(s["id"])
    lines = [f"## 技能词表（data/skills.json 的 id，只能用这些，共 {len(skills)} 项）", ""]
    for cat, ids in by_cat.items():
        lines.append(f"{cat}：" + ", ".join(ids))
        lines.append("")
    md = re.sub(r"## 技能词表.*?(?=## 岗位清单)", "\n".join(lines), md, flags=re.S)

    table = [f"## 岗位清单（全 {len(catalog)} 个，adjacent 只能引用这里的 id）", "",
             "| id | 名称 | 方向 | id | 名称 | 方向 |", "|---|---|---|---|---|---|"]
    half = (len(catalog) + 1) // 2
    left, right = catalog[:half], catalog[half:]
    for i in range(half):
        a = left[i]
        b = right[i] if i < len(right) else None
        if b:
            table.append(f"| {a['id']} | {a['name']} | {a['track']} | {b['id']} | {b['name']} | {b['track']} |")
        else:
            table.append(f"| {a['id']} | {a['name']} | {a['track']} |  |  |  |")
    md = re.sub(r"## 岗位清单.*?(?=## 输出)", "\n".join(table) + "\n\n", md, flags=re.S)
    path.write_text(md, encoding="utf-8")
    print("已刷新 data/_SCHEMA.md")


def main():
    skills = extend_skills()
    catalog = build_catalog()
    refresh_schema(skills, catalog)


if __name__ == "__main__":
    main()
