@echo off
rem Finalize the workbench migration: re-point the cloudflared Windows service
rem and the ZhiYin scheduled tasks to THIS folder (duihuamoxing\yumingbushu),
rem so the old sibling folder can be deleted. Self-elevating (one UAC prompt).
setlocal
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges - please click Yes on the UAC prompt...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0finalize_move.ps1"
echo.
pause
exit /b 0
