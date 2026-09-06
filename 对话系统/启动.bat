@echo off
cd /d "%~dp0"
title ZhiYin Chat System

echo ========================================
echo   ZhiYin Chat System - Start
echo ========================================
echo.
set "ROOT=%~dp0.."
if not exist "%ROOT%\log" mkdir "%ROOT%\log"
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
set "WEBUI_EXE=%ROOT%\venv\Scripts\open-webui.exe"

rem ---------- 1. Ollama ----------
echo [1/2] Checking Ollama...
if not exist "%OLLAMA_EXE%" (
    echo [ERROR] Ollama not found. Please install Ollama first (see DEPLOY.md).
    pause
    exit /b 1
)
set "OLLAMA_MODELS=%ROOT%\data\ollama\models"
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
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%OLLAMA_EXE%' -ArgumentList 'serve' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%ROOT%\log\ollama.log' -RedirectStandardError '%ROOT%\log\ollama.err.log'"
if not exist "%ROOT%\log" mkdir "%ROOT%\log"
set /a n=0
:ollamawait
set /a n+=1
if %n% gtr 30 (
    echo [ERROR] Ollama start timeout.
    pause
    exit /b 1
)
powershell -NoProfile -Command "$m = (Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3).models; if ($m -and ($m.name -contains 'qwen2.5:7b')) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto ollamaok
ping -n 4 127.0.0.1 >nul
goto ollamawait
:ollamaok
echo      Ollama ready (qwen2.5:7b + bge-m3).

rem ---------- 2. Open WebUI ----------
echo [2/2] Checking Open WebUI...
if not exist "%WEBUI_EXE%" (
    echo [ERROR] Open WebUI not found (venv not installed). See DEPLOY.md.
    pause
    exit /b 1
)
set "DATA_DIR=%ROOT%\data\open-webui"
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
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8089/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      Open WebUI already running.
    goto webuiok
)
echo      Starting Open WebUI (first start about 30s)...
if not exist "%ROOT%\log" mkdir "%ROOT%\log"
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%WEBUI_EXE%' -ArgumentList 'serve','--port','8089','--host','0.0.0.0' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%ROOT%\log\webui.log' -RedirectStandardError '%ROOT%\log\webui.err.log'"
set /a n=0
:webuiwait
set /a n+=1
if %n% gtr 30 (
    echo [WARN] Open WebUI start timeout. Check log\webui.err.log.
    goto webuiok
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8089/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto webuiok
ping -n 4 127.0.0.1 >nul
goto webuiwait
:webuiok
echo      Open WebUI ready (http://localhost:8089).
echo.
echo ========================================
echo   Chat System started!
echo   Chat UI: http://localhost:8089
echo ========================================
echo.
start "" "http://localhost:8089"
ping -n 11 127.0.0.1 >nul
exit /b 0
