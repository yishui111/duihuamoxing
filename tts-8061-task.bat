@echo off
rem TTS 语音服务启动器（8061）：由任务计划调用，带环境变量
set "TTS_API_PORT=8061"
set "GSV_MODELS_DIR=D:\xm\duihuamoxing\文字驱动语音\tts_service\models"
set "TTS_DEFAULT_VOICE=azhong"
set "TTS_DEVICE=cuda"
set "FFMPEG_PATH=D:\xm\duihuamoxing\runtime\ffmpeg\bin\ffmpeg.exe"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
"D:\xm\duihuamoxing\runtime\py312\python.exe" "D:\xm\duihuamoxing\文字驱动语音\tts_service\tts_api.py" > "D:\xm\zhuomianchunwu\airi\tts-run.log" 2>&1
