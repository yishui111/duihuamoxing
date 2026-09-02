@echo off
chcp 936 >nul
cd /d "%~dp0"
title ZhiYin - Start All (native, no Docker)

if not exist "%~dp0log" mkdir "%~dp0log"

echo.
echo  ========================================
echo    ZhiYin (Ollama + Open WebUI native)
echo    One-click start of all services
echo  ========================================
echo.

set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
set "WEBUI_EXE=%~dp0venv\Scripts\open-webui.exe"

rem ========== 1. Ollama native ==========
echo  [1/5] Checking Ollama...
if not exist "%OLLAMA_EXE%" (
    echo  [ERROR] Ollama not found. Please install Ollama first (see DEPLOY.md).
    pause
    exit /b 1
)
set "OLLAMA_MODELS=%~dp0data\ollama\models"
set "OLLAMA_KEEP_ALIVE=24h"
set "OLLAMA_FLASH_ATTENTION=true"
set "OLLAMA_GPU_OVERHEAD=1024"
set "OLLAMA_NUM_PARALLEL=1"
powershell -NoProfile -Command "$m = (Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3).models; if ($m -and ($m.name -contains 'qwen2.5:7b')) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      Ollama already running.
    goto ollamaok
)
echo      Starting Ollama service...
powershell -NoProfile -Command "Get-Process -Name 'ollama','ollama app' -ErrorAction SilentlyContinue | Stop-Process -Force"
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%OLLAMA_EXE%' -ArgumentList 'serve' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%~dp0log\ollama.log' -RedirectStandardError '%~dp0log\ollama.err.log'"
set /a n=0
:ollamawait
set /a n+=1
if %n% gtr 30 (
    echo  [ERROR] Ollama start timeout.
    pause
    exit /b 1
)
powershell -NoProfile -Command "$m = (Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3).models; if ($m -and ($m.name -contains 'qwen2.5:7b')) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto ollamaok
ping -n 4 127.0.0.1 >nul
goto ollamawait
:ollamaok
echo      Ollama ready (models: qwen2.5:7b + bge-m3).

rem ========== 2. Open WebUI native ==========
echo  [2/5] Checking Open WebUI...
if not exist "%WEBUI_EXE%" (
    echo  [ERROR] Open WebUI not found (venv not installed). See DEPLOY.md.
    pause
    exit /b 1
)
set "DATA_DIR=%~dp0data\open-webui"
set "WEBUI_AUTH=True"
set "WEBUI_NAME=ZhiYin"
set "OFFLINE_MODE=true"
set "HF_HUB_OFFLINE=1"
set "TRANSFORMERS_OFFLINE=1"
set "OLLAMA_BASE_URL=http://localhost:11434"
set "OPENAI_API_BASE_URL=http://localhost:11434/v1"
set "OPENAI_API_KEY=local"
set "RAG_EMBEDDING_ENGINE=ollama"
set "RAG_EMBEDDING_MODEL=bge-m3"
set "RAG_EMBEDDING_MODEL_EMBEDDING_DIMENSION=1024"
set "ENABLE_MEMORY_SYSTEM_CONTEXT=false"
set "ENABLE_MEMORY_BACKGROUND_REVIEW=false"
set "WHISPER_LANGUAGE=zh"
set "WHISPER_MODEL=small"
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8088/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      Open WebUI already running.
    goto webuiok
)
echo      Starting Open WebUI (first start about 30s)...
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%WEBUI_EXE%' -ArgumentList 'serve','--port','8088','--host','0.0.0.0' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%~dp0log\webui.log' -RedirectStandardError '%~dp0log\webui.err.log'"
set /a n=0
:webuiwait
set /a n+=1
if %n% gtr 30 (
    echo  [WARN] Open WebUI start timeout. Check log\webui.err.log.
    goto webuiwarn
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8088/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto webuiok
ping -n 4 127.0.0.1 >nul
goto webuiwait
:webuiok
echo      Open WebUI ready (http://localhost:8088).
:webuiwarn

rem ========== 3. Warm up chat model ==========
echo  [3/5] Warming up chat model qwen2.5:7b...
set /a n=0
:preheat
set /a n+=1
powershell -NoProfile -Command "$body = @{model='qwen2.5:7b'; messages=@(@{role='user';content='hi'}); stream=$false} | ConvertTo-Json -Depth 5; try { Invoke-RestMethod -Uri 'http://localhost:11434/api/chat' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 60 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto preheated
if %n% gtr 3 (
    echo  [WARN] Warm-up timeout. First chat may be slow.
    goto preheatwarn
)
echo      Warming up... (attempt %n%, first model load 1-3 min)
ping -n 8 127.0.0.1 >nul
goto preheat
:preheated
echo      Model warm-up done.
:preheatwarn

rem ========== 4. Built-in TTS voice service (8061) ==========
echo  [4/5] Checking built-in TTS voice service (trained voice, port 8061)...
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8061/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      TTS service already running (8061), reading uses trained voice.
    goto tts_finish
)
echo      Starting built-in TTS service (CPU mode if VRAM < 10GB; chat unaffected)...
set "TTS_DEVICE=cuda"
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$g = (nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null); if ($g) { $m = [int]($g[0].Trim()); if ($m -lt 10240) { 'cpu' } else { 'cuda' } } else { 'cuda' }"`) do set "TTS_DEVICE=%%v"
echo      Inference device: %TTS_DEVICE%
powershell -NoProfile -Command "$env:TTS_API_PORT='8061'; $env:GSV_MODELS_DIR='%~dp0文字驱动语音\tts_service\models'; $env:TTS_DEFAULT_VOICE='azhong'; $env:TTS_DEVICE='%TTS_DEVICE%'; $p = Start-Process -FilePath '%~dp0runtime\py312\python.exe' -ArgumentList '%~dp0文字驱动语音\tts_service\tts_api.py' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%~dp0log\tts.log' -RedirectStandardError '%~dp0log\tts.err.log'; $p.Id | Out-File -FilePath '%~dp0data\tts.pid' -Encoding ascii"
set /a n=0
:ttswait
set /a n+=1
if %n% gtr 40 (
    echo  [WARN] TTS start timeout. Reading falls back to system voice.
    goto tts_finish
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8061/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      TTS service ready (8061), reading uses trained voice.
    goto tts_finish
)
ping -n 5 127.0.0.1 >nul
goto ttswait
:tts_finish

rem ========== 5. Digital human avatar service (48620) ==========
echo  [5/5] Digital human avatar service (light-avatar:48620)...
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:48620/api/libs' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      Avatar service already running (48620).
    goto av_ok
)
echo      Starting avatar service (lightweight Python, low memory)...
set "LIGHT_AVATAR_LIBS=%~dp0数字人\avatar_libs"
set "AVATAR_PORT=48620"
set "FFMPEG_PATH=%~dp0runtime\ffmpeg\bin\ffmpeg.exe"
set "FFPROBE_PATH=%~dp0runtime\ffmpeg\bin\ffprobe.exe"
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%~dp0venv\Scripts\python.exe' -ArgumentList '%~dp0数字人\avatar_server.py' -WorkingDirectory '%~dp0数字人' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%~dp0log\avatar.log' -RedirectStandardError '%~dp0log\avatar.err.log'"
set /a n=0
:avwait
set /a n+=1
if %n% gtr 12 (
    echo  [WARN] Avatar start timeout. Face panel unavailable (chat unaffected).
    goto av_done
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:48620/api/libs' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto av_ok
ping -n 4 127.0.0.1 >nul
goto avwait
:av_ok
echo      Avatar service ready (choose a person in the avatar menu).
:av_done

echo.
echo  ========================================
echo    Startup complete!
echo    Chat UI: http://localhost:8088
echo  ========================================
echo.
start "" "http://localhost:8088"
ping -n 11 127.0.0.1 >nul
exit /b 0
