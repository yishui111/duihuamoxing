@echo off
rem Stop ZhiYin Login Gateway (port 8088).
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue; if ($c) { Stop-Process -Id $c[0].OwningProcess -Force; Write-Host 'Login gateway stopped.' } else { Write-Host 'Login gateway not running.' }"
exit /b 0
