@echo off
cd /d "%~dp0"
title ZhiYin Avatar Service - Stop

echo ========================================
echo   Digital Human Avatar Service - Stop
echo ========================================
echo.
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 48620 -State Listen -ErrorAction SilentlyContinue; if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }; Write-Host '  Avatar service stopped' } else { Write-Host '  [INFO] Avatar service not running' }"
echo.
pause
