param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = $Python
}

& $pythonExe -m pytest -q
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed"
}

Write-Host "Tests completed successfully."
