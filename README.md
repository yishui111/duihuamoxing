<div align="center">

# 知音 ZhiYin —— 综合 AI 对话系统

> ⭐ **喜欢这个项目？请先点个 Star 支持一下，让更多人看到！** ⭐

<!-- 自动徽章（公开后自动显示星星数/语言/许可证），占位写法，推送前按仓库替换：
![GitHub stars](https://img.shields.io/github/stars/yishui111/duihuamoxing.svg?style=flat-square&color=orange)
![GitHub forks](https://img.shields.io/github/forks/yishui111/duihuamoxing.svg?style=flat-square)
![GitHub repo size](https://img.shields.io/github/repo-size/yishui111/duihuamoxing.svg?style=flat-square)
-->

对话 + 知识库 + 数字人 + 朗读 四合一，全部**本地运行**、数据不出门：一个窗口启动，即可拥有会聊天的 AI 助理、会查资料的知识库、会张嘴的数字人和会用训练音色朗读的语音。

</div>

---

## ✨ 项目简介

知音（ZhiYin）是一套**完全本地私有**的综合 AI 对话系统，由三个可独立运行的子项目 + 一个公网发布工作台组成：

| 子项目 | 端口 | 功能 | 代码 |
|--------|------|------|------|
| 对话系统 | 8088 / 11434 | 本地大模型对话 + RAG 知识库（Open WebUI + Ollama） | 启动脚本 + 前端增强 `loader.js` |
| 数字人 | 48620 | 数字人素材服务：说话视频 → 嘴型图库、声音驱动嘴型 | **自研** `avatar_server.py`（纯 Python 标准库） |
| 文字驱动语音 | 8061 | 文字 → 训练音色语音合成（GPT-SoVITS OpenAI 兼容封装） | **自研** `tts_service/tts_api.py`（FastAPI） |
| 公网部署工作台 `yumingbushu/` | 8291 / 8290 | Cloudflare Tunnel 发布公网 + 自研登录网关 + 运维面板 | **自研** `login_gateway/`、`ops_dashboard/` |

- **适合谁**：想在本机搭一套私有 AI 助理、不想把聊天/资料/声音发给云端、又想要"看得见、听得见"的完整体验的用户。
- **本仓库包含**：三个子项目的自研代码、启动/关闭脚本、`loader.js` 前端增强、运维/排障脚本、人格蒸馏工具、部署文档、公网发布工作台（原兄弟仓库 yumingbushu 已并入为 `yumingbushu/` 子目录）。**模型、运行时、真人素材等大件不随仓库分发**（见下方下载表与 DEPLOY.md）。

## 🎯 主要功能

- 💬 **本地对话**：Ollama 运行 `qwen2.5:7b`（可换任意模型），GPU/CPU 自适应，离线可用
- 📚 **RAG 知识库**：上传 PDF/Word/Excel/文本，`bge-m3` 自动向量化，对话中 `#` 引用即答
- 🧠 **模型记忆（各记各的）**：对话前自动检索该模型的记忆注入上下文，每 10 次对话/30 分钟自动总结入库
- ⚙️ **系统定义生成**：对话页 🧠 按钮，把角色资料一键总结成系统提示词并写回模型
- 🎙️ **语音输入**：本地 Whisper（中文），说话即可提问
- 🔊 **朗读回复**：GPT-SoVITS 训练音色朗读；服务未启动时自动回退浏览器系统语音并提示
- 🎭 **数字人**：自研嘴型驱动——把一段说话视频变成图库，朗读时嘴巴随声音张合
- 🧬 **人格蒸馏工具链**：聊天记录 → 五层人格档案 → 接入模型预设/知识库（`tools/`，纯标准库）
- 🚀 **一键启停**：`一键启动全部.bat` 拉起三个子项目，`一键关闭全部.bat` 全部停止
- 🌐 **一键公网上线**：`公网上线.bat` = 本地服务 → 登录网关 → Cloudflare Tunnel，手机/外网直接访问 https://nas.905283.xyz（无需公网 IP / 端口映射；`公网下线.bat` 反向关停，`公网状态.bat` 体检）

## 🗂️ 目录结构

```
duihuamoxing/
├── 对话系统/            # 子项目 1：Open WebUI(8088) + Ollama(11434)，含启动/关闭.bat
├── 数字人/              # 子项目 2：数字人素材服务(48620)，自研 avatar_server.py + avatar_core/avatar_web
├── 文字驱动语音/         # 子项目 3：GPT-SoVITS 朗读服务(8061)，自研 tts_service/tts_api.py
├── yumingbushu/         # 公网部署工作台：cloudflared 隧道脚本 + 自研登录网关(8291) + 运维面板(8290)，见其 README/DEPLOY
├── 共享资源/            # 公共依赖（venv/runtime/data 在仓库根共享）说明
├── tools/               # 人格蒸馏 / 带记忆对话 / 角色管理（自研，纯标准库）
├── scripts/             # 部署与排障脚本（loader.js 集成 / webui.db 修复 / whisper 下载）
├── tests/               # 功能验证脚本（PowerShell / Node）
├── docs/                # 示例模板（个人资料模板）
├── loader.js            # 前端增强：记忆/系统定义/数字人/朗读回退/兼容性 polyfill（自研）
├── docker-compose.yml   # 可选 Docker 部署（备选方案，主用原生部署）
├── 一键启动全部.bat / 一键关闭全部.bat   # 三个子项目一键启停
├── 启动.bat / 关闭.bat / 状态.bat         # 单窗口启动全部 / 停止 / 状态查看
├── 公网上线.bat / 公网下线.bat / 公网状态.bat   # 公网发布一键上线 / 下线 / 体检（调用 yumingbushu\）
├── 使用说明.md          # 功能使用手册（记忆/系统定义/音色切换/FAQ）
├── DEPLOY.md            # ★ 新机器部署指南（从头搭一模一样的环境）
└── README.md            # 本文件
```

> 💡 本仓库只包含**自研代码 / 脚本 / 配置 / 文档**。
> 模型权重、Python 运行时、GPT-SoVITS 引擎、真人素材等**大件不随仓库分发**，见下方「大件资源下载」与 `DEPLOY.md`。

## 🚀 快速开始（拉到新电脑即可部署）

> 完整步骤见 **`DEPLOY.md`**（环境要求、每步命令、常见问题）。这里是浓缩版：

### 环境要求

- Windows 10/11（中文系统，含 cmd 脚本）；NVIDIA 显卡可选（无 GPU 也能跑，较慢）
- 软件：Python 3.12（安装时勾选 Add to PATH）、Ollama、Git

### 1. 克隆

```bash
git clone https://github.com/yishui111/duihuamoxing.git
cd duihuamoxing
```

### 2. 按 DEPLOY.md 准备运行时与模型

（Ollama 安装 + `ollama pull qwen2.5:7b` / `ollama pull bge-m3`、`venv` 装 Open WebUI、注入 loader.js、GPT-SoVITS 引擎、ffmpeg——对应下方大件下载表）

### 3. 启动

```bat
一键启动全部.bat        :: 三个子项目分别最小化窗口启动；或双击 启动.bat 单窗口全部启动
```

### 4. 验证

- 浏览器打开 **http://localhost:8088**，首次使用创建管理员账号并登录，顶部模型选择 `qwen2.5:7b` 即可对话；
- 输入框 `#` 选择知识库引用文档；点喇叭用训练音色朗读；头部数字人小画面可选人物。

### 5. （可选）发布公网

双击 `公网上线.bat`（隧道步骤会弹 UAC 提权确认），完成后用手机流量打开 **https://nas.905283.xyz**，先过登录网关（口令在 `yumingbushu\login_gateway\config.json`，不入库）再进入知音。前置条件：`yumingbushu\cloudflared\` 下已放好 `cloudflared.exe` 与隧道 token（见 `yumingbushu\README.md`）；不用公网时双击 `公网下线.bat` 关停。

## 📥 大件资源下载（模型 / 运行时 / 引擎——均不随仓库分发）

| 资源 | 用途 | 下载地址 / 获取方式 |
| ---- | ---- | ---- |
| Ollama（运行时） | 本地 LLM 推理 | https://ollama.com/download （Windows 安装版；模型目录由启动脚本指向 `data\ollama\models`） |
| `qwen2.5:7b`（Q4_K_M，约 4.7GB） | 对话问答模型 | 安装 Ollama 后 `ollama pull qwen2.5:7b`（国内网络可配 `OLLAMA_HOST`/镜像源） |
| `bge-m3`（F16，约 1.2GB） | 知识库文档向量化嵌入模型 | `ollama pull bge-m3` |
| Open WebUI（Python 包） | 对话界面 + RAG 知识库前端/服务 | 见 DEPLOY.md：`python -m venv venv` + `pip install open-webui`（镜像：https://github.com/open-webui/open-webui ） |
| faster-whisper-small | 语音输入（本地转文字） | Open WebUI 自动下载；国内网络用 `python scripts\download_whisper.py`（hf-mirror） |
| GPT-SoVITS 推理引擎（第三方） | 朗读合成引擎 | 官方仓库克隆到 `文字驱动语音\gptsovits\GPT-SoVITS`：https://github.com/RVC-Boss/GPT-SoVITS ；预训练基座按官方 README 下载 |
| 角色声音模型（可选） | 训练音色朗读 | 用 GPT-SoVITS 官方训练流程训练自己的音色 → 4 件套放入 `文字驱动语音\tts_service\models\<角色>\`（见《模型放置与使用.md》） |
| 数字人素材（可选） | 数字人人物形象 | 用本项目建库工具 `http://127.0.0.1:48620/web/preprocess.html` 由你自己的说话视频生成 |
| ffmpeg（可选） | 视频/音频转码 | https://ffmpeg.org/download.html ，解压放 `runtime\ffmpeg` |

## 🛠️ 本地开发 & 提交

```bash
git add .
git commit -m "feat: xxx"
git push origin main
```

> 提交前务必确认没有把密钥/模型/素材/个人数据加进来（`.gitignore` 已兜底，见「注意事项」）。

## ❓ 常见问题（FAQ）

- **Q：启动报「Open WebUI not found (venv not installed)」？** A：还没有创建 `venv` 并安装 open-webui，按 `DEPLOY.md` 第 4 节执行。
- **Q：对话 401 / 没反应？** A：浏览器按 `Ctrl+Shift+R` 强刷（loader.js 更新后需要）；仍不行则重新登录一次。
- **Q：朗读变成系统自带声音？** A：内置朗读服务（8061）未启动或音色模型缺失。先启动 `文字驱动语音\启动.bat`，并确认 `tts_service\models\` 下有完整角色模型（4 件套）。
- **Q：数字人画面不出现？** A：确认数字人服务（48620）已启动、页面已强刷；在数字人菜单里选人物（素材需先用建库工具生成）。
- **Q：显存不够？** A：Ollama 单并发 + 显存预留已调优；8GB 显卡时 TTS 会自动 CPU 推理；模型太大可换 `qwen2.5:3b`。
- **Q：能联网吗？** A：本项目离线优先（OFFLINE_MODE=true），除首次下载模型外不依赖公网；DeepSeek 人格蒸馏等外部引擎需自行配 Key。

## ⚠️ 注意事项

- 敏感信息（密钥、token、账号密码）一律放环境变量或 `.env`（参考 `DEPLOY.md`），禁止提交；
- 本项目**不含真人素材与个人数据**：数字人素材库、训练音色模型、真实个人资料/聊天记录请放在本地并用 `.gitignore` 忽略，不要上传公开仓库；
- 默认端口仅供本机/内网使用；需要外网访问时用内置的 `公网上线.bat`（Cloudflare Tunnel + 自研登录网关，详见 `yumingbushu\README.md`），不要直接把 8088 端口映射到公网；
- 本仓库仅供学习交流使用，涉及他人形象/声音/隐私的内容请自行取得授权。

## 📄 许可证

MIT License

## 🙏 支持与致谢

如果这个项目帮到了你，**请点亮右上角的 ⭐ Star**，你的支持是我持续更新的最大动力！
