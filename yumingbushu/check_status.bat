@echo off
rem Status check: local services, tunnel, external access.
setlocal
echo ============================================
echo   ZhiYin Status Check
echo ============================================
echo.
echo [1/4] Local services (ports):
powershell -NoProfile -Command "$p=@(8088,8089,11434,48620,18060); foreach($x in $p){ $c=Get-NetTCPConnection -State Listen -LocalPort $x -ErrorAction SilentlyContinue; if($c){ Write-Host ('  port {0} : OK' -f $x) } else { Write-Host ('  port {0} : DOWN' -f $x) } }"
echo.
echo [2/4] Open WebUI health:
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://localhost:8089/health' -TimeoutSec 5; Write-Host ('  status: ' + $r.status) } catch { Write-Host '  FAIL' }"
echo.
echo [3/4] Tunnel service:
sc query cloudflared | findstr /i "STATE" 
echo.
echo [4/4] External access:
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'https://nas.905283.xyz' -TimeoutSec 15 -UseBasicParsing; Write-Host ('  HTTP ' + $r.StatusCode + ' (reachable, login gate)') } catch { Write-Host '  FAIL (offline?)' }"
echo.
echo ============================================
pause
