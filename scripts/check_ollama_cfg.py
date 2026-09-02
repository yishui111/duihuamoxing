# -*- coding: utf-8 -*-
"""查看 Open WebUI 数据库中的 Ollama/嵌入相关配置（排查 RAG 500 用）。

用法: python scripts/check_ollama_cfg.py
数据库位置: <仓库根>/data/open-webui/webui.db（首次启动 Open WebUI 后生成）
"""
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

db = sqlite3.connect(DB)
rows = db.execute(
    "select key, value from config where key like '%ollama%' or key like '%embed%'"
).fetchall()
for k, v in rows:
    print(k, "=", v)
db.close()
