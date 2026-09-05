@echo off
rem Stop ZhiYin Login Gateway (port 8291).
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8291 -State Listen -ErrorAction SilentlyContinue; if ($c) { Stop-Process -Id $c[0].OwningProcess -Force; Write-Host 'Login gateway stopped.' } else { Write-Host 'Login gateway not running.' }"
exit /b 0
