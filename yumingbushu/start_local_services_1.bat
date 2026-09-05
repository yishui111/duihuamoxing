@echo off
rem Start local ZhiYin services (Open WebUI 8088, Ollama 11434, TTS 8061, Avatar 48620).
rem This folder lives inside the duihuamoxing project; the project root is the parent folder.
rem Entry probing runs inside PowerShell because cmd cannot safely parse the
rem non-ASCII path (Chinese entry name) captured via for /f.
setlocal
for %%I in ("%~dp0..") do set "PROJECT=%%~fI"
if not exist "%PROJECT%\" (
    echo [ERROR] project root not found: %PROJECT%
    echo This folder must stay inside the duihuamoxing project (duihuamoxing\yumingbushu).
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$e = & '%~dp0find_entry.ps1' -Project '%PROJECT%' -Mode start; if ($e) { Write-Host ('Found entry: ' + $e); Start-Process -FilePath $e -NoNewWindow -Wait } else { Write-Host '[WARN] no entry script found - starting base services only (Open WebUI + Ollama)...'; cmd /c call '%~dp0silent_start_local.bat' }"

echo.
echo Local services started. Open WebUI: http://localhost:8088
start "" "http://localhost:8088"
exit /b 0
