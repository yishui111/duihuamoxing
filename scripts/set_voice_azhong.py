# -*- coding: utf-8 -*-
"""把 Open WebUI 的朗读音色设为默认角色（默认 azhong，可用 TTS_VOICE 覆盖）。

用法: python scripts/set_voice_azhong.py
      TTS_VOICE=xxx python scripts/set_voice_azhong.py   # 指定其他角色名
改完在页面刷新即可（或重启 Open WebUI）。
"""
import json
import os
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "open-webui", "webui.db")
VOICE = os.environ.get("TTS_VOICE", "azhong")

if not os.path.isfile(DB):
    raise SystemExit("未找到 webui.db，请先启动一次 Open WebUI：%s" % DB)

db = sqlite3.connect(DB)
cur = db.cursor()
cur.execute(
    "UPDATE config SET value=? WHERE key='audio.tts.voice'",
    (json.dumps(VOICE),),
)
db.commit()
cur.execute("SELECT value FROM config WHERE key='audio.tts.voice'")
print("audio.tts.voice =", cur.fetchone()[0])
db.close()
print("朗读音色已设为:", VOICE)
