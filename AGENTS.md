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
| 8061 | GPT-SoVITS 训练音色朗读（文字驱动语音/tts_service/tts_api.py 封装，失败自动回退系统语音） |
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
- 知音 ZhiYin 四合一：8089 Open WebUI / 11434 Ollama / 48620 自研数字人(avatar_server.py 纯标准库) / 8061 GPT-SoVITS 朗读(tts_service/tts_api.py)
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
