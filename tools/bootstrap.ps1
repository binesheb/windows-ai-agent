param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

& $Python --version
if ($LASTEXITCODE -ne 0) {
    throw "Python was not found. Install a supported Python 3 version or pass -Python with its executable."
}

if (-not (Test-Path ".venv")) {
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv" }
}

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment Python was not found at $venvPython"
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }

& $venvPython -m compileall -q agent tests
if ($LASTEXITCODE -ne 0) { throw "Python source validation failed" }

Write-Host "Bootstrap complete: dependencies installed and source compiled successfully."
