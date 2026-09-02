# -*- coding: utf-8 -*-
"""修复 rag.relevance_threshold（知识库检索阈值）类型错误。

背景：该值若是空字符串会与 float 比较报 TypeError（"" > 0.0），记忆/检索 500。
本脚本统一写回 JSON 数字 0.0（读取时动态生效，无需重启）。

用法: python scripts/fix_relevance_threshold.py
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

db = sqlite3.connect(DB)
rows = db.execute(
    "select key, value from config where key like 'rag.relevance%'"
).fetchall()
print("before:", rows)
db.execute(
    "UPDATE config SET value=? WHERE key='rag.relevance_threshold'",
    (json.dumps(0.0),),
)
db.commit()
rows = db.execute(
    "select key, value from config where key='rag.relevance_threshold'"
).fetchall()
print("after:", rows)
db.close()
