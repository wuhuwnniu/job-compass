# 街道观察 · Street Observatory

Windows 桌面客流调研 App：上传固定机位视频、设置计数线、统计通行人次并逐条复核，再通过使用者自己的 DeepSeek Key 生成报告和继续问答。

## 桌面版使用

解压 StreetObservatory-0.2.0-windows-x64.zip，保留整个文件夹，双击 **StreetObservatory.exe**。无需安装 Python，内置 CPU 检测环境和 YOLO11n 权重。需要 Windows 10/11 x64 与 Microsoft Edge WebView2 Runtime。

桌面数据保存在 `%LOCALAPPDATA%\StreetObservatory`，不写入安装目录。

GitHub 中的源码位于 `street-observatory/`。进入仓库 **Actions → Street Observatory Windows → 最近一次成功运行 → Artifacts** 下载 Windows 包（需登录 GitHub）。构建产物保留 30 天；之后可用 Run workflow 重新构建。下载产物的外层 ZIP 解压后，再解压其中的 Windows 便携包。

## 接入自己的 DeepSeek Key

1. 点击右上角 **AI 待配置** 或左下角 **AI 接入设置**。
2. 粘贴以 sk- 开头的完整密钥，或者从只包含密钥的 TXT 文件导入。
3. 填写模型名（默认 deepseek-flash），点击 **保存配置**，无需重启。
4. 点击 **测试已保存连接**，确认当前密钥和模型能正常调用。
5. 可随时替换或删除密钥；只改模型时，Key 留空会保留旧值。

密钥由后端使用 Windows 当前用户 DPAPI 加密保存。浏览器只持有随机 HttpOnly、SameSite=Strict 的配置标识；读取设置接口只返回尾号，不返回完整 Key。不同浏览器配置不会继承彼此的 Key，不同 Windows 用户有各自的数据目录和加密凭据。清除浏览器数据或换电脑后，需要重新填写 Key。

这是本地桌面配置隔离，不是带注册登录的公网多人 SaaS。普通浏览器请求不会继承开发者环境变量中的 Key。不要将本地服务直接暴露到公网。

AI 按使用者自己的 DeepSeek 账户计费。默认只发送统计摘要和填写的项目背景，不发送原视频、人像截图或逐人轨迹。未配置 Key 时，视频统计、复核与导出仍可使用。

官方文档：https://api-docs.deepseek.com/zh-cn/

## 调研流程

创建项目 → 填写背景 → 上传视频 → 设置计数线和矩形区域 → 后台分析 → 查看时段和方向统计 → 逐条回放复核 → AI 报告 → PDF / CSV 导出。

推荐 H.264 MP4，最大 20GB。其他格式的预览能力取决于浏览器编码支持。行人脚部越过有限计数线记一次，同一个人再次经过可再次计数，不提供去重人数。A/B 表示越线后到达的一侧。

更换视频或重新分析会清除旧事件与人工修正；修改背景、设置或统计结果会更新数据版本，旧报告标记过期。

## 当前能力与限制

- 已实现：项目管理、视频上传、本地保存、真实行人检测与短时跟踪、双向过线人次、时段趋势、事件复核、补录、中文 PDF 和 CSV。
- 已实现：个人 Key 导入、加密保存、替换、删除及连接测试，以及报告、问答、项目比较的 DeepSeek 接口。
- 尚未接入：服装、携带物品、出行方式及同行规模模型，界面明确标记暂不支持。
- 不支持移动拍摄统计；按需求不提供停留、排队、进店或转化率。
- 中断后保留已提交结果，可从头重试；尚无逐帧断点续算。
- 五分钟真实公开样片已跑通（自动 178 次过线）。前 120 秒仅做近似标注框数量对照，不是精确率或召回率评测。一小时真实视频及真实 DeepSeek 调用仍需对应素材和有效密钥验证。

## 从源码运行

推荐 Python 3.12：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

浏览器访问 http://127.0.0.1:8765 。开发数据默认在 data/，可通过 STREET_DATA_DIR 指向其他目录。

运行原生桌面窗口：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe desktop.pyw
```

开发者在命令行直接调用 AI 函数时，可使用 .env.example 中的环境变量；这些凭据不会自动共享给浏览器用户。

## 测试与本地打包

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node --check web/app.js
.\tools\build_windows.ps1
```

打包脚本准备官方模型、构建程序、运行冻结程序自检，生成便携 ZIP 和 SHA256 校验文件。包中排除 .env、Key、用户数据库、视频和测试输出。不配置自动发布工作流，上传采用手动操作。

## 结构

- app.py：HTTP API、SQLite、统计、报告与导出。
- credentials.py：浏览器配置隔离和 Windows 密钥加密。
- ai_providers.py：模型服务商适配接口与 DeepSeek 实现。
- analyzer.py / attributes.py：检测跟踪、过线事件、属性扩展接口。
- desktop.pyw：桌面窗口、用户数据目录与退出清理。
- web/：中文响应式工作台。
- packaging/：桌面打包规格、版本、使用说明。
- tools/build_windows.ps1：本地构建与可执行文件自检。
- tests/：独立临时数据库及合成密钥上的回归检查。

Key 接口为 GET/PUT/DELETE /api/ai/settings 和 POST /api/ai/test。项目分析接口包括 /api/projects 及项目下的 /video、/analyze、/stats、/events、/report、/chat、/csv、/pdf，另有 /api/compare。

## 许可证

本项目以 GNU AGPL-3.0 发布，见 LICENSE。依赖和模型另有各自条款，见 THIRD_PARTY_NOTICES.md。公开测试视频不随源代码和安装包分发。
