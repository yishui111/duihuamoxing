@echo off
rem One-click bring-up, in the recommended order:
rem   1) local duihuamoxing services -> 2) login gateway -> 3) cloudflared tunnel
rem NOTE: step 1 may take 1-3 minutes (model warm-up); step 3 may raise a UAC prompt.
setlocal
echo ============================================
echo   ZhiYin - bring server online
echo ============================================
echo.
echo [1/3] Starting local services (duihuamoxing)...
call "%~dp0start_local_services_1.bat"
echo.
echo [2/3] Starting login gateway (127.0.0.1:8291)...
call "%~dp0start_login_gateway.bat"
echo.
echo [3/3] Starting cloudflared tunnel...
call "%~dp0start_cloudflared_2.bat"
echo.
echo Done. External access: https://nas.905283.xyz
echo.
pause
exit /b 0
