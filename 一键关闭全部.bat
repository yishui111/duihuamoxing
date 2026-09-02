@echo off
chcp 936 >nul
cd /d "%~dp0"
title ZhiYin - Stop All

echo ========================================
echo   ZhiYin - Stop all 3 sub-projects
echo ========================================
echo.
echo Stopping Digital Human avatar service...
call "%~dp0数字人\关闭.bat" < nul
echo Stopping Text-to-Speech service...
call "%~dp0文字驱动语音\关闭.bat" < nul
echo Stopping Chat System...
call "%~dp0对话系统\关闭.bat" < nul
echo.
echo All services stopped.
pause
