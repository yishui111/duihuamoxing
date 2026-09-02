# -*- coding: utf-8 -*-
"""修复 Open WebUI 数据库中的 Ollama 地址配置为本地服务。

背景：RAG 嵌入/对话报 InvalidUrlClientError 多为 webui.db config 里的
ollama.base_urls / rag.ollama.base_url 是空值或旧环境遗留地址（如容器时代地址）。
本脚本统一改写为 http://localhost:11434。

用法: python scripts/fix_ollama_url.py   （需先停止 Open WebUI，改完再启动）
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

db = sqlite3.connect(DB)
cur = db.cursor()
cur.execute(
    "UPDATE config SET value=? WHERE key='ollama.base_urls'",
    (json.dumps(["http://localhost:11434"]),),
)
cur.execute(
    "UPDATE config SET value=? WHERE key='rag.ollama.base_url'",
    (json.dumps("http://localhost:11434"),),
)
db.commit()
cur.execute(
    "SELECT key, value FROM config WHERE key IN ('ollama.base_urls','rag.ollama.base_url')"
)
for k, v in cur.fetchall():
    print(k, "=", v)
db.close()
print("已修正 Ollama 地址为 http://localhost:11434")
