# ZhiYin diagnostics collector
# Gathers service logs + system info into a timestamped zip.
# All paths are derived relative to this script, so the repo can live anywhere
# the duihuamoxing project root is the parent folder of this one.
$ErrorActionPreference = 'SilentlyContinue'
$REPO = $PSScriptRoot
$ROOT = Split-Path $PSScriptRoot -Parent   # duihuamoxing project root (this folder is its sub-directory)
$CFD = Join-Path $PSScriptRoot 'cloudflared\cloudflared.exe'
$OUTDIR = $PSScriptRoot
$STAMP = Get-Date -Format 'yyyyMMdd_HHmmss'
$WORK = Join-Path $OUTDIR "diag_tmp"
$ZIP = Join-Path $OUTDIR "diag_$STAMP.zip"

if (Test-Path $WORK) { Remove-Item $WORK -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $WORK 'logs') -Force | Out-Null

Write-Host 'Collecting logs...'
$logs = @('webui.log','webui.err.log','ollama.log','ollama.err.log','tts.log','tts.err.log','avatar.log','avatar.err.log')
foreach ($name in $logs) {
    $src = Join-Path (Join-Path $ROOT 'log') $name
    if (Test-Path $src) {
        Get-Content $src -Tail 500 | Out-File (Join-Path $WORK "logs\$name") -Encoding utf8
    }
}

Write-Host 'Collecting system info...'
$info = Join-Path $WORK 'system_info.txt'
function W($line) { $line | Out-File $info -Append -Encoding utf8 }

W "==== ZhiYin Diagnostics $STAMP ===="
W "Host: $env:COMPUTERNAME | User: $env:USERNAME"
W "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
W ''
W '--- Versions ---'
W "cloudflared: $(& $CFD --version 2>&1)"
W "python(venv): $(& "$ROOT\venv\Scripts\python.exe" --version 2>&1)"
$di = Get-ChildItem "$ROOT\venv\Lib\site-packages" -Directory -Filter 'open_webui-*.dist-info' | Select-Object -First 1
W "open-webui: $(if ($di) { $di.Name } else { 'unknown' })"
W ''
W '--- Service ---'
$svc = Get-Service cloudflared -ErrorAction SilentlyContinue
W "cloudflared service: $(if ($svc) { "$($svc.Status) / $($svc.StartType)" } else { 'NOT INSTALLED' })"
W ''
W '--- Ports ---'
foreach ($p in 8088,8089,11434,48620,8061) {
    $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue
    W "port $p : $(if ($c) { "LISTEN (pid $($c[0].OwningProcess))" } else { 'DOWN' })"
}
W ''
W '--- Processes ---'
Get-Process | Where-Object { $_.ProcessName -match 'ollama|open-webui|python|cloudflared' } |
    ForEach-Object { W ('{0} pid={1} mem={2:N0}MB' -f $_.ProcessName, $_.Id, ($_.WorkingSet64/1MB)) }
W ''
W '--- GPU ---'
$gpu = & nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader 2>&1
W ($gpu -join '; ')
W ''
W '--- Disk ---'
Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -ne $null } |
    ForEach-Object { W ('{0}: free={1:N1}GB used={2:N1}GB' -f $_.Name, ($_.Free/1GB), ($_.Used/1GB)) }
W ''
W '--- Database ---'
$db = Get-Item "$ROOT\data\open-webui\webui.db"
W "webui.db: $(if ($db) { "size={0:N1}MB modified={1}" -f ($db.Length/1MB), $db.LastWriteTime } else { 'NOT FOUND' })"
W ''
W '--- Recent cloudflared events (last 8) ---'
$ev = Get-WinEvent -LogName Application -MaxEvents 5000 -ErrorAction SilentlyContinue |
    Where-Object { $_.ProviderName -match 'cloudflared' -or $_.Message -match 'cloudflared' } |
    Select-Object -First 8
if ($ev) { $ev | ForEach-Object { W ("[{0}] {1}: {2}" -f $_.TimeCreated, $_.LevelDisplayName, $_.Message) } } else { W 'no cloudflared events' }
W ''

Write-Host 'Packing...'
Compress-Archive -Path "$WORK\*" -DestinationPath $ZIP -Force
Remove-Item $WORK -Recurse -Force

if (Test-Path $ZIP) {
    Write-Host ''
    Write-Host '============================================'
    Write-Host "  Diagnostics saved: $ZIP"
    Write-Host '  Send this file to the developer.'
    Write-Host '============================================'
} else {
    Write-Host '[ERROR] zip creation failed'
}
