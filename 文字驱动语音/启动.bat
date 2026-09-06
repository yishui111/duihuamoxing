@echo off
chcp 936 >nul
cd /d "%~dp0"
title ZhiYin Text-to-Speech Service

echo ========================================
echo   Text-to-Speech Service (GPT-SoVITS) - Start
echo ========================================
echo.
set "ROOT=%~dp0.."

rem ---------- 1. Check voice models ----------
echo [1/3] Checking voice models...
set "GSV_MODELS_DIR=%~dp0tts_service\models"
if not exist "%GSV_MODELS_DIR%" (
    echo [ERROR] Voice model directory not found: tts_service\models
    pause
    exit /b 1
)
powershell -NoProfile -Command "$d='%GSV_MODELS_DIR%'; $ok=$false; Get-ChildItem $d -Directory | ForEach-Object { $hasCkpt = (Get-ChildItem $_.FullName -Filter '*.ckpt' -ErrorAction SilentlyContinue | Select-Object -First 1); $hasPth = (Get-ChildItem $_.FullName -Filter '*.pth' -ErrorAction SilentlyContinue | Select-Object -First 1); if ($hasCkpt -and $hasPth -and (Test-Path (Join-Path $_.FullName 'ref.wav'))) { $ok=$true } }; if ($ok) { exit 0 } else { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No complete voice model found under tts_service\models.
    echo         Each role folder needs: .ckpt + .pth + ref.wav + ref_text.txt
    echo         See 模型放置与使用.md - model placement guide.
    pause
    exit /b 1
)
echo      Voice model check passed.

rem ---------- 2. Check service status ----------
echo [2/3] Checking service status...
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8061/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      TTS service already running.
    goto ok
)

rem ---------- 3. Inference device ----------
echo [3/3] Detecting inference device...
set "TTS_DEVICE=cuda"
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "$g = @(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null); if ($g.Count -gt 0) { $m = [int]($g[0].Trim()); if ($m -lt 10240) { 'cpu' } else { 'cuda' } } else { 'cuda' }"`) do set "TTS_DEVICE=%%v"
echo      Inference device: %TTS_DEVICE%
echo      Starting TTS service (first model load 1-3 min)...
set "TTS_API_PORT=8061"
set "TTS_DEFAULT_VOICE=azhong"
if not exist "%ROOT%\log" mkdir "%ROOT%\log"
powershell -NoProfile -Command "$env:TTS_API_PORT='8061'; $env:GSV_MODELS_DIR='%GSV_MODELS_DIR%'; $env:TTS_DEFAULT_VOICE='azhong'; $env:TTS_DEVICE='%TTS_DEVICE%'; $env:FFMPEG_PATH='%ROOT%\runtime\ffmpeg\bin\ffmpeg.exe'; $p = Start-Process -FilePath '%ROOT%\runtime\py312\python.exe' -ArgumentList '%~dp0tts_service\tts_api.py' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%ROOT%\log\tts.log' -RedirectStandardError '%ROOT%\log\tts.err.log'; $p.Id | Out-File -FilePath '%ROOT%\data\tts.pid' -Encoding ascii"
set /a n=0
:wait
set /a n+=1
if %n% gtr 60 (
    echo [WARN] TTS service start timeout.
    goto ok
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8061/health' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto ok
ping -n 5 127.0.0.1 >nul
goto wait
:ok
echo.
echo ========================================
echo   TTS service started!
echo   Service:  http://127.0.0.1:8061
echo   Health:   http://127.0.0.1:8061/health
echo ========================================
echo.
pause
