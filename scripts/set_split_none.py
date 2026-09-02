# -*- coding: utf-8 -*-
"""Open WebUI 朗读分段策略设为 none：整段一次合成、一次播放。

背景：按标点分段时，若某段合成失败/中断会出现"读一半就停"。
SPLIT_ON=none 可避免该问题（对自定义 TTS 服务更稳）。

用法: python scripts/set_split_none.py
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
    (json.dumps("none"),),
)
db.commit()
cur.execute("SELECT value FROM config WHERE key='audio.tts.split_on'")
print("audio.tts.split_on =", cur.fetchone()[0])
db.close()
