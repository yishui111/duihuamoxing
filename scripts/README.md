# scripts —— 运维/修复小工具（自研）

部署与排障时用到的自研脚本（从项目开发期沉淀），按需运行，均有幂等/备份保护。

## loader 集成

| 脚本 | 作用 |
|------|------|
| `inline_loader.py` | 把根目录 `loader.js` 内联进 venv 中 open-webui 前端的 `index.html`（原生部署**必需**，幂等） |

```bash
python scripts\inline_loader.py                 # 默认找 <仓库根>\venv 下的 open_webui
python scripts\inline_loader.py --venv <路径>    # 自定义虚拟环境
```

## Open WebUI 数据库配置修复（webui.db）

这些脚本读取 <仓库根>\data\open-webui\webui.db（首次启动 Open WebUI 后自动生成）。
**修改 config 表的脚本建议先停 open-webui，改完再启动。**

| 脚本 | 作用 |
|------|------|
| `check_ollama_cfg.py` | 查看 ollama/嵌入相关配置（排查 RAG 500） |
| `check_tts_cfg.py` | 查看音频/TTS 配置 |
| `fix_ollama_url.py` | 修正 ollama.base_urls / rag.ollama.base_url → `http://localhost:11434` |
| `fix_rag_ollama_url.py` | 同上，只修 rag.ollama.base_url |
| `fix_relevance_threshold.py` | 修 rag.relevance_threshold 为 JSON 数字 0.0（空串会导致检索 500） |
| `fix_config_json.py` | 批量修复 config 表非法 JSON（先备份为 webui.db.broken-backup） |
| `set_voice_azhong.py` | 朗读音色设为默认角色（`TTS_VOICE` 环境变量可指定其他角色） |
| `set_split_none.py` | 朗读分段策略 = none（整段合成，避免"读一半停"） |
| `set_split_punct.py` | 恢复按标点分段（默认行为） |

## 模型下载

| 脚本 | 作用 |
|------|------|
| `download_whisper.py` | 用 hf-mirror 国内镜像下载 faster-whisper-small 到 Open WebUI 语音识别缓存（需先 `pip install huggingface_hub`） |

```bash
python scripts\download_whisper.py
```

## 备注

- 这些脚本默认假设仓库结构：`venv`、`data\open-webui`、`loader.js` 均在仓库根目录；
- 目录不在 Git 内的大件（venv/data/runtime）请先按 `DEPLOY.md` 部署好再运行。
