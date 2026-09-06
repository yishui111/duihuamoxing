@echo off
chcp 936>nul
rem ==================================================
rem  DUIHUAMOXING - one-key preflight for big assets
rem  Guarantee flow: (A) copy original project folder
rem  with big assets (fastest), or (B) clone this repo
rem  then run this script; details: see DEPLOY.md top.
rem ==================================================
setlocal
cd /d "%~dp0"
set "MISSING=0"
echo Checking required big assets...
if exist "data\ollama\models" (echo   OK   data\ollama\models) else (echo   MISS data\ollama\models ^& set MISSING=1)
if exist "文字驱动语音\gptsovits\GPT-SoVITS" (echo   OK   文字驱动语音\gptsovits\GPT-SoVITS) else (echo   MISS 文字驱动语音\gptsovits\GPT-SoVITS ^& set MISSING=1)
if exist "runtime\ffmpeg\bin" (echo   OK   runtime\ffmpeg\bin) else (echo   MISS runtime\ffmpeg\bin ^& set MISSING=1)
echo.
if %MISSING%==0 (
  echo ALL big assets present. Run start.bat now.
) else (
  echo Some big assets missing. See DEPLOY.md top section
  "Deployment guarantee" for download instructions.
)
pause
