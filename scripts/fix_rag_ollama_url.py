# -*- coding: utf-8 -*-
"""修复 rag.ollama.base_url（RAG 嵌入使用的 Ollama 地址）。

同 fix_ollama_url.py，只处理 rag.ollama.base_url 一项；改完需重启 Open WebUI。

用法: python scripts/fix_rag_ollama_url.py
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

db = sqlite3.connect(DB)
db.execute(
    "UPDATE config SET value=? WHERE key='rag.ollama.base_url'",
    (json.dumps("http://localhost:11434"),),
)
db.commit()
rows = db.execute(
    "select key, value from config where key='rag.ollama.base_url'"
).fetchall()
for k, v in rows:
    print(k, "=", v)
db.close()
print("已修正 rag.ollama.base_url = http://localhost:11434")
