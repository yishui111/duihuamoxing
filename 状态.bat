@echo off
cd /d "%~dp0"
title ZhiYin - Status

echo.
echo  ========================================
echo    ZhiYin - Status
echo  ========================================
echo.

echo  -- Chat System (Open WebUI 8088) --
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:8088/health' -TimeoutSec 5; Write-Host ('  Open WebUI: OK (' + $r.status + ')') } catch { Write-Host '  Open WebUI: not running or still loading...' }"

echo  -- Ollama (11434) --
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5; Write-Host '  Installed models:'; $r.models | ForEach-Object { Write-Host ('    - ' + $_.name + '  ' + [math]::Round($_.size/1GB,2) + 'GB') } } catch { Write-Host '  Ollama: not running or still loading...' }"
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://localhost:11434/api/ps' -TimeoutSec 5; if ($r.models.Count -gt 0) { Write-Host ('  Loaded models (VRAM): ' + (($r.models | ForEach-Object { $_.name }) -join ', ')) } else { Write-Host '  Loaded models (VRAM): none; first chat may wait 1-3 min for cold load' } } catch { Write-Host '  (model load state unknown)' }"

echo  -- TTS voice service (18060) --
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:18060/health' -TimeoutSec 5 | Out-Null; Write-Host '  TTS: OK (18060)' } catch { Write-Host '  TTS: not running (reading falls back to system voice)' }"

echo  -- Digital Human avatar service (48620) --
powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:48620/api/libs' -TimeoutSec 5; Write-Host ('  Avatar: OK (libs: ' + (($r.libs) -join ', ') + ')') } catch { Write-Host '  Avatar: not running' }"

echo.
pause
