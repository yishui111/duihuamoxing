@echo off
rem One-click diagnostics: collect logs + system info into a zip.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0collect_diag.ps1"
pause
