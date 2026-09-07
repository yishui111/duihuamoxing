@echo off
rem Start ZhiYin Login Gateway on 8088 - the port the Cloudflare tunnel maps to.
rem It fronts Open WebUI (now on local port 8089).
rem Uses the venv python of the parent duihuamoxing project (this folder is its sub-directory).
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
set "PYEXE=%PROJECT%\venv\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo [ERROR] Python not found: %PYEXE%
    echo Install the duihuamoxing venv first - see ..\DEPLOY.md.
    exit /b 1
)
if not exist "%~dp0login_gateway\config.json" (
    echo [ERROR] login_gateway\config.json not found.
    echo Copy login_gateway\config.json.example to login_gateway\config.json and set a strong password.
    exit /b 1
)
rem Self-heal: if something squats 8088 (e.g. a WebUI launched with the old port),
rem clear it first so the gateway always gets its port.
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue; if ($c) { $c | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { $p = Get-CimInstance Win32_Process -Filter \"ProcessId=$_\" -ErrorAction SilentlyContinue; if ($p -and $p.CommandLine -notmatch 'uvicorn') { Write-Host ('Clearing port 8088 squatter PID ' + $_); Stop-Process -Id $_ -Force } } }"
timeout /t 2 /nobreak >nul
echo Starting ZhiYin Login Gateway...
start "ZhiYin-LoginGateway" "%PYEXE%" -m uvicorn main:app --host 127.0.0.1 --port 8088 --app-dir "%~dp0login_gateway"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8088"
exit /b 0
