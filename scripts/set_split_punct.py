# -*- coding: utf-8 -*-
"""Open WebUI 朗读分段策略恢复为按标点分段（PUNCTUATION，默认行为）。

用法: python scripts/set_split_punct.py
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
    "UPDATE config SET value=? WHERE key='audio.tts.split_on'",
    (json.dumps("PUNCTUATION"),),
)
db.commit()
cur.execute("SELECT value FROM config WHERE key='audio.tts.split_on'")
print("audio.tts.split_on =", cur.fetchone()[0])
db.close()
