@echo off
rem Start ZhiYin Ops Dashboard (local web console, http://127.0.0.1:8290).
rem Uses the venv python of the parent duihuamoxing project (this folder is its sub-directory).
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
set "PYEXE=%PROJECT%\venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [ERROR] Python not found: %PYEXE%
    echo Install the duihuamoxing venv first - see ..\DEPLOY.md.
    exit /b 1
)
echo Starting ZhiYin Ops Dashboard...
start "ZhiYin-OpsDashboard" "%PYEXE%" -m uvicorn main:app --host 127.0.0.1 --port 8290 --app-dir "%~dp0ops_dashboard"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8290"
exit /b 0
