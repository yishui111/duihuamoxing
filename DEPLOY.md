
## 🚀 换电脑部署（保证可用）

> **方式 A（推荐 · 100% 保证）**：用 U 盘 / 网盘把「原项目整份文件夹」（含全部大件）复制到新电脑 → 双击 `start.bat` 即可。
>
> **方式 B（代码装配）**：`git clone` 本仓库 → 双击 `assemble.bat` 预检大件 → 按提示补齐缺失项（下载地址见下文/README）→ 双击 `start.bat`。

> 说明：引擎、模型、镜像、运行时等大件体积超过 GitHub 单文件 100MB 上限，**不随仓库分发**；本仓库承载全部自研代码与装配指引，"方式 A"是换机部署最稳路径，"方式 B"适合需要重新下载大件的场景。
# DEPLOY —— 新机器部署指南（知音 ZhiYin）

> 目标：把本仓库拉到一台**新电脑**，按本文件逐步操作，得到和原项目一模一样的运行环境。
> 本仓库只含源码/脚本/文档，**模型、Python 运行时、GPT-SoVITS 引擎、素材等大件需要按下面步骤准备**。
> Windows 下所有 `.bat` 已用 `%~dp0` 定位，**仓库可放在任意位置**（建议纯英文路径，如 `apps\duihuamoxing`）。

---

## 0. 环境要求

| 项 | 要求 |
|----|------|
| 操作系统 | Windows 10/11（中文系统最佳；其他语言系统请确保支持代码页 936 / 中文区域） |
| Python | 3.12（装 3.11 亦可，见各步骤说明） |
| 显卡 | NVIDIA + CUDA 可选：有则 Ollama/TTS 用 GPU（快）；无 GPU 也能跑（较慢） |
| 磁盘 | 运行时+模型合计约 20~30GB 可用空间 |
| 网络 | 首次下载模型/安装依赖需要联网；日常运行可断网（离线模式） |

安装 Ollama、Python 时按默认即可；Python 安装时勾选 **Add python.exe to PATH**。

---

## 1. 获取代码

```bash
git clone https://github.com/yishui111/duihuamoxing.git
cd duihuamoxing
```

（不想用 git 也可以把整个文件夹复制过去，注意保留目录层级。）

---

## 2. 安装 Ollama 并准备对话/嵌入模型

1. 下载安装 Ollama：https://ollama.com/download （装到 `%LOCALAPPDATA%\Programs\Ollama\`）。
2. **停掉 Ollama 托盘自启**（可选但推荐）：任务管理器 → 启动 → 禁用 `Ollama`，否则它常驻占用 11434 且用默认空模型目录，和本项目脚本冲突。
3. 本项目启动脚本用 `OLLAMA_MODELS=<仓库>\data\ollama\models` 作为模型目录，所以先手动把模型拉进这个目录（只做一次）：

```bat
:: 终端 1：以项目模型目录启动 Ollama（窗口保持运行）
cd /d <你的仓库路径>
set OLLAMA_MODELS=%CD%\data\ollama\models
ollama serve
```

```bat
:: 终端 2：拉取模型（会存到上面的 data\ollama\models）
set OLLAMA_MODELS=%CD%\data\ollama\models
ollama pull qwen2.5:7b
ollama pull bge-m3
```

> 国内网络拉不动时：设置镜像源环境变量（如 `OLLAMA_HOST` 走代理）或下载离线包后导入（`ollama create`）。完成后关掉终端 1，日常用 `启动.bat` 即可。

---

## 3. 安装 Open WebUI（对话系统前端+服务）

```bat
cd /d <你的仓库路径>
python -m venv venv
venv\Scripts\python -m pip install -U pip
venv\Scripts\python -m pip install open-webui
```

验证：`venv\Scripts\open-webui --version` 能输出版本号即可。

### 3.1 注入 loader.js（前端增强，必需）

`loader.js` 实现了模型记忆、系统定义生成、数字人窗口、朗读回退等功能，需要内联进 Open WebUI 前端：

```bat
venv\Scripts\python scripts\inline_loader.py
:: 输出 "内联完成, index.html 大小: xxx" 即成功
```

> loader.js 每次更新后重新执行一次本命令，并让用户浏览器 `Ctrl+Shift+R` 强刷。

### 3.2 语音输入模型（可选，中文语音输入）

默认 `WHISPER_MODEL=small`，Open WebUI 首次使用语音输入时会自动下载；离线/国内网络慢时可手动预下载：

```bat
venv\Scripts\python -m pip install huggingface_hub
venv\Scripts\python scripts\download_whisper.py
```

---

## 4. 安装 GPT-SoVITS 朗读引擎（文字驱动语音子项目）

> 不装也能用对话系统；朗读会提示服务未启动并自动回退系统语音。建议完整安装。

1. **克隆官方引擎**到约定目录（启动脚本默认从 `GSV_ROOT=<仓库>\文字驱动语音\gptsovits\GPT-SoVITS` 加载）：

```bat
cd /d <你的仓库路径>\文字驱动语音
git clone https://github.com/RVC-Boss/GPT-SoVITS.git gptsovits\GPT-SoVITS
cd gptsovits\GPT-SoVITS
```

2. **下载预训练基座**：按 GPT-SoVITS 官方 README 下载 `GPT_SoVITS/pretrained_models/` 所需文件
   （含 `chinese-hubert-base`、`chinese-roberta-wwm-ext-large` 等，脚本会自动找这些路径；官方一键包/HF 均可）。

3. **Python 运行时**：本项目启动脚本使用 `<仓库>\runtime\py312\python.exe`（镜像原项目布局）。两种做法任选：
   - **A（推荐）**：用 Python 3.12 官方安装器装到自定义目录 `runtime\py312`，再把 GPT-SoVITS 依赖装进去：

     ```bat
     :: 下载 python-3.12.x-amd64.exe 后执行（安静安装到 runtime\py312，不加入 PATH）
     python-3.12.x-amd64.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir=<你的仓库路径>\runtime\py312
     cd /d <你的仓库路径>\文字驱动语音\gptsovits\GPT-SoVITS
     <你的仓库路径>\runtime\py312\python.exe -m pip install -U pip
     <你的仓库路径>\runtime\py312\python.exe -m pip install -r requirements.txt
     :: 如需 GPU 版 PyTorch，再按官方文档装 cu12x 版 torch（CPU 也可运行，速度慢）
     ```
   - **B**：不想用 runtime 布局，可自行改 `文字驱动语音\启动.bat` 里的 python 路径或先 `set PYTHON_EXE=...`（脚本暂不支持，需手改）。

4. **ffmpeg（可选）**：朗读转 mp3、数字人建库转码需要。下载 https://ffmpeg.org/download.html 的
   Windows release 包，解压成如下结构（与脚本默认路径一致）：

   ```
   runtime\ffmpeg\bin\ffmpeg.exe
   runtime\ffmpeg\bin\ffprobe.exe
   ```

---

## 5. 角色声音模型（训练音色，可选）

朗读要"用自己的音色"，需要用 GPT-SoVITS 官方流程**训练角色**（教程见其官方仓库），
训练完成后按《文字驱动语音\模型放置与使用.md》把 4 件套放进来：

```
文字驱动语音\tts_service\models\<角色名>\
├── <角色名>.ckpt
├── <角色名>.pth
├── ref.wav
└── ref_text.txt
```

每个子文件夹 = 一个角色；放进去启动服务即自动识别。**训练素材（真人录音）属个人数据，请勿提交公开仓库。**

---

## 6. 数字人素材（可选）

数字人服务用**你自己的说话视频**建库：

1. 启动数字人（`一键启动全部.bat` 或 `数字人\启动.bat`）；
2. 打开建库工具 http://127.0.0.1:48620/web/preprocess.html
3. 上传一段 3~10 秒正脸说话视频 → 一键生成图库（素材生成在 `数字人\avatar_libs\`，属个人形象数据，勿提交）。

---

## 7. 启动 / 停止

| 操作 | 方式 |
|------|------|
| 全部启动 | 双击 `一键启动全部.bat`（三个子项目窗口分别启动）；或双击 `启动.bat`（单窗口全部启动） |
| 全部停止 | 双击 `一键关闭全部.bat` 或 `关闭.bat` |
| 只启对话 | `对话系统\启动.bat` |
| 只启数字人 | `数字人\启动.bat` |
| 只启朗读 | `文字驱动语音\启动.bat`（需已有引擎+模型） |
| 查看状态 | `状态.bat` |

**首次打开对话界面**：http://localhost:8088 → 创建管理员账号并登录（WEBUI_AUTH=True），
顶部模型选 `qwen2.5:7b` 即可对话。

---

## 8. 数据库关键配置（新机器/重装后核对）

Open WebUI 的配置存在 `data\open-webui\webui.db`（config 表）。**首次部署环境变量已正确时无需处理**；
若出现下面症状，用 `scripts\` 里的工具修复（先停 open-webui）：

| 症状 | 配置 | 修复 |
|------|------|------|
| RAG 嵌入报 InvalidUrlClientError / 500 | `rag.ollama.base_url` 为空或旧地址 | `python scripts\fix_ollama_url.py` |
| 记忆/检索 500（`"" > 0.0` 类型错） | `rag.relevance_threshold` 是空串 | `python scripts\fix_relevance_threshold.py` |
| 页面读配置报错 | config 表有非法 JSON | `python scripts\fix_config_json.py`（自动备份） |
| 朗读音色不是默认角色 | `audio.tts.voice` | `TTS_VOICE=<角色> python scripts\set_voice_azhong.py` |
| 朗读"读一半就停" | `audio.tts.split_on` | `python scripts\set_split_none.py` |
| 排查用 | ollama/tts 配置查看 | `python scripts\check_ollama_cfg.py` / `scripts\check_tts_cfg.py` |

TTS 对接：Open WebUI **设置 → 音频**：语音服务 = OpenAI 兼容，Base URL = `http://127.0.0.1:8061/v1`，
音色 = 你的角色名（8061 `/v1/audio/voices` 自动列出）。浏览器/system 语音回退由 `loader.js` 处理。

---

## 9. 验证

```powershell
powershell -ExecutionPolicy Bypass -File .\tests\test_rag_chat.ps1
# 输出 "结果: PASS" 即核心功能正常（对话/嵌入/健康/语音端点）
```

登录+界面对话等更完整用例（及数字人嘴型 e2e）见 `tests\README.md`。

---

## 10. 本机与目标机器可能不同的项

| 项 | 本机默认 | 说明 |
|----|----------|------|
| 仓库位置 | 任意 | 脚本全部 `%~dp0` 相对定位，可整体移动 |
| 端口 | 8088 / 11434 / 48620 / 8061 | 被占用时改对应启动脚本/环境变量（`AVATAR_PORT`、`TTS_API_PORT` 等） |
| Open WebUI 账号 | 首次创建 | 管理员账号密码由你设定，不写死在仓库 |
| Ollama 模型目录 | `data\ollama\models` | 由启动脚本 `OLLAMA_MODELS` 指向；迁移时整个 `data\` 带走 |
| 显存 | 自动 | 对话/TTS 按显存选 cuda/cpu；<10GB 时 TTS 自动 CPU |
| DeepSeek API Key（可选） | 无 | 人格蒸馏用 `tools\` 时设 `DEEPSEEK_API_KEY`，否则用本地 ollama 引擎 |

---

## 11. 常见问题排查

- **`启动.bat` 提示 Ollama not found**：Ollama 没装或不在 `%LOCALAPPDATA%\Programs\Ollama\`。
- **Ollama 一直"就绪检测失败"**：多半是模型没拉到 `data\ollama\models`（见第 2 节）；或托盘 Ollama 占用 11434（禁用自启后重试）。
- **Open WebUI 起不来**：看 `log\webui.err.log`；端口 8088 被占换端口（改 `启动.bat` 的 `--port`）。
- **朗读自动变系统语音**：8061 未启动或 `tts_service\models\` 无完整角色（4 件套）；先看 `log\tts.err.log`。
- **数字人素材库为空**：素材需自己建库（第 6 节），仓库不含真人素材。
- **首次对话/朗读慢**：模型冷加载（qwen 1~3 分钟、某音色首次 10~25 秒），属正常；启动脚本已自动预热默认音色。
- **代理/杀软拦截**：本项目全本地端口，可加防火墙例外：8088/11434/48620/8061。

---

## 12. 更新与迁移

- **代码更新**：`git pull` 后如 `loader.js` 有变，重跑 `python scripts\inline_loader.py` 并强刷浏览器。
- **迁移**：整个文件夹复制即用（含 `venv`/`runtime`/`data`/`gptsovits`/模型目录/素材库）；换机器后重新跑一次第 7、9 节验证。
- 每次部署优化后请同步更新本文件。
