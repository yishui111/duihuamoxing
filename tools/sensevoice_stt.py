# -*- coding: utf-8 -*-
"""
SenseVoice 语音识别子进程脚本（Open WebUI 语音输入用）
=============================================================
用法: python sensevoice_stt.py <音频文件路径>
输出: 识别文本（stdout，UTF-8）

说明:
- 用 runtime\\py312 的 python 运行（该环境装有 funasr 1.4.1）
- 模型在 data\\asr_models\\SenseVoiceSmall（本地，无需联网）
- 支持中文/粤语等方言自动识别，输出简体 + 数字/标点归一化
"""
import logging
import os
import re
import sys

# 屏蔽 funasr/ctranslate2 的 INFO/WARNING 打印（会污染 stdout 识别结果）
logging.disable(logging.WARNING)
sys.stdout.reconfigure(encoding='utf-8')

MODEL_DIR = os.getenv(
    'SENSEVOICE_MODEL_DIR',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'asr_models', 'SenseVoiceSmall'),
)

_model = None


def get_model():
    global _model
    if _model is None:
        import contextlib
        import io
        from funasr import AutoModel
        # 把加载过程的 print 输出吞掉，避免污染 stdout
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            _model = AutoModel(
                model=MODEL_DIR,
                trust_remote_code=True,
                disable_update=True,
                disable_pbar=True,
                device='cpu',
            )
    return _model


def clean(text):
    # 去掉 <|zh|> <|NEUTRAL|> <|Speech|> <|withitn|> 等标记
    return re.sub(r'<\|[^|]+\|>', '', text or '').strip()


def main():
    if len(sys.argv) < 2:
        print('用法: python sensevoice_stt.py <音频文件>', file=sys.stderr)
        sys.exit(2)
    audio = sys.argv[1]
    if not os.path.isfile(audio):
        print(f'音频文件不存在: {audio}', file=sys.stderr)
        sys.exit(1)
    model = get_model()
    res = model.generate(input=audio, language='auto', use_itn=True, batch_size_s=60)
    text = clean(res[0]['text']) if res else ''
    print(text)


if __name__ == '__main__':
    main()
