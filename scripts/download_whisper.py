# -*- coding: utf-8 -*-
"""用 hf-mirror 国内镜像下载 faster-whisper-small 到 Open WebUI 语音识别模型目录。

Open WebUI 的语音输入依赖本地 Whisper 模型（WHISPER_MODEL=small）；
国内网络直连 HuggingFace 容易失败，本脚本走 hf-mirror.com 下载并校验完整。

用法: python scripts/download_whisper.py   （需已安装 huggingface_hub：pip install huggingface_hub）
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHISPER_DIR = os.path.join(ROOT, "data", "open-webui", "cache", "whisper", "models")

# 1. 清掉残缺缓存（避免 incomplete snapshot 干扰）
if os.path.isdir(WHISPER_DIR):
    for name in os.listdir(WHISPER_DIR):
        p = os.path.join(WHISPER_DIR, name)
        if name == "CACHEDIR.TAG":
            continue
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        else:
            try:
                os.remove(p)
            except OSError:
                pass
    print("已清理残缺缓存")
else:
    os.makedirs(WHISPER_DIR, exist_ok=True)

# 2. 走国内镜像下载完整模型
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_OFFLINE"] = "0"

from huggingface_hub import snapshot_download  # noqa: E402

path = snapshot_download(
    "Systran/faster-whisper-small",
    cache_dir=WHISPER_DIR,
    local_files_only=False,
)
print("下载完成:", path)

# 3. 验证关键文件存在且非空
snap = os.path.join(WHISPER_DIR, "models--Systran--faster-whisper-small", "snapshots")
if os.path.isdir(snap):
    for rev in os.listdir(snap):
        revdir = os.path.join(snap, rev)
        if os.path.isdir(revdir):
            for f in ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt", "preprocessor_config.json"]:
                fp = os.path.join(revdir, f)
                sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
                print("  %-28s %s" % (f, ("%d bytes" % sz) if sz else "MISSING!"))
else:
    print("警告: 未找到 snapshot 目录，请检查下载是否完整")
