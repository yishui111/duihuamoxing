@echo off
rem Re-register the cloudflared Windows service so it runs cloudflared.exe from THIS folder.
rem Needed ONCE after merging the workbench into duihuamoxing\yumingbushu, because the old
rem service entry still points to the previous location. Run as administrator (UAC prompt).
setlocal
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)
set "CFD=%~dp0cloudflared\cloudflared.exe"
set "TOKEN_FILE=%~dp0cloudflared\tunnel-token.txt"
if not exist "%CFD%" (
    echo [ERROR] cloudflared.exe not found: %CFD%
    pause
    exit /b 1
)
if not exist "%TOKEN_FILE%" (
    echo [ERROR] tunnel token file not found: %TOKEN_FILE%
    pause
    exit /b 1
)
sc query cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping and removing the existing cloudflared service...
    net stop cloudflared >nul 2>&1
    "%CFD%" service uninstall
)
set "TOKEN="
set /p TOKEN=<"%TOKEN_FILE%"
echo Installing cloudflared service from: %CFD%
"%CFD%" service install %TOKEN%
if %errorlevel% neq 0 (
    echo [ERROR] service install failed. See output above.
    pause
    exit /b 1
)
net start cloudflared
echo.
echo Done. Service now runs from this folder and auto-starts at boot:
sc qc cloudflared | findstr /i "BINARY_PATH_NAME"
pause
exit /b 0
