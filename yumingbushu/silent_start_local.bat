@echo off
rem Silent start of local ZhiYin services (no browser window). Project root = parent folder.
rem Used by auto_health_check.bat.
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
set "WEBUI_EXE=%PROJECT%\venv\Scripts\open-webui.exe"
rem Same Ollama settings as the main start script (models live inside the project)
set "OLLAMA_MODELS=%PROJECT%\data\ollama\models"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_FLASH_ATTENTION=true"
set "OLLAMA_GPU_OVERHEAD=1024"
set "OLLAMA_NUM_PARALLEL=1"

rem --- Ollama ---
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%OLLAMA_EXE%" (
        if not exist "%PROJECT%\log" mkdir "%PROJECT%\log"
        powershell -NoProfile -Command "$proc = Start-Process -FilePath '%OLLAMA_EXE%' -ArgumentList 'serve' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%PROJECT%\log\ollama.log' -RedirectStandardError '%PROJECT%\log\ollama.err.log'"
    )
)

rem --- Open WebUI ---
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8088/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 exit /b 0

set "DATA_DIR=%PROJECT%\data\open-webui"
set "WEBUI_AUTH=True"
set "WEBUI_NAME=ZhiYin"
set "OFFLINE_MODE=true"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "OLLAMA_BASE_URL=http://localhost:11434"
set "OPENAI_API_BASE_URL=http://localhost:11434/v1"
set "RAG_EMBEDDING_ENGINE=ollama"
set "RAG_EMBEDDING_MODEL=bge-m3"
set "RAG_EMBEDDING_MODEL_EMBEDDING_DIMENSION=1024"
set "ENABLE_MEMORY_SYSTEM_CONTEXT=false"
set "ENABLE_MEMORY_BACKGROUND_REVIEW=false"
set "WHISPER_LANGUAGE=zh"
set "WHISPER_MODEL=small"
if not exist "%PROJECT%\log" mkdir "%PROJECT%\log"
powershell -NoProfile -Command "$env:OPENAI_API_KEY='ollama'; $proc = Start-Process -FilePath '%WEBUI_EXE%' -WorkingDirectory '%PROJECT%' -ArgumentList 'serve','--port','8088','--host','0.0.0.0' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%PROJECT%\log\webui.log' -RedirectStandardError '%PROJECT%\log\webui.err.log'"
exit /b 0
