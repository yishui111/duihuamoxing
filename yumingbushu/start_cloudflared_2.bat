@echo off
rem Start Cloudflare Tunnel service (tunnel -> https://nas.905283.xyz).
rem cloudflared.exe and tunnel-token.txt must be prepared under cloudflared\
rem (see README.md / DEPLOY.md - they are NOT part of this repository).
setlocal
net session >nul 2>&1
if %errorlevel% neq 0 goto notadmin

set "CFD=%~dp0cloudflared\cloudflared.exe"
set "TOKEN_FILE=%~dp0cloudflared\tunnel-token.txt"

if not exist "%CFD%" (
    echo [ERROR] cloudflared.exe not found: %CFD%
    echo Download it from https://github.com/cloudflare/cloudflared/releases and put it here.
    pause
    exit /b 1
)
if not exist "%TOKEN_FILE%" (
    echo [ERROR] tunnel token file not found: %TOKEN_FILE%
    echo Create it from your Cloudflare dashboard tunnel: Zero Trust - Networks - Tunnels.
    pause
    exit /b 1
)

sc query cloudflared >nul 2>&1
if %errorlevel% neq 0 goto foreground

rem Service registered: skip if already running, then try to start it.
sc query cloudflared | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo cloudflared service already running.
    start "" "https://nas.905283.xyz"
    exit /b 0
)
echo Starting cloudflared Windows service...
net start cloudflared
if %errorlevel% equ 0 (
    echo cloudflared service started.
    start "" "https://nas.905283.xyz"
    exit /b 0
)
echo [WARN] Service failed to start. Its binary path may still point to the old
echo        workbench location. Falling back to a foreground tunnel from THIS folder.
echo        Permanent fix: run finalize_move.bat as administrator.

:foreground
echo Starting cloudflared as a foreground process...
set "TOKEN="
set /p TOKEN=<"%TOKEN_FILE%"
start "cloudflared-tunnel" "%CFD%" tunnel --no-autoupdate run --token %TOKEN%
echo cloudflared started in a new window. Check https://nas.905283.xyz
exit /b 0

:notadmin
echo Requesting administrator privileges - PLEASE CLICK YES ON THE UAC PROMPT...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
rem The elevated copy does the work in its own window. Wait up to ~36s for the
rem user to click UAC, then report the truth: cancelled UAC = tunnel stays offline.
set /a tries=0
:uacwait
ping -n 13 127.0.0.1 >nul
sc query cloudflared | findstr /i "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo Tunnel is RUNNING. Public access: https://nas.905283.xyz
    exit /b 0
)
set /a tries+=1
if %tries% lss 3 goto uacwait
echo [WARN] Tunnel is NOT running - public access stays OFFLINE.
echo        Likely cause: the UAC prompt was cancelled, or the service failed.
echo        Run this script again and click YES on the UAC prompt.
exit /b 0
