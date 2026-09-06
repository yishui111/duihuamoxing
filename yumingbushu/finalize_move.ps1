# Finalize the migration of the deployment workbench into duihuamoxing:
# re-point the cloudflared Windows service and the ZhiYin scheduled tasks
# from the old sibling folder (D:\xm\yumingbushu) to this folder, so the old
# folder can be deleted safely. Run as administrator (self-elevating wrapper:
# finalize_move.bat). Also usable after moving the whole duihuamoxing folder.
$ErrorActionPreference = 'Continue'
$Root = $PSScriptRoot
Write-Host '=== 1/3 cloudflared Windows service -> re-register from this folder ==='
$cfd = Join-Path $Root 'cloudflared\cloudflared.exe'
$tokFile = Join-Path $Root 'cloudflared\tunnel-token.txt'
if (-not (Test-Path $cfd)) { Write-Host "[ERROR] cloudflared.exe not found: $cfd"; exit 1 }
if (-not (Test-Path $tokFile)) { Write-Host "[ERROR] token file not found: $tokFile"; exit 1 }
$token = (Get-Content $tokFile -Raw).Trim()
& sc.exe stop cloudflared | Out-Null
Start-Sleep -Seconds 2
& $cfd service uninstall | Out-Null
Start-Sleep -Seconds 1
& $cfd service install $token
if ($LASTEXITCODE -ne 0) { Write-Host '[ERROR] cloudflared service install failed'; exit 1 }
& sc.exe start cloudflared | Out-Null
Start-Sleep -Seconds 3
& sc.exe qc cloudflared | Select-String 'BINARY_PATH_NAME'
& sc.exe query cloudflared | Select-String 'STATE'

Write-Host '=== 2/3 scheduled tasks -> re-point to this folder ==='
$map = @{ 'ZhiYinBackup' = 'backup_webui.bat'; 'ZhiYinHealthCheck' = 'auto_health_check.bat' }
foreach ($name in $map.Keys) {
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $task) { Write-Host "  [INFO] task $name not registered, skipped"; continue }
    $bat = Join-Path $Root $map[$name]
    $args = '-NoProfile -WindowStyle Hidden -Command Start-Process -FilePath "{0}" -WindowStyle Hidden' -f $bat
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $args
    Set-ScheduledTask -TaskName $name -Action $action | Out-Null
    $check = (Get-ScheduledTask -TaskName $name).Actions[0]
    Write-Host ("  {0}: {1} {2}" -f $name, $check.Execute, $check.Arguments)
}

Write-Host '=== 3/3 done ==='
Write-Host 'Old D:\xm\yumingbushu can now be deleted safely.'
