# Find the first existing project entry script under a project directory.
#
# The parent project (duihuamoxing) may name its entry scripts in Chinese,
# which cannot be written literally inside an ASCII-only .bat file. Candidate
# names are therefore kept in entry_names.json (UTF-8, next to this script)
# and resolved here at runtime, so this works regardless of the console code
# page (GBK 936 / UTF-8 65001 / ...).
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0find_entry.ps1" -Project "<dir>" -Mode start
#   powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0find_entry.ps1" -Project "<dir>" -Mode stop
#
# Prints the full path of the first candidate that exists, or nothing (exit 1).
param(
    [Parameter(Mandatory = $true)][string]$Project,
    [Parameter(Mandatory = $true)][ValidateSet('start', 'stop')][string]$Mode
)
$ErrorActionPreference = 'SilentlyContinue'

# 输出编码与 cmd（GBK 936）对齐，避免 for /f 捕获中文路径时乱码崩溃
try { [Console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(936) } catch {}

$namesFile = Join-Path $PSScriptRoot 'entry_names.json'
if (-not (Test-Path -LiteralPath $namesFile)) {
    Write-Error "entry_names.json not found next to find_entry.ps1"
    exit 1
}

$cfg = Get-Content -Raw -Encoding UTF8 -LiteralPath $namesFile | ConvertFrom-Json
$candidates = @($cfg.$Mode)
if ($candidates.Count -eq 0) {
    exit 1
}

foreach ($name in $candidates) {
    $candidate = Join-Path $Project $name
    if (Test-Path -LiteralPath $candidate) {
        Write-Output $candidate
        exit 0
    }
}
exit 1
