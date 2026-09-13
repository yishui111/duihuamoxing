# AGENTS.md — 知音 ZhiYin 综合 AI 对话系统 项目档案

> ⚠️ 修改本仓库前先读本文件（AI 助手/开发者项目记忆）。用户向文档见 README.md / DEPLOY.md / 使用说明.md。

## 1. 定位
本地私有四合一综合 AI 对话系统：**对话 + 知识库 + 数字人 + 朗读**，一键全启动、数据不出门。品牌名「知音 ZhiYin」。原兄弟仓库 yumingbushu（Cloudflare Tunnel 部署工作台）已于 2026-09-06 并入为本仓库子目录 `yumingbushu/`，双击根目录「公网上线.bat」即可发布公网 nas.905283.xyz（登录网关 8088 反代 8089，运维面板 8290 仅本机；旧同级目录 D:\xm\yumingbushu 已于 2026-09-07 删除，勿再引用）。

## 2. 端口 / 组件
| 端口 | 组件 |
| ---- | ---- |
| 8089 | Open WebUI（对话+知识库；loader.js 前端增强） |
| 11434 | Ollama（qwen2.5:7b 本地对话 / bge-m3 RAG 向量） |
| 48620 | 自研数字人（avatar_server.py 纯标准库嘴型驱动，素材建库由用户视频自建） |
| 18060 | GPT-SoVITS 训练音色朗读（文字驱动语音/tts_service/tts_api.py 封装，失败自动回退系统语音） |
| 8088 | 自研登录网关（yumingbushu/login_gateway，公网入口第一道登录，反代 8089） |
| 8290 | 自研运维面板（yumingbushu/ops_dashboard，仅本机访问） |

结构：对话系统/、数字人/、文字驱动语音/、共享资源/、yumingbushu/（公网部署工作台：隧道脚本 + find_entry.ps1/entry_names.json 中文入口探测，勿删）、tools/（人格蒸馏工具，纯标准库）、scripts/（11 个自研运维脚本，路径已相对化）、tests/、docs/、loader.js（单文件前端增强，个人域名已改可配置 window.__DSH_AVATAR_REMOTE__，默认本机）。

## 3. 公开版边界（不入库）
venv/、runtime/、data/（open-webui 库/用户数据/ollama 模型）、log/、sessions/（真实人格会话）、ziliao/、.extract_tmp/、_edge_test/（浏览器 profile）、patched/、py-xiaozhi 与 xiaozhi-server 与 shumeipai 与 树莓派小智（第三方小智开源副本，后者含 pi@192.168.1.15 LAN 凭据）、GPT-SoVITS 引擎与角色音色模型、数字人 avatar_libs/avatar_input（真人脸图素材）、两枚 image.tar、.webui_secret_key、真实个人资料文档（仅留虚构模板）、_scan_login.py/_auth_dom.html（登录页探测脚本，一律弃传）、yumingbushu/ 内的 cloudflared/（含 tunnel-token.txt 隧道钥匙）、login_gateway/config.json（网关口令）与 .secret、backup/（webui.db 备份）。
> 大件装配路径与下载命令全在 DEPLOY.md；真人声音/形象素材绝不入库。

## 4. 特殊约定
- 4 个含中文目录调用的 bat（启动.bat/关闭.bat/一键启动全部.bat/一键关闭全部.bat 及文字驱动语音\启动.bat）= **GBK + chcp936**（与原件一致，中文 Windows 正常运行；勿转 UTF-8、勿去 chcp，否则找不到中文目录）。其余 bat 纯 ASCII+CRLF+无 BOM（根目录 公网上线/公网下线/公网状态.bat 内容纯 ASCII，文件名含中文无碍）。
- 三子项目 README 均注明模型/引擎/素材按根 DEPLOY.md 准备。
- 提交 `git push origin main`；中文文档 UTF-8。
---
### 关键点（2026-09-02 上传整理补充）
- 知音 ZhiYin 四合一：8089 Open WebUI / 11434 Ollama / 48620 自研数字人(avatar_server.py 纯标准库) / 18060 GPT-SoVITS 朗读(tts_service/tts_api.py)
- 4 个含中文目录调用的 bat（启动/关闭/一键启动全部/一键关闭全部）= GBK + chcp936，勿转 UTF-8、勿去 chcp（否则找不到中文目录）
- _scan_login.py / _auth_dom.html（登录页探测）一律弃传；loader.js 个人域名已改可配置(window.__DSH_AVATAR_REMOTE__，默认本机)
- 大件装配全在 DEPLOY.md：Ollama 便携+模型(qwen2.5:7b/bge-m3)、open-webui(pip)、GPT-SoVITS 引擎、whisper(scripts\download_whisper.py)、ffmpeg
- data/sessions/log/真人素材/人格档案 不入库
### 关键点（2026-09-06 yumingbushu 并入）
- yumingbushu/ 是子目录不再是兄弟仓库：其脚本 PROJECT 一律 `%~dp0..` 解析到本仓库根；根目录新增 公网上线.bat/公网下线.bat/公网状态.bat（ASCII+CRLF）调用 yumingbushu\start|stop|check_status.bat
- 敏感且需自备（已 gitignore）：yumingbushu\cloudflared\cloudflared.exe + tunnel-token.txt、login_gateway\config.json、login_gateway\.secret、backup\
- cloudflared 服务与 ZhiYinBackup/ZhiYinHealthCheck 计划任务已于 2026-09-07 用 yumingbushu\finalize_move.bat(.ps1) 重指向新目录，旧同级目录已删除；日后整体挪动 duihuamoxing 后再运行一次它即可；start_cloudflared_2.bat 保留"服务启动失败→本目录前台运行"回退
- silent_start_local.bat 已固定 Open WebUI 工作目录到项目根（否则会生成第二把 .webui_secret_key，重启后登录态全失效）并补齐 OLLAMA_MODELS 等环境变量
- 8290 端口与用户另一项目 chat_workbench.py 冲突：跑运维面板前先关它
### 关键点（2026-09-11 仅手动启动 + TTS 统一 18060）
- 本项目只允许用户双击脚本手动启动：NightGate 看门狗（C:\Users\dapanji\night_gate.ps1，管 D:\xm 全部 python）已在 Get-TargetProcesses 加 duihuamoxing 永久排除并删除 night_gate_services.json 里本项目 3 条注册（曾把 TTS/8088旧open-webui 每10分钟自动复活=「关不掉」元凶）；计划任务 AIRI_TTS8060 已禁用；Cloudflared 服务已停并改 Manual（公网上线.bat 的 net start 对 Manual 照常有效）
- TTS 端口统一 18060（原任务通道 8060/手动通道 8061 合并），WebUI 数据库 audio.tts.openai.api_base_url 已同步；AIRI 侧 TTS 地址仍指 8060，需用户在 AIRI 设置自行改 http://127.0.0.1:18060/v1
- 8088 端口不可改：cloudflared 云端（token 远程管理）映射指向 localhost:8088，改本地网关端口会断公网
- 8088 上的 open-webui = NightGate 复活的旧实例抢占，与登录网关无关；再见到直接杀即可，不会再被复活
### 关键点（2026-09-11 朗读英文 500 修复 + 冒烟测试）
- **朗读含英文字母必 500 的坑**：文本含英文（AI/OK/Hello/中英混排）时 GPT-SoVITS 走 `GPT_SoVITS\text\english.py` → `g2p_en` → nltk `cmudict`；`runtime\py312\nltk_data` 下缺 `corpora/cmudict` 就 `LookupError: Resource 'cmudict' not found` → HTTP 500。纯中文走不到该分支，所以表现为 `/tts` 正常而 `/v1/audio/speech`（Open WebUI 实际朗读通道）挂掉，容易误判。已补 `corpora/cmudict` + `taggers/averaged_perceptron_tagger_eng`（后者原本就在，是之前只修了一半）。
- 新增 `scripts\setup_nltk_data.py`（幂等：先复制本机 `%APPDATA%\nltk_data`，再联网下载，最后校验 g2p_en）。`runtime\` 不入库，**换机器必须重跑**；DEPLOY.md 第 4 节第 5 步与第 11 节排查已记录。
- 新增 `tests\smoke_e2e.py`：四服务端到端冒烟（Ollama 真推理 / WebUI health+config+首页 / 数字人 libs+页面 / TTS wav+OpenAI 兼容 mp3），产物落 `tests\_smoke_out\`。
