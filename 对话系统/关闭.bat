@echo off
cd /d "%~dp0"
title ZhiYin Chat System - Stop

echo ========================================
echo   ZhiYin Chat System - Stop
echo ========================================
echo.
echo  Stopping Open WebUI...
powershell -NoProfile -Command "Get-Process -Name 'open-webui' -ErrorAction SilentlyContinue | Stop-Process -Force"
echo  Stopping Ollama...
powershell -NoProfile -Command "Get-Process -Name 'ollama' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
echo.
echo  All stopped.
pause
