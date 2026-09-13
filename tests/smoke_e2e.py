# -*- coding: utf-8 -*-
"""知音 ZhiYin 四服务端到端冒烟测试（只走真实 HTTP，不依赖内部实现）。"""
import json
import os
import time
import urllib.request
import urllib.error
import uuid

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke_out")
os.makedirs(OUT, exist_ok=True)

FAIL = []


def _req(url, data=None, headers=None, timeout=600, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    return r.status, body, time.time() - t0


def post_json(url, payload, timeout=600):
    return _req(url, json.dumps(payload).encode("utf-8"),
                {"Content-Type": "application/json"}, timeout)


def get(url, timeout=30):
    return _req(url, timeout=timeout)


def check(name, ok, detail=""):
    print(("  [PASS] " if ok else "  [FAIL] ") + name + ("  " + detail if detail else ""))
    if not ok:
        FAIL.append(name)


print("=" * 60)
print("1) Ollama 对话模型 qwen2.5:7b 真实推理")
print("=" * 60)
try:
    st, body, dt = post_json("http://127.0.0.1:11434/api/chat", {
        "model": "qwen2.5:7b",
        "messages": [{"role": "user", "content": "用一句话介绍你自己"}],
        "stream": False,
    }, timeout=600)
    d = json.loads(body.decode("utf-8"))
    reply = (d.get("message") or {}).get("content", "")
    print("  回复:", reply[:120].replace("\n", " "))
    print("  耗时: %.1fs  首字加载含模型冷启" % dt)
    check("Ollama 对话返回非空", bool(reply.strip()), "%d 字" % len(reply))
except Exception as e:
    check("Ollama 对话返回非空", False, "%s: %s" % (type(e).__name__, e))

print()
print("=" * 60)
print("2) Open WebUI 8089")
print("=" * 60)
try:
    st, body, dt = get("http://127.0.0.1:8089/health")
    check("WebUI /health", st == 200, body.decode("utf-8", "ignore")[:60])
    st, body, dt = get("http://127.0.0.1:8089/api/config")
    cfg = json.loads(body.decode("utf-8"))
    check("WebUI /api/config", st == 200,
          "name=%s auth=%s" % (cfg.get("name"), (cfg.get("features") or {}).get("auth", "?")))
    st, body, dt = get("http://127.0.0.1:8089/")
    check("WebUI 首页 HTML", st == 200 and len(body) > 1000, "%d 字节" % len(body))
except Exception as e:
    check("WebUI 服务可用", False, "%s: %s" % (type(e).__name__, e))

print()
print("=" * 60)
print("3) 数字人 48620")
print("=" * 60)
try:
    st, body, dt = get("http://127.0.0.1:48620/api/libs")
    libs = json.loads(body.decode("utf-8")).get("libs", [])
    check("数字人 /api/libs", st == 200 and len(libs) > 0, "%d 个素材库" % len(libs))
    st, body, dt = get("http://127.0.0.1:48620/web/index.html")
    check("数字人页面 /web/index.html", st == 200 and len(body) > 500, "%d 字节" % len(body))
except Exception as e:
    check("数字人服务可用", False, "%s: %s" % (type(e).__name__, e))

print()
print("=" * 60)
print("4) TTS 朗读 18060 —— 训练音色合成")
print("=" * 60)
try:
    st, body, dt = get("http://127.0.0.1:18060/health")
    h = json.loads(body.decode("utf-8"))
    check("TTS /health", st == 200, "device=%s roles=%d" % (h.get("device"), len(h.get("ready_roles", []))))
except Exception as e:
    check("TTS /health", False, "%s: %s" % (type(e).__name__, e))

# 4a. 原生 /tts 表单接口（wav）
try:
    boundary = "----smoke" + uuid.uuid4().hex
    fields = {"text": "你好，我是知音，现在朗读功能测试正常。", "character": "azhong", "speed": "1.0"}
    parts = []
    for k, v in fields.items():
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, k, v)).encode("utf-8"))
    parts.append(("--%s--\r\n" % boundary).encode("utf-8"))
    payload = b"".join(parts)
    st, body, dt = _req("http://127.0.0.1:18060/tts", payload,
                        {"Content-Type": "multipart/form-data; boundary=" + boundary}, timeout=900)
    wav = os.path.join(OUT, "tts_azhong.wav")
    with open(wav, "wb") as f:
        f.write(body)
    check("TTS /tts 合成 wav", st == 200 and len(body) > 10000,
          "%d 字节  耗时 %.1fs  -> %s" % (len(body), dt, os.path.basename(wav)))
except Exception as e:
    check("TTS /tts 合成 wav", False, "%s: %s" % (type(e).__name__, e))

# 4b. OpenAI 兼容接口（mp3，Open WebUI 实际调用路径）
try:
    st, body, dt = post_json("http://127.0.0.1:18060/v1/audio/speech", {
        "model": "azhong", "voice": "azhong",
        "input": "这是通过 OpenAI 兼容接口合成的语音。",
    }, timeout=900)
    mp3 = os.path.join(OUT, "tts_openai.mp3")
    with open(mp3, "wb") as f:
        f.write(body)
    check("TTS /v1/audio/speech 合成 mp3", st == 200 and len(body) > 5000,
          "%d 字节  耗时 %.1fs  -> %s" % (len(body), dt, os.path.basename(mp3)))
except Exception as e:
    check("TTS /v1/audio/speech 合成 mp3", False, "%s: %s" % (type(e).__name__, e))

print()
print("=" * 60)
if FAIL:
    print("结果: %d 项失败 -> %s" % (len(FAIL), FAIL))
else:
    print("结果: 全部通过")
print("产物目录:", OUT)
print("=" * 60)
