@echo off
rem ==================================================
rem  YUMINGBUSHU - one-key preflight for big assets
rem  Guarantee flow: (A) copy original project folder
rem  with big assets (fastest), or (B) clone this repo
rem  then run this script; details: see DEPLOY.md top.
rem ==================================================
setlocal
cd /d "%~dp0"
set "MISSING=0"
echo Checking required big assets...
if exist "cloudflared\cloudflared.exe" (echo   OK   cloudflared\cloudflared.exe) else (echo   MISS cloudflared\cloudflared.exe ^& set MISSING=1)
if exist "cloudflared\tunnel-token.txt" (echo   OK   cloudflared\tunnel-token.txt) else (echo   MISS cloudflared\tunnel-token.txt ^& set MISSING=1)
if exist "..\venv\Scripts\python.exe" (echo   OK   ..\venv ^(parent duihuamoxing python^)) else (echo   MISS ..\venv - install duihuamoxing first, see ..\DEPLOY.md ^& set MISSING=1)
echo.
if %MISSING%==0 (
  echo ALL big assets present. Run start.bat now.
) else (
  echo Some big assets missing. See DEPLOY.md (top section
  "Deployment guarantee") for download instructions.
)
pause
