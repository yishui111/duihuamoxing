# AGENTS.md — 知音 ZhiYin 综合 AI 对话系统 项目档案

> ⚠️ 修改本仓库前先读本文件（AI 助手/开发者项目记忆）。用户向文档见 README.md / DEPLOY.md / 使用说明.md。

## 1. 定位
本地私有四合一综合 AI 对话系统：**对话 + 知识库 + 数字人 + 朗读**，一键全启动、数据不出门。品牌名「知音 ZhiYin」。兄弟仓库 yumingbushu（Cloudflare Tunnel 部署工作台）与本仓库同级放置可发布公网。

## 2. 端口 / 组件
| 端口 | 组件 |
| ---- | ---- |
| 8088 | Open WebUI（对话+知识库；loader.js 前端增强） |
| 11434 | Ollama（qwen2.5:7b 本地对话 / bge-m3 RAG 向量） |
| 48620 | 自研数字人（avatar_server.py 纯标准库嘴型驱动，素材建库由用户视频自建） |
| 8061 | GPT-SoVITS 训练音色朗读（文字驱动语音/tts_service/tts_api.py 封装，失败自动回退系统语音） |

结构：对话系统/、数字人/、文字驱动语音/、共享资源/、tools/（人格蒸馏工具，纯标准库）、scripts/（11 个自研运维脚本，路径已相对化）、tests/、docs/、loader.js（单文件前端增强，个人域名已改可配置 window.__DSH_AVATAR_REMOTE__，默认本机）。

## 3. 公开版边界（不入库）
venv/、runtime/、data/（open-webui 库/用户数据/ollama 模型）、log/、sessions/（真实人格会话）、ziliao/、.extract_tmp/、_edge_test/（浏览器 profile）、patched/、py-xiaozhi 与 xiaozhi-server 与 shumeipai 与 树莓派小智（第三方小智开源副本，后者含 pi@192.168.1.15 LAN 凭据）、GPT-SoVITS 引擎与角色音色模型、数字人 avatar_libs/avatar_input（真人脸图素材）、两枚 image.tar、.webui_secret_key、真实个人资料文档（仅留虚构模板）、_scan_login.py/_auth_dom.html（登录页探测脚本，一律弃传）。
> 大件装配路径与下载命令全在 DEPLOY.md；真人声音/形象素材绝不入库。

## 4. 特殊约定
- 4 个含中文目录调用的 bat（启动.bat/关闭.bat/一键启动全部.bat/一键关闭全部.bat 及文字驱动语音\启动.bat）= **GBK + chcp936**（与原件一致，中文 Windows 正常运行；勿转 UTF-8、勿去 chcp，否则找不到中文目录）。其余 bat 纯 ASCII+CRLF+无 BOM。
- 三子项目 README 均注明模型/引擎/素材按根 DEPLOY.md 准备。
- 提交 `git push origin main`；中文文档 UTF-8。
---
### 关键点（2026-09-02 上传整理补充）
- 知音 ZhiYin 四合一：8088 Open WebUI / 11434 Ollama / 48620 自研数字人(avatar_server.py 纯标准库) / 8061 GPT-SoVITS 朗读(tts_service/tts_api.py)
- 4 个含中文目录调用的 bat（启动/关闭/一键启动全部/一键关闭全部）= GBK + chcp936，勿转 UTF-8、勿去 chcp（否则找不到中文目录）
- _scan_login.py / _auth_dom.html（登录页探测）一律弃传；loader.js 个人域名已改可配置(window.__DSH_AVATAR_REMOTE__，默认本机)
- 大件装配全在 DEPLOY.md：Ollama 便携+模型(qwen2.5:7b/bge-m3)、open-webui(pip)、GPT-SoVITS 引擎、whisper(scripts\download_whisper.py)、ffmpeg
- data/sessions/log/真人素材/人格档案 不入库；与 yumingbushu 同级目录放置可发布公网
