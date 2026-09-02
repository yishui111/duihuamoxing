@echo off
cd /d "%~dp0"
title ZhiYin Avatar Service

echo ========================================
echo   Digital Human Avatar Service - Start
echo ========================================
echo.
set "ROOT=%~dp0.."
set "AVATAR_PORT=48620"
set "LIGHT_AVATAR_LIBS=%~dp0avatar_libs"
set "FFMPEG_PATH=%ROOT%\runtime\ffmpeg\bin\ffmpeg.exe"
set "FFPROBE_PATH=%ROOT%\runtime\ffmpeg\bin\ffprobe.exe"

powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:48620/api/libs' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    echo      Avatar service already running.
    goto ok
)
echo      Starting avatar service...
if not exist "%ROOT%\log" mkdir "%ROOT%\log"
powershell -NoProfile -Command "$proc = Start-Process -FilePath '%ROOT%\venv\Scripts\python.exe' -ArgumentList '%~dp0avatar_server.py' -WorkingDirectory '%~dp0' -WindowStyle Minimized -PassThru -RedirectStandardOutput '%ROOT%\log\avatar.log' -RedirectStandardError '%ROOT%\log\avatar.err.log'"
set /a n=0
:wait
set /a n+=1
if %n% gtr 12 (
    echo [WARN] Avatar service start timeout.
    goto ok
)
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:48620/api/libs' -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 goto ok
ping -n 4 127.0.0.1 >nul
goto wait
:ok
echo      Avatar service ready.
echo.
echo ========================================
echo   Avatar service started!
echo   Library tool: http://127.0.0.1:48620/web/preprocess.html
echo   Avatar page:  http://127.0.0.1:48620/web/index.html
echo ========================================
echo.
pause
