param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if ((git status --porcelain)) { throw 'Local changes detected; refusing to overwrite them.' }
git fetch origin main
$local = (git rev-parse HEAD).Trim()
$remote = (git rev-parse origin/main).Trim()
if ($local -eq $remote) { Write-Host 'Windows AI Agent is up to date.'; exit 0 }
if ($CheckOnly) { Write-Host "Update available: $($remote.Substring(0,12))"; exit 10 }
git merge --ff-only origin/main
Write-Host "Updated to $((git rev-parse HEAD).Substring(0,12))."
