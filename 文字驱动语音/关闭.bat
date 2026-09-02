@echo off
cd /d "%~dp0"
title ZhiYin Text-to-Speech Service - Stop

echo ========================================
echo   Text-to-Speech Service - Stop
echo ========================================
echo.
set "ROOT=%~dp0.."
powershell -NoProfile -Command "$f='%ROOT%\data\tts.pid'; if (Test-Path $f) { $id=[int](Get-Content $f -Raw); $p = Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -eq $id -and $_.CommandLine -match 'tts_api' } | Select-Object -First 1; if ($p) { Stop-Process -Id $id -Force; Write-Host ('  Stopped TTS service (PID '+$id+')') } else { Write-Host '  [INFO] Recorded service not running' }; Remove-Item $f -Force -ErrorAction SilentlyContinue } else { Write-Host '  [INFO] No TTS pid record (may not be started)' }"
echo.
pause
