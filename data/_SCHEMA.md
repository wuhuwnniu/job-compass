# 岗位知识库数据规范（写数据前必读）

## 这是什么

「岗位罗盘」是一个给**刚毕业、还没毕业、暂时待业**的人用的手机应用。用户不填求职意向，
只填自己的专业和已掌握技能，应用反推「你可以去做哪些岗位」，并告诉用户每个岗位
**真实每天做什么、需要哪些技能、自己缺什么、怎么入门、以后怎么长**。

所以数据不是招聘广告，是**一个懂行的朋友在跟你讲实话**。

## 语气规则（很重要）

- 中文，口语，第二人称。像学长/行业里的人聊天，不像 JD。
- `daily` 必须写**具体场景**："早上先看昨天上线的报错""和设计师对间距"，
  **禁止**"负责 XX 系统的开发与维护""参与需求评审"这类招聘套话。
- `reality` 必须写**劝退点**：这行累在哪、枯燥在哪、什么性格做着痛苦。
  每条数据都要有一句真话，不许全是好话。
- 不用夸张词（"前景广阔""大有可为"），不用感叹号。

## 单个岗位的 JSON 结构

```json
{
  "id": "fe-dev",
  "name": "前端开发工程师",
  "aliases": ["Web 前端", "H5 开发"],
  "track": "互联网/软件",
  "tagline": "一句话说清这岗位在干嘛，不超过 30 字",
  "daily": ["具体场景 1", "具体场景 2", "... 5 条，每条 15–45 字"],
  "friendly": "高 | 中 | 低",
  "majors": ["常见对口专业 3–6 个"],
  "skills": [{ "id": "frontend", "w": 3 }],
  "salary": {
    "unit": "千元/月（税前）",
    "junior": [7, 14],
    "mid": [15, 28],
    "senior": [30, 50],
    "note": "一线/新一线城市参考区间；估算值，不是官方统计"
  },
  "growth": ["晋升方向 1", "晋升方向 2", "晋升方向 3"],
  "in3to5": "3–5 年后一般能到什么位置，或能转去哪里。2–3 句。",
  "learn": [
    { "stage": "0–3 个月", "goal": "这一阶段结束时你能做出什么", "items": ["具体学什么 / 做什么产出", "…"] },
    { "stage": "3–6 个月", "goal": "…", "items": ["…"] },
    { "stage": "6–12 个月", "goal": "…", "items": ["…"] }
  ],
  "adjacent": ["ui-designer", "qa-test"],
  "reality": "这行的真实代价与劝退点，2–3 句。"
}
```

### 字段硬性要求

- `id`：小写英文 + 连字符，**必须用下面清单里给定的 id**。
- `friendly`：应届/无经验的人直接能投 = `高`；需要相关实习或作品 = `中`；
  通常要证书/资格证/研究生/多年经验 = `低`。
- `majors`：写中国高校真实存在的专业名，例如「计算机科学与技术」「汉语言文学」
  「护理学」「机械设计制造及其自动化」。不要写「相关专业」。
- `skills`：**6–10 项**，`w` 只能是 `3`（核心必备）、`2`（重要）、`1`（加分）。
  每项 `id` **必须**来自下面的技能词表，不许自造。
  软技能也要挑，但占比不要超过一半。
- `salary`：给区间，**不要给单点数字**。数字是参考估算，`note` 里必须写明
  「估算值，不是官方统计」。区间要符合常识：junior 的下限不要低于当地最低工资，
  senior 的上限不要夸张（除非确实如此）。
- `learn`：固定 3 个阶段，`stage` 写 `0–3 个月` / `3–6 个月` / `6–12 个月`。
  每阶段 2–4 条 `items`，每条是**可执行动作或可交付成果**（"做完 X 放到哪里"），
  不是"学习 XX 知识"这种空话。涉及需要证书的岗位（护士、教师、会计），
  要在第一阶段就写明考证时间线与报考条件。
- `adjacent`：2–4 个**真实可转**的岗位 id，必须来自下面的岗位清单。
- `track`：从这 11 个里选一个：`互联网/软件`、`产品/设计`、`运营/市场`、
  `销售/商务`、`职能/财务`、`金融`、`教育`、`医疗/健康`、`制造/工程`、
  `传媒/内容`、`公共服务/其他`（共 11 个，按岗位实际选）。

## 技能词表（data/skills.json 的 id，只能用这些，共 146 项）

技术：programming, frontend, backend, python, java, mobile_dev, sql, linux, git, testing, cloud, devops, security, ai_tools, embedded, networking

数据：excel, data_analysis, statistics, visualization, machine_learning, spreadsheet_model

设计：ui_design, design_tools, user_research, illustration, motion_design, rendering

产品：product_thinking, prototyping, project_management

运营：operations, content_planning, copywriting, growth, ecommerce, social_media, event_planning, live_stream, community_ops, seo, merchandising

商业：sales, customer_success, business_sense, market_research, presentation

职能：hr, accounting, law, audit, procurement, admin, tax, payroll, compliance, customs, patent, esg, notary, data_compliance

内容：writing, editing, video_editing, photography, audio, translation, foreign_language, script_writing, dubbing, post_production, interpreting

教育：teaching, curriculum, early_ed

健康：nursing, medical, health_management, rehab, lab_test, imaging, nutrition, vet, elder_care, first_aid, massage, midwifery, optometry, dental_lab, speech_therapy

工程：cad, electrical, manufacturing, quality, 3d_modeling, game_engine, cnc, welding, construction, cost_estimation, surveying, safety, lean, maintenance, auto_repair, forklift, drone, elevator, plumbing, hvac, fire_ops, gardening, machine_ops, injection, agronomy, livestock

通用：psychology, communication, teamwork, problem_solving, logic, detail, pressure, learning, creativity, empathy, self_management, drive, service_mind, physical_stamina

服务：driving, store_mgmt, cooking, childcare, coffee, mixology, baking, hair, beauty, nail, makeup, fitness, yoga, pet_care, cashier_ops, visual_merch
## 岗位清单（全 300 个，adjacent 只能引用这里的 id）

| id | 名称 | 方向 | id | 名称 | 方向 |
|---|---|---|---|---|---|
| fe-dev | 前端开发工程师 | 互联网/软件 | barista | 咖啡师 | 公共服务/其他 |
| be-dev | 后端开发工程师 | 互联网/软件 | bartender | 调酒师 | 公共服务/其他 |
| qa-test | 软件测试工程师 | 互联网/软件 | baker | 烘焙师 | 公共服务/其他 |
| ops-cloud | 运维/云工程师 | 互联网/软件 | pastry-chef | 面点师 | 公共服务/其他 |
| data-analyst | 数据分析师 | 互联网/软件 | waiter | 餐厅服务员 | 公共服务/其他 |
| ml-engineer | 算法/机器学习工程师 | 互联网/软件 | tea-artist | 茶艺师 | 公共服务/其他 |
| mobile-dev | 移动端开发工程师 | 互联网/软件 | banquet-exec | 宴会执行 | 公共服务/其他 |
| security-eng | 网络安全工程师 | 互联网/软件 | housekeeper | 客房服务员 | 公共服务/其他 |
| tech-support | 技术支持/实施工程师 | 互联网/软件 | tour-operator | 旅游计调 | 公共服务/其他 |
| product-manager | 产品经理 | 产品/设计 | flight-attendant | 空乘 | 公共服务/其他 |
| ui-designer | UI 设计师 | 产品/设计 | train-attendant | 高铁乘务员 | 公共服务/其他 |
| ux-designer | 交互设计师 | 产品/设计 | airport-ground | 机场地勤 | 公共服务/其他 |
| user-researcher | 用户研究员 | 产品/设计 | hairstylist | 美发师 | 公共服务/其他 |
| game-planner | 游戏策划 | 产品/设计 | beautician | 美容师 | 公共服务/其他 |
| content-ops | 内容运营 | 运营/市场 | manicurist | 美甲师 | 公共服务/其他 |
| newmedia-ops | 新媒体运营 | 运营/市场 | makeup-artist | 化妆师 | 公共服务/其他 |
| user-ops | 用户运营 | 运营/市场 | fitness-coach | 健身教练 | 公共服务/其他 |
| marketing-specialist | 市场专员 | 运营/市场 | yoga-coach | 瑜伽教练 | 公共服务/其他 |
| brand-pr | 品牌公关 | 运营/市场 | massage-therapist | 推拿理疗师 | 医疗/健康 |
| ecommerce-ops | 电商运营 | 运营/市场 | pet-groomer | 宠物美容师 | 公共服务/其他 |
| growth-marketer | 增长/投放专员 | 运营/市场 | store-manager | 店长 | 销售/商务 |
| event-planner | 活动策划 | 运营/市场 | cashier-clerk | 收银员 | 销售/商务 |
| b2b-sales | 大客户销售 | 销售/商务 | visual-merchandiser | 陈列师 | 运营/市场 |
| bd-specialist | 商务拓展 | 销售/商务 | auto-sales | 汽车销售 | 销售/商务 |
| presales | 售前工程师 | 销售/商务 | used-car-appraiser | 二手车评估师 | 销售/商务 |
| customer-success | 客户成功经理 | 销售/商务 | jewelry-sales | 珠宝销售 | 销售/商务 |
| hr-specialist | 人力资源专员 | 职能/财务 | luxury-sales | 奢侈品销售 | 销售/商务 |
| accountant | 会计 | 职能/财务 | insurance-broker | 保险经纪人 | 金融 |
| fpa-analyst | 财务分析 | 职能/财务 | hotel-front-desk | 酒店前台 | 公共服务/其他 |
| legal-assistant | 法务助理 | 职能/财务 | warehouse-keeper | 仓储管理员 | 销售/商务 |
| admin | 行政专员 | 职能/财务 | logistics-dispatcher | 物流调度 | 销售/商务 |
| procurement | 采购/供应链专员 | 制造/工程 | truck-driver | 货车司机 | 公共服务/其他 |
| auditor | 审计助理 | 职能/财务 | forklift-driver | 叉车司机 | 制造/工程 |
| bank-teller | 银行柜员/客户经理 | 金融 | customs-broker | 报关员 | 销售/商务 |
| research-assistant | 证券研究助理 | 金融 | express-station-mgr | 快递站点管理 | 销售/商务 |
| insurance-advisor | 保险顾问 | 金融 | cold-chain-ops | 冷链运营 | 销售/商务 |
| credit-risk | 风控/信贷专员 | 金融 | drone-pilot | 无人机飞手 | 制造/工程 |
| teacher | 中小学教师 | 教育 | property-manager | 物业管家 | 公共服务/其他 |
| trainer | 培训讲师 | 教育 | elevator-tech | 电梯维保 | 制造/工程 |
| curriculum-designer | 课程设计/教研 | 教育 | plumber | 水电工 | 制造/工程 |
| study-abroad | 留学顾问 | 教育 | hvac-tech | 空调安装维修 | 制造/工程 |
| nurse | 护士 | 医疗/健康 | fire-operator | 消防设施操作员 | 公共服务/其他 |
| pharmacist | 药师 | 医疗/健康 | safety-assessor | 安全评价师 | 制造/工程 |
| medical-device-sales | 医疗器械销售 | 销售/商务 | landscape-gardener | 园林绿化 | 制造/工程 |
| health-manager | 健康管理师 | 医疗/健康 | electrician | 电工 | 制造/工程 |
| medical-editor | 医学编辑 | 传媒/内容 | fitter | 钳工 | 制造/工程 |
| mechanical-design | 机械设计工程师 | 制造/工程 | lathe-operator | 车工 | 制造/工程 |
| electrical-eng | 电气工程师 | 制造/工程 | stamping-operator | 冲压工 | 制造/工程 |
| process-eng | 工艺工程师 | 制造/工程 | injection-tech | 注塑工艺 | 制造/工程 |
| quality-eng | 质量工程师 | 制造/工程 | line-leader | 生产班长 | 制造/工程 |
| journalist | 编辑记者 | 传媒/内容 | robot-debug | 机器人调试 | 制造/工程 |
| video-director | 短视频编导 | 传媒/内容 | electrical-assembler | 电气装配 | 制造/工程 |
| photographer | 摄影/摄像师 | 传媒/内容 | iqc-inspector | 来料检验 | 制造/工程 |
| graphic-designer | 平面设计师 | 产品/设计 | die-casting-tech | 压铸工艺 | 制造/工程 |
| translator | 翻译 | 传媒/内容 | heat-treatment | 热处理 | 制造/工程 |
| civil-servant | 公务员/事业单位 | 公共服务/其他 | surface-treatment | 表面处理 | 制造/工程 |
| social-worker | 社会工作者 | 公共服务/其他 | auto-mechanic | 汽车维修工 | 制造/工程 |
| realtor | 房产经纪人 | 销售/商务 | nev-tech | 新能源汽车维修 | 制造/工程 |
| hotel-mgmt | 酒店管培生 | 公共服务/其他 | auto-detailing | 汽车美容 | 制造/工程 |
| headhunter | 猎头顾问 | 职能/财务 | auto-body | 汽车钣金喷漆 | 制造/工程 |
| devops-eng | DevOps 工程师 | 互联网/软件 | auto-parts-sales | 汽配销售 | 销售/商务 |
| dba | 数据库管理员 | 互联网/软件 | midwife | 助产士 | 医疗/健康 |
| embedded-eng | 嵌入式开发工程师 | 互联网/软件 | tuina-therapist | 中医推拿师 | 医疗/健康 |
| game-client | 游戏客户端开发 | 互联网/软件 | optometrist | 眼视光师 | 医疗/健康 |
| it-support | IT 支持工程师 | 互联网/软件 | dental-tech | 义齿技师 | 医疗/健康 |
| qa-automation | 自动化测试工程师 | 互联网/软件 | medical-equipment-tech | 医疗器械维修 | 医疗/健康 |
| data-engineer | 数据工程师 | 互联网/软件 | public-health | 公共卫生医师 | 医疗/健康 |
| ai-app-engineer | AI 应用工程师 | 互联网/软件 | pharmacy-clerk | 药店店员 | 医疗/健康 |
| tech-writer | 技术文档工程师 | 互联网/软件 | health-care-manager | 健康照护师 | 医疗/健康 |
| mini-program | 小程序开发工程师 | 互联网/软件 | sports-rehab | 运动康复师 | 医疗/健康 |
| product-ops | 产品运营 | 产品/设计 | speech-therapist | 言语治疗师 | 医疗/健康 |
| visual-designer | 视觉设计师 | 产品/设计 | medical-writer | 医学写作 | 医疗/健康 |
| illustrator | 插画师 | 产品/设计 | cro | 临床研究协调员 | 医疗/健康 |
| animator | 动画师 | 产品/设计 | regulatory-affairs | 注册专员 | 医疗/健康 |
| interior-designer | 室内设计师 | 产品/设计 | childcare-worker | 保育员 | 教育 |
| industrial-designer | 工业设计师 | 产品/设计 | early-ed-teacher | 早教老师 | 教育 |
| packaging-designer | 包装设计师 | 产品/设计 | after-school-tutor | 托管老师 | 教育 |
| video-editor | 视频剪辑师 | 产品/设计 | coding-teacher | 编程老师 | 教育 |
| game-artist | 游戏美术 | 产品/设计 | english-teacher | 英语老师 | 教育 |
| exhibition-designer | 展陈设计师 | 产品/设计 | admissions-consultant | 招生顾问 | 教育 |
| community-ops | 社群运营 | 运营/市场 | study-abroad-writer | 留学文书 | 教育 |
| live-ops | 直播运营 | 运营/市场 | edu-product-manager | 教育产品经理 | 教育 |
| ecommerce-cs | 电商客服 | 运营/市场 | teaching-researcher | 教研员 | 教育 |
| seo-specialist | SEO / SEM 专员 | 运营/市场 | librarian | 图书馆员 | 教育 |
| channel-sales | 渠道销售 | 运营/市场 | pentester | 渗透测试工程师 | 互联网/软件 |
| merchandiser | 买手 / 商品企划 | 运营/市场 | data-labeler | 数据标注员 | 互联网/软件 |
| market-researcher | 市场调研员 | 运营/市场 | ai-trainer | AI 训练师 | 互联网/软件 |
| copywriter | 广告文案 | 运营/市场 | mlops-engineer | MLOps 工程师 | 互联网/软件 |
| event-exec | 活动执行 | 运营/市场 | av-dev | 音视频开发工程师 | 互联网/软件 |
| franchise-sales | 招商专员 | 运营/市场 | test-dev | 测试开发工程师 | 互联网/软件 |
| foreign-trade-sales | 外贸业务员 | 销售/商务 | tech-artist | 技术美术 | 互联网/软件 |
| foreign-trade-merchandiser | 外贸跟单员 | 销售/商务 | game-ops | 游戏运营 | 运营/市场 |
| freight-forwarder | 货运代理 | 销售/商务 | game-numerical | 游戏数值策划 | 产品/设计 |
| customer-service | 客服专员 | 销售/商务 | user-growth | 用户增长 | 运营/市场 |
| retail-sales | 门店导购 | 销售/商务 | rpa-engineer | RPA 工程师 | 互联网/软件 |
| telemarketing | 电话销售 | 销售/商务 | low-code-impl | 低代码实施顾问 | 互联网/软件 |
| bidding-specialist | 招投标专员 | 销售/商务 | solution-architect | 解决方案架构师 | 互联网/软件 |
| cashier | 出纳 | 职能/财务 | data-viz-engineer | 数据可视化工程师 | 互联网/软件 |
| tax-specialist | 税务专员 | 职能/财务 | prompt-engineer | 提示词工程师 | 互联网/软件 |
| compensation-hr | 薪酬绩效专员 | 职能/财务 | insurance-underwriter | 保险核保 | 金融 |
| recruiter | 招聘专员 | 职能/财务 | securities-broker | 证券经纪人 | 金融 |
| compliance | 合规专员 | 职能/财务 | fund-sales | 基金销售 | 金融 |
| board-secretary | 董秘 / 证券事务 | 职能/财务 | payment-ops | 支付运营 | 金融 |
| archivist | 档案管理员 | 职能/财务 | consumer-risk | 消费金融风控 | 金融 |
| receptionist | 前台 | 职能/财务 | collector | 催收专员 | 金融 |
| internal-control | 内控专员 | 职能/财务 | ir-manager | 投资者关系 | 金融 |
| wealth-manager | 理财经理 | 金融 | trust-officer | 信托经理 | 金融 |
| fund-ops | 基金运营 | 金融 | executive-assistant | 总经理助理 | 职能/财务 |
| ib-analyst | 投行分析师 | 金融 | government-affairs | 政府事务 | 职能/财务 |
| claims-adjuster | 保险理赔员 | 金融 | party-affairs | 党务专员 | 职能/财务 |
| kindergarten-teacher | 幼儿园教师 | 教育 | union-officer | 工会干事 | 职能/财务 |
| special-ed-teacher | 特教教师 | 教育 | patent-agent | 专利代理师 | 职能/财务 |
| college-counselor | 高校辅导员 | 教育 | trademark-agent | 商标代理人 | 职能/财务 |
| tutor | 课外辅导老师 | 教育 | contract-admin | 合同管理 | 职能/财务 |
| exam-trainer | 考公考研讲师 | 教育 | esg-specialist | ESG 专员 | 职能/财务 |
| pe-coach | 体育教练 | 教育 | hrbp | HRBP | 职能/财务 |
| art-teacher | 美术老师 | 教育 | training-officer | 培训主管 | 职能/财务 |
| edu-consultant | 教育咨询师 | 教育 | office-manager | 行政主管 | 职能/财务 |
| clinician | 临床医生 | 医疗/健康 | it-auditor | IT 审计 | 职能/财务 |
| dentist | 口腔医生 | 医疗/健康 | trade-compliance | 贸易合规 | 职能/财务 |
| lab-technician | 医学检验师 | 医疗/健康 | data-compliance | 数据合规专员 | 职能/财务 |
| rehab-therapist | 康复治疗师 | 医疗/健康 | retoucher | 修图师 | 传媒/内容 |
| psych-counselor | 心理咨询师 | 医疗/健康 | director | 导演 | 传媒/内容 |
| dietitian | 营养师 | 医疗/健康 | producer | 制片人 | 传媒/内容 |
| veterinarian | 兽医 | 医疗/健康 | script-supervisor | 场记 | 传媒/内容 |
| elder-care | 养老护理员 | 医疗/健康 | lighting-tech | 灯光师 | 传媒/内容 |
| pharma-rep | 医药代表 | 医疗/健康 | sound-recordist | 录音师 | 传媒/内容 |
| imaging-tech | 影像技师 | 医疗/健康 | host | 主持人 | 传媒/内容 |
| mold-design | 模具设计师 | 制造/工程 | podcast-producer | 播客制作 | 传媒/内容 |
| cnc-programmer | 数控编程员 | 制造/工程 | content-moderator | 内容审核员 | 传媒/内容 |
| welding-eng | 焊接工程师 | 制造/工程 | copyright-ops | 版权运营 | 传媒/内容 |
| equipment-maintenance | 设备维修工程师 | 制造/工程 | simultaneous-interpreter | 同声传译 | 传媒/内容 |
| pmc-planner | 生产计划 PMC | 制造/工程 | localization-specialist | 本地化专员 | 传媒/内容 |
| safety-officer | 安全员 | 制造/工程 | auxiliary-police | 辅警 | 公共服务/其他 |
| construction-supervisor | 施工员 | 制造/工程 | urban-management | 城管 | 公共服务/其他 |
| cost-engineer | 造价工程师 | 制造/工程 | notary | 公证员 | 公共服务/其他 |
| architect-designer | 建筑设计师 | 制造/工程 | forensic-appraiser | 司法鉴定人 | 公共服务/其他 |
| surveyor | 测绘员 | 制造/工程 | funeral-director | 殡葬礼仪师 | 公共服务/其他 |
| scriptwriter | 编剧 | 传媒/内容 | charity-officer | 慈善项目专员 | 公共服务/其他 |
| voice-actor | 配音员 | 传媒/内容 | nursing-home-manager | 养老院院长 | 公共服务/其他 |
| streamer | 带货主播 | 传媒/内容 | lawyer | 律师 | 公共服务/其他 |
| film-post | 影视后期 | 传媒/内容 | sign-language-interpreter | 手语翻译 | 公共服务/其他 |
| proofreader | 校对员 | 传媒/内容 | agronomist | 农艺师 | 制造/工程 |
| police-officer | 民警 | 公共服务/其他 | horticulturist | 园艺师 | 制造/工程 |
| firefighter | 消防员 | 公共服务/其他 | livestock-tech | 畜牧技术员 | 制造/工程 |
| courier | 快递员 | 公共服务/其他 | agri-ecommerce | 农产品电商 | 运营/市场 |
| delivery-rider | 外卖骑手 | 公共服务/其他 | farm-manager | 家庭农场主 | 制造/工程 |
| ride-hailing-driver | 网约车司机 | 公共服务/其他 | supply-planner | 供应链计划 | 制造/工程 |
| tour-guide | 导游 | 公共服务/其他 | energy-manager | 能源管理师 | 制造/工程 |
| chef | 厨师 | 公共服务/其他 | wedding-planner | 婚礼策划 | 运营/市场 |

## 输出

把结果写成**一个 JSON 数组**（只含分配给你的岗位，按清单顺序），
保存到指定文件，UTF-8，不写注释、不写 Markdown 代码块。
写完后自己核对一遍：每个 `skills[].id` 和 `adjacent[]` 都在上面的清单里；
JSON 能被 `json.load` 解析；没有占位符、没有 "..."。

## 示例（fe-dev，已存在，不要重复生成）

```json
{
  "id": "fe-dev",
  "name": "前端开发工程师",
  "aliases": ["Web 前端", "H5 开发"],
  "track": "互联网/软件",
  "tagline": "把设计稿变成能点、能滑、加载还不慢的界面",
  "daily": [
    "早上先看昨天上线后有没有报错，处理用户反馈的某个按钮点不动",
    "和设计师对一版新页面，确认间距、交互和手机上怎么显示",
    "写一个列表页：搜索、翻页、没有数据时的空状态都要处理",
    "下午和后台同学联调接口，字段对不上就来回改几轮",
    "改 bug、自测、等发布，上线后再看一眼监控有没有异常"
  ],
  "friendly": "高",
  "majors": ["计算机科学与技术", "软件工程", "数字媒体技术", "信息管理与信息系统"],
  "skills": [
    { "id": "frontend", "w": 3 },
    { "id": "programming", "w": 3 },
    { "id": "git", "w": 2 },
    { "id": "problem_solving", "w": 2 },
    { "id": "learning", "w": 2 },
    { "id": "teamwork", "w": 2 },
    { "id": "ui_design", "w": 2 },
    { "id": "sql", "w": 1 }
  ],
  "salary": {
    "unit": "千元/月（税前）",
    "junior": [7, 14],
    "mid": [15, 28],
    "senior": [30, 50],
    "note": "一线/新一线城市参考区间，小公司偏低、大厂偏高；估算值，不是官方统计"
  },
  "growth": [
    "前端开发 → 高级前端，能独立负责一整块业务",
    "往工程化 / 跨端 / 可视化方向做专精",
    "转产品经理，或带 3–5 人小组做技术管理"
  ],
  "in3to5": "3–5 年后一般能独立负责一条业务线的前端；也有人专精到可视化、低代码这类窄而深的方向，或转产品、转管理。",
  "learn": [
    {
      "stage": "0–3 个月",
      "goal": "做出 2 个能在手机上点开的页面",
      "items": [
        "HTML/CSS 布局：flex、响应式，手机上不塌",
        "JavaScript 基础：变量、函数、数组方法、点击事件",
        "做完一个个人主页 + 一个待办清单，传到 GitHub Pages 拿到公开链接"
      ]
    },
    {
      "stage": "3–6 个月",
      "goal": "能独立接一个完整小项目",
      "items": [
        "选一个框架（Vue 或 React）学组件与状态管理",
        "调接口：请求、加载中、报错三种状态都要处理",
        "用 Git 管代码，会开分支、写提交信息"
      ]
    },
    {
      "stage": "6–12 个月",
      "goal": "达到能投实习 / 初级岗的水平",
      "items": [
        "做一个有真实交互的项目（后台管理或小程序），写清 README",
        "补基础：浏览器渲染、缓存、跨域、简单的性能优化",
        "刷常见面试题，把项目讲成「解决了谁的什么问题」"
      ]
    }
  ],
  "adjacent": ["ui-designer", "qa-test", "mobile-dev"],
  "reality": "技术更新快，两三年不学就跟不上；赶发布时连续加班是常事；大部分时间在改别人写的代码、修边界 bug，不是天天做新功能。坐不住、受不了反复改的人会很痛苦。"
}
```
