# -*- coding: utf-8 -*-
"""批量修复 webui.db config 表中的非法 JSON 值。

背景：Open WebUI 迁移/断电后，config 表可能出现 NULL 或非 JSON 字符串，
前端读配置解析报错。本脚本把所有非法值修复为 JSON 空字符串 '""'，
并先把原库备份一份到 webui.db.broken-backup。

用法: python scripts/fix_config_json.py   （需先停止 Open WebUI）
"""
import json
import os
import shutil
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

shutil.copy2(DB, DB + ".broken-backup")
print("已备份原库到:", DB + ".broken-backup")

db = sqlite3.connect(DB)
cur = db.cursor()
cur.execute("SELECT key, value FROM config")
rows = cur.fetchall()
fixed = 0
for k, v in rows:
    if v is None:
        cur.execute("UPDATE config SET value='\"\"' WHERE key=?", (k,))
        fixed += 1
    else:
        try:
            json.loads(v)
        except Exception:
            cur.execute("UPDATE config SET value='\"\"' WHERE key=?", (k,))
            fixed += 1
db.commit()
print("修复行数:", fixed)
db.close()
