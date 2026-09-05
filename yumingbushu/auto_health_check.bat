@echo off
rem Auto health check: restart local services if Open WebUI (8088) is down.
rem Intended to run periodically via Task Scheduler.
setlocal
set "WEBUI_OK="
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://localhost:8088/health' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
)
echo [%date% %time%] Open WebUI down, restarting services...
call "%~dp0silent_start_local.bat"
exit /b 0
