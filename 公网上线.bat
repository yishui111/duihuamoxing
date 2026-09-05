@echo off
rem ZhiYin - go ONLINE on the public domain (https://nas.905283.xyz).
rem Order: local services (Ollama/Open WebUI/TTS/avatar) -> login gateway 8091 -> Cloudflare tunnel.
rem The tunnel step asks for administrator rights (UAC). Workbench lives in yumingbushu\.
cd /d "%~dp0"
call "%~dp0yumingbushu\start.bat"
