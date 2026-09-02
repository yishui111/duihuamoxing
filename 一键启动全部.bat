@echo off
chcp 936 >nul
cd /d "%~dp0"
title ZhiYin - Start All

echo ========================================
echo   ZhiYin - Start all 3 sub-projects
echo ========================================
echo.
echo [1/3] Starting Chat System (Open WebUI 8088 + Ollama 11434)...
start "" /min "%~dp0对话系统\启动.bat"
echo [2/3] Starting Text-to-Speech (GPT-SoVITS voice 8061)...
start "" /min "%~dp0文字驱动语音\启动.bat"
echo [3/3] Starting Digital Human avatar service (48620)...
start "" /min "%~dp0数字人\启动.bat"
echo.
echo All 3 sub-projects started in minimized windows.
echo   Chat:      http://localhost:8088
echo   Avatar:    http://127.0.0.1:48620/web/index.html
echo   TTS:       http://127.0.0.1:8061/health
echo.
echo Wait 1-3 minutes for models to load, then open the browser.
echo Each window shows its own progress; see the sub-project README on errors.
echo.
pause
