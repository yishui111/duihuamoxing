@echo off
chcp 936 >nul
cd /d "%~dp0"
title ZhiYin - Stop All (native)

echo.
echo  ========================================
echo    ZhiYin - Stop all services (native)
echo  ========================================
echo.

echo  Stopping Open WebUI...
powershell -NoProfile -Command "Get-Process -Name 'open-webui' -ErrorAction SilentlyContinue | Stop-Process -Force"
echo  Stopping Ollama...
powershell -NoProfile -Command "Get-Process -Name 'ollama' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"
echo  Stopping built-in TTS voice service (8061)...
powershell -NoProfile -Command "$f='%~dp0data\tts.pid'; if (Test-Path $f) { $id=[int](Get-Content $f -Raw); $p = Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -eq $id -and $_.CommandLine -match 'tts_api' } | Select-Object -First 1; if ($p) { Stop-Process -Id $id -Force; Write-Host ('  Stopped TTS service (PID '+$id+')') } else { Write-Host '  [INFO] Recorded service not running (may be stopped manually)' }; Remove-Item $f -Force -ErrorAction SilentlyContinue } else { Write-Host '  [INFO] No TTS pid record (may not be started)' }"
echo  Stopping Digital Human avatar service (light-avatar)...
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 48620 -State Listen -ErrorAction SilentlyContinue; if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"
echo.
echo  All stopped. Double-click Æô¶¯.bat to start again.
echo.
pause
