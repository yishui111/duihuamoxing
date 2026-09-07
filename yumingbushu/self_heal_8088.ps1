# Self-heal for the gateway port: if anything other than the gateway itself
# (uvicorn) is squatting 8088 - e.g. a WebUI launched with the old port - clear it.
$c = Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction SilentlyContinue
if (-not $c) { exit 0 }
$c | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$_" -ErrorAction SilentlyContinue
    if ($p -and $p.CommandLine) {
        if ($p.CommandLine -match 'uvicorn') {
            Write-Host ("Port 8088 already held by the gateway (PID " + $_ + ") - keeping it.")
        } else {
            $snippet = $p.CommandLine.Substring(0, [Math]::Min(90, $p.CommandLine.Length))
            Write-Host ("Clearing port 8088 squatter PID " + $_ + " : " + $snippet)
            $par = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ParentProcessId)" -ErrorAction SilentlyContinue
            $parTxt = if ($par) { $par.CommandLine } else { "parent exited (PID " + $p.ParentProcessId + ")" }
            "$([DateTime]::Now) squatter PID $($_) cleared; cmdline: $($p.CommandLine); parent: $parTxt" | Out-File "$PSScriptRoot\squatter_8088.log" -Append -Encoding utf8
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host ("Port 8088 held by PID " + $_ + " (cmdline unreadable) - left alone.")
    }
}
