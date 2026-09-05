@echo off
rem Stop Cloudflare Tunnel service (cloudflared).
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)
sc query cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    net stop cloudflared
    if %errorlevel% equ 0 (
        echo cloudflared service stopped.
        exit /b 0
    )
    echo [ERROR] Failed to stop service.
    exit /b 1
)
echo cloudflared service not found. Nothing to stop.
exit /b 0
