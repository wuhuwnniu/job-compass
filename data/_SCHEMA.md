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

## 技能词表（data/skills.json 的 id，只能用这些，共 110 项）

技术：programming, frontend, backend, python, java, mobile_dev, sql, linux, git, testing, cloud, devops, security, ai_tools, embedded, networking

数据：excel, data_analysis, statistics, visualization, machine_learning, spreadsheet_model

设计：ui_design, design_tools, user_research, illustration, motion_design, rendering

产品：product_thinking, prototyping, project_management

运营：operations, content_planning, copywriting, growth, ecommerce, social_media, event_planning, live_stream, community_ops, seo, merchandising

商业：sales, customer_success, business_sense, market_research, presentation

职能：hr, accounting, law, audit, procurement, admin, tax, payroll, compliance

内容：writing, editing, video_editing, photography, audio, translation, foreign_language, script_writing, dubbing, post_production

教育：teaching, curriculum

健康：nursing, medical, health_management, rehab, lab_test, imaging, nutrition, vet, elder_care, first_aid

工程：cad, electrical, manufacturing, quality, 3d_modeling, game_engine, cnc, welding, construction, cost_estimation, surveying, safety, lean, maintenance

通用：psychology, communication, teamwork, problem_solving, logic, detail, pressure, learning, creativity, empathy, self_management, drive, service_mind, physical_stamina

服务：driving, store_mgmt, cooking, childcare

## 岗位清单（全 150 个，adjacent 只能引用这里的 id）

| id | 名称 | 方向 | id | 名称 | 方向 |
|---|---|---|---|---|---|
| fe-dev | 前端开发工程师 | 互联网/软件 | industrial-designer | 工业设计师 | 产品/设计 |
| be-dev | 后端开发工程师 | 互联网/软件 | packaging-designer | 包装设计师 | 产品/设计 |
| qa-test | 软件测试工程师 | 互联网/软件 | video-editor | 视频剪辑师 | 产品/设计 |
| ops-cloud | 运维/云工程师 | 互联网/软件 | game-artist | 游戏美术 | 产品/设计 |
| data-analyst | 数据分析师 | 互联网/软件 | exhibition-designer | 展陈设计师 | 产品/设计 |
| ml-engineer | 算法/机器学习工程师 | 互联网/软件 | community-ops | 社群运营 | 运营/市场 |
| mobile-dev | 移动端开发工程师 | 互联网/软件 | live-ops | 直播运营 | 运营/市场 |
| security-eng | 网络安全工程师 | 互联网/软件 | ecommerce-cs | 电商客服 | 运营/市场 |
| tech-support | 技术支持/实施工程师 | 互联网/软件 | seo-specialist | SEO / SEM 专员 | 运营/市场 |
| product-manager | 产品经理 | 产品/设计 | channel-sales | 渠道销售 | 运营/市场 |
| ui-designer | UI 设计师 | 产品/设计 | merchandiser | 买手 / 商品企划 | 运营/市场 |
| ux-designer | 交互设计师 | 产品/设计 | market-researcher | 市场调研员 | 运营/市场 |
| user-researcher | 用户研究员 | 产品/设计 | copywriter | 广告文案 | 运营/市场 |
| game-planner | 游戏策划 | 产品/设计 | event-exec | 活动执行 | 运营/市场 |
| content-ops | 内容运营 | 运营/市场 | franchise-sales | 招商专员 | 运营/市场 |
| newmedia-ops | 新媒体运营 | 运营/市场 | foreign-trade-sales | 外贸业务员 | 销售/商务 |
| user-ops | 用户运营 | 运营/市场 | foreign-trade-merchandiser | 外贸跟单员 | 销售/商务 |
| marketing-specialist | 市场专员 | 运营/市场 | freight-forwarder | 货运代理 | 销售/商务 |
| brand-pr | 品牌公关 | 运营/市场 | customer-service | 客服专员 | 销售/商务 |
| ecommerce-ops | 电商运营 | 运营/市场 | retail-sales | 门店导购 | 销售/商务 |
| growth-marketer | 增长/投放专员 | 运营/市场 | telemarketing | 电话销售 | 销售/商务 |
| event-planner | 活动策划 | 运营/市场 | bidding-specialist | 招投标专员 | 销售/商务 |
| b2b-sales | 大客户销售 | 销售/商务 | cashier | 出纳 | 职能/财务 |
| bd-specialist | 商务拓展 | 销售/商务 | tax-specialist | 税务专员 | 职能/财务 |
| presales | 售前工程师 | 销售/商务 | compensation-hr | 薪酬绩效专员 | 职能/财务 |
| customer-success | 客户成功经理 | 销售/商务 | recruiter | 招聘专员 | 职能/财务 |
| hr-specialist | 人力资源专员 | 职能/财务 | compliance | 合规专员 | 职能/财务 |
| accountant | 会计 | 职能/财务 | board-secretary | 董秘 / 证券事务 | 职能/财务 |
| fpa-analyst | 财务分析 | 职能/财务 | archivist | 档案管理员 | 职能/财务 |
| legal-assistant | 法务助理 | 职能/财务 | receptionist | 前台 | 职能/财务 |
| admin | 行政专员 | 职能/财务 | internal-control | 内控专员 | 职能/财务 |
| procurement | 采购/供应链专员 | 制造/工程 | wealth-manager | 理财经理 | 金融 |
| auditor | 审计助理 | 职能/财务 | fund-ops | 基金运营 | 金融 |
| bank-teller | 银行柜员/客户经理 | 金融 | ib-analyst | 投行分析师 | 金融 |
| research-assistant | 证券研究助理 | 金融 | claims-adjuster | 保险理赔员 | 金融 |
| insurance-advisor | 保险顾问 | 金融 | kindergarten-teacher | 幼儿园教师 | 教育 |
| credit-risk | 风控/信贷专员 | 金融 | special-ed-teacher | 特教教师 | 教育 |
| teacher | 中小学教师 | 教育 | college-counselor | 高校辅导员 | 教育 |
| trainer | 培训讲师 | 教育 | tutor | 课外辅导老师 | 教育 |
| curriculum-designer | 课程设计/教研 | 教育 | exam-trainer | 考公考研讲师 | 教育 |
| study-abroad | 留学顾问 | 教育 | pe-coach | 体育教练 | 教育 |
| nurse | 护士 | 医疗/健康 | art-teacher | 美术老师 | 教育 |
| pharmacist | 药师 | 医疗/健康 | edu-consultant | 教育咨询师 | 教育 |
| medical-device-sales | 医疗器械销售 | 销售/商务 | clinician | 临床医生 | 医疗/健康 |
| health-manager | 健康管理师 | 医疗/健康 | dentist | 口腔医生 | 医疗/健康 |
| medical-editor | 医学编辑 | 传媒/内容 | lab-technician | 医学检验师 | 医疗/健康 |
| mechanical-design | 机械设计工程师 | 制造/工程 | rehab-therapist | 康复治疗师 | 医疗/健康 |
| electrical-eng | 电气工程师 | 制造/工程 | psych-counselor | 心理咨询师 | 医疗/健康 |
| process-eng | 工艺工程师 | 制造/工程 | dietitian | 营养师 | 医疗/健康 |
| quality-eng | 质量工程师 | 制造/工程 | veterinarian | 兽医 | 医疗/健康 |
| journalist | 编辑记者 | 传媒/内容 | elder-care | 养老护理员 | 医疗/健康 |
| video-director | 短视频编导 | 传媒/内容 | pharma-rep | 医药代表 | 医疗/健康 |
| photographer | 摄影/摄像师 | 传媒/内容 | imaging-tech | 影像技师 | 医疗/健康 |
| graphic-designer | 平面设计师 | 产品/设计 | mold-design | 模具设计师 | 制造/工程 |
| translator | 翻译 | 传媒/内容 | cnc-programmer | 数控编程员 | 制造/工程 |
| civil-servant | 公务员/事业单位 | 公共服务/其他 | welding-eng | 焊接工程师 | 制造/工程 |
| social-worker | 社会工作者 | 公共服务/其他 | equipment-maintenance | 设备维修工程师 | 制造/工程 |
| realtor | 房产经纪人 | 销售/商务 | pmc-planner | 生产计划 PMC | 制造/工程 |
| hotel-mgmt | 酒店管培生 | 公共服务/其他 | safety-officer | 安全员 | 制造/工程 |
| headhunter | 猎头顾问 | 职能/财务 | construction-supervisor | 施工员 | 制造/工程 |
| devops-eng | DevOps 工程师 | 互联网/软件 | cost-engineer | 造价工程师 | 制造/工程 |
| dba | 数据库管理员 | 互联网/软件 | architect-designer | 建筑设计师 | 制造/工程 |
| embedded-eng | 嵌入式开发工程师 | 互联网/软件 | surveyor | 测绘员 | 制造/工程 |
| game-client | 游戏客户端开发 | 互联网/软件 | scriptwriter | 编剧 | 传媒/内容 |
| it-support | IT 支持工程师 | 互联网/软件 | voice-actor | 配音员 | 传媒/内容 |
| qa-automation | 自动化测试工程师 | 互联网/软件 | streamer | 带货主播 | 传媒/内容 |
| data-engineer | 数据工程师 | 互联网/软件 | film-post | 影视后期 | 传媒/内容 |
| ai-app-engineer | AI 应用工程师 | 互联网/软件 | proofreader | 校对员 | 传媒/内容 |
| tech-writer | 技术文档工程师 | 互联网/软件 | police-officer | 民警 | 公共服务/其他 |
| mini-program | 小程序开发工程师 | 互联网/软件 | firefighter | 消防员 | 公共服务/其他 |
| product-ops | 产品运营 | 产品/设计 | courier | 快递员 | 公共服务/其他 |
| visual-designer | 视觉设计师 | 产品/设计 | delivery-rider | 外卖骑手 | 公共服务/其他 |
| illustrator | 插画师 | 产品/设计 | ride-hailing-driver | 网约车司机 | 公共服务/其他 |
| animator | 动画师 | 产品/设计 | tour-guide | 导游 | 公共服务/其他 |
| interior-designer | 室内设计师 | 产品/设计 | chef | 厨师 | 公共服务/其他 |

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
