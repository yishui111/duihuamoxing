@echo off
rem Backup Open WebUI database (webui.db). Keeps newest 7 backups.
rem The database lives in the parent duihuamoxing project; backups are saved
rem into backup\ under this folder (excluded from git via .gitignore).
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
set "SRC=%PROJECT%\data\open-webui\webui.db"
set "DSTDIR=%~dp0backup"
if not exist "%SRC%" (
    echo [ERROR] webui.db not found: %SRC%
    exit /b 1
)
if not exist "%DSTDIR%" mkdir "%DSTDIR%"
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set "DD=%%a%%b%%c"
for /f "tokens=1-2 delims=: " %%a in ("%time%") do set "TT=%%a%%b"
set "TT=%TT: =0%"
set "OUT=%DSTDIR%\webui_%DD%_%TT%.db"
copy /y "%SRC%" "%OUT%" >nul
echo Backup saved: %OUT%
rem Remove backups older than newest 7
powershell -NoProfile -Command "Get-ChildItem '%DSTDIR%' -Filter 'webui_*.db' | Sort-Object LastWriteTime -Descending | Select-Object -Skip 7 | Remove-Item -Force"
exit /b 0
