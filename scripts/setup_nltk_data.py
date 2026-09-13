# -*- coding: utf-8 -*-
"""补齐 GPT-SoVITS 英文 G2P 依赖的 NLTK 语料到 runtime\\py312\\nltk_data（幂等）。

背景（2026-09-11 实测）：
    朗读文本里只要含英文字母（"AI" / "OK" / "Hello" / 中英混排），
    GPT-SoVITS 的 text/english.py 就会 `en_G2p()` -> nltk `cmudict.dict()`。
    若 runtime\\py312\\nltk_data 下缺 corpora/cmudict，合成直接抛
    LookupError 并返回 HTTP 500，前端表现为"朗读用不了"。
    纯中文文本走不到该分支，所以 `/tts` 可能正常而 `/v1/audio/speech` 挂掉。

需要的两份语料：
    corpora/cmudict                       （英文发音词典，g2p_en 必需）
    taggers/averaged_perceptron_tagger_eng（nltk 3.9+ 词性标注，g2p_en 必需）

用法: python scripts\\setup_nltk_data.py
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NLTK_DIR = os.path.join(ROOT, "runtime", "py312", "nltk_data")

# (类别, 名称) —— nltk 的 subdir/name 结构
NEEDED = [
    ("corpora", "cmudict"),
    ("taggers", "averaged_perceptron_tagger_eng"),
]

# 本机可能已存在的备用来源（按序尝试，第一个命中的整目录复制过来）
# 注意：环境变量在部分启动方式下为空，故同时硬编码经典位置
_HOME = os.path.expanduser("~")
FALLBACK_ROOTS = [
    os.path.join(os.environ.get("APPDATA", "") or "", "nltk_data"),
    os.path.join(os.environ.get("LOCALAPPDATA", "") or "", "nltk_data"),
    os.path.join(_HOME, "nltk_data"),
    os.path.join(_HOME, "AppData", "Roaming", "nltk_data"),
]


def _present(subdir, name):
    d = os.path.join(NLTK_DIR, subdir, name)
    return os.path.isdir(d) and bool(os.listdir(d))


def _copy_from_local(subdir, name):
    """从本机其他 nltk_data 目录整目录复制（离线可用）。"""
    for root in FALLBACK_ROOTS:
        if not root or not os.path.isdir(root):
            continue
        src = os.path.join(root, subdir, name)
        if os.path.isdir(src) and os.listdir(src):
            dst = os.path.join(NLTK_DIR, subdir, name)
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return root
    return None


def _download(subdir, name):
    """联网下载（国内直连 raw.githubusercontent.com 常失败，失败不致命）。"""
    try:
        import nltk
    except ImportError:
        return "nltk 未安装"
    os.makedirs(NLTK_DIR, exist_ok=True)
    ok = nltk.download(name, download_dir=NLTK_DIR, quiet=True)
    return None if ok else "下载失败"


def main():
    print("NLTK 语料目标目录: %s" % NLTK_DIR)
    os.makedirs(NLTK_DIR, exist_ok=True)
    failed = []
    for subdir, name in NEEDED:
        if _present(subdir, name):
            print("  [已存在] %s/%s" % (subdir, name))
            continue
        src = _copy_from_local(subdir, name)
        if src:
            print("  [已复制] %s/%s  <- %s" % (subdir, name, src))
            continue
        err = _download(subdir, name)
        if err is None and _present(subdir, name):
            print("  [已下载] %s/%s" % (subdir, name))
        else:
            print("  [失败]   %s/%s  (%s)" % (subdir, name, err))
            failed.append("%s/%s" % (subdir, name))

    if failed:
        print("\n以下语料仍缺失: %s" % ", ".join(failed))
        print("可手动下载 https://github.com/nltk/nltk_data 对应包，")
        print("解压到 %s 下，或把其他机器 %%APPDATA%%\\nltk_data 里同名目录复制过来。" % NLTK_DIR)
        return 1

    # 真实校验：能否 import 到 g2p_en 的完整链路
    print("\n校验 g2p_en ...")
    try:
        from g2p_en import G2p
        out = G2p()("Hello AI")
        print("  [通过] Hello AI -> %s" % " ".join(out).replace("  ", " | "))
    except Exception as exc:  # noqa: BLE001
        print("  [警告] g2p_en 校验失败: %s: %s" % (type(exc).__name__, exc))
        return 1
    print("\n完成：朗读中英混排文本不再报 cmudict 缺失。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
