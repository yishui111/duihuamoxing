@echo off
rem Start ZhiYin Login Gateway (http://127.0.0.1:8291) in front of Open WebUI.
rem Uses the venv python of the parent duihuamoxing project (this folder is its sub-directory).
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
set "PYEXE=%PROJECT%\venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [ERROR] Python not found: %PYEXE%
    echo Install the duihuamoxing venv first (see ..\DEPLOY.md).
    exit /b 1
)
if not exist "%~dp0login_gateway\config.json" (
    echo [ERROR] login_gateway\config.json not found.
    echo Copy login_gateway\config.json.example to login_gateway\config.json and set a strong password.
    exit /b 1
)
echo Starting ZhiYin Login Gateway...
start "ZhiYin-LoginGateway" "%PYEXE%" -m uvicorn main:app --host 127.0.0.1 --port 8291 --app-dir "%~dp0login_gateway"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8291"
exit /b 0
