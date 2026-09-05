@echo off
rem One-click shutdown, in the recommended order:
rem   1) cloudflared tunnel -> 2) login gateway -> 3) local services
rem NOTE: step 1 may raise a UAC prompt.
setlocal
echo ============================================
echo   ZhiYin - take server offline
echo ============================================
echo.
echo [1/3] Stopping cloudflared tunnel...
call "%~dp0stop_cloudflared_1.bat"
echo.
echo [2/3] Stopping login gateway...
call "%~dp0stop_login_gateway.bat"
echo.
echo [3/3] Stopping local services (duihuamoxing)...
call "%~dp0stop_local_services_2.bat"
echo.
echo Done. The server is offline now.
echo.
pause
exit /b 0
