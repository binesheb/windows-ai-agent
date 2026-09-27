[CmdletBinding()]
param(
    [string]$Model = "",
    [switch]$SkipModelPull,
    [switch]$SkipPython,
    [switch]$SkipOllama,
    [string]$ReportPath = ""
)
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
$started = Get-Date
$results = [ordered]@{
    schema = "binesh-agent-report/v1"
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    computer = $env:COMPUTERNAME
    user = $env:USERNAME
    status = "running"
    checks = @()
    errors = @()
}
function Add-Check([string]$Name, [bool]$Passed, [string]$Details) {
    $script:results.checks += [ordered]@{ name=$Name; passed=$Passed; details=$Details }
    if (-not $Passed) { $script:results.errors += ($Name + ": " + $Details) }
}
function Invoke-Checked([string]$File, [string[]]$Args, [string]$Name) {
    & $File @Args
    $code = $LASTEXITCODE
    Add-Check $Name ($code -eq 0) ("exit_code=" + $code)
    if ($code -ne 0) { throw ($Name + " failed with exit code " + $code) }
}
try {
    if ($PSVersionTable.PSVersion.Major -lt 5) { throw "PowerShell 5 or newer is required." }
    Add-Check "PowerShell" $true $PSVersionTable.PSVersion.ToString()
    $os = Get-CimInstance Win32_OperatingSystem
    Add-Check "Windows" $true ($os.Caption + " build " + $os.BuildNumber)
    $ramGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    $gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1 Name, AdapterRAM
    $gpuName = if ($gpu) { $gpu.Name } else { "unknown" }
    $gpuGB = if ($gpu -and $gpu.AdapterRAM) { [math]::Round($gpu.AdapterRAM / 1GB, 1) } else { 0 }
    $results.hardware = [ordered]@{ ram_gb=$ramGB; gpu=$gpuName; gpu_memory_gb=$gpuGB; cpu=(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name) }
    if (-not $SkipOllama) {
        $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        if (-not $ollama) {
            $winget = Get-Command winget -ErrorAction SilentlyContinue
            if (-not $winget) { throw "Ollama is not installed and winget is unavailable. Install Ollama manually, then rerun." }
            Invoke-Checked "winget" @("install","--id","Ollama.Ollama","--exact","--accept-package-agreements","--accept-source-agreements") "Install Ollama"
            $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        }
        if (-not $ollama) {
            $ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
            if (Test-Path $ollamaPath) { $env:Path += ";" + (Split-Path $ollamaPath) }
            $ollama = Get-Command ollama -ErrorAction SilentlyContinue
        }
        if (-not $ollama) { throw "Ollama installation completed but ollama.exe was not found on PATH." }
        Add-Check "Ollama CLI" $true ((& ollama --version 2>&1 | Out-String).Trim())
        $service = Get-Service "Ollama" -ErrorAction SilentlyContinue
        if ($service -and $service.Status -ne "Running") { try { Start-Service "Ollama" -ErrorAction Stop } catch { } }
        try { Invoke-Checked "ollama" @("list") "Ollama service" }
        catch {
            $ollamaExe = (Get-Command ollama).Source
            Start-Process $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
            Start-Sleep -Seconds 3
            Invoke-Checked "ollama" @("list") "Ollama service"
        }
        if (-not $Model) {
            if ($ramGB -ge 24) { $Model="qwen3:14b" } elseif ($ramGB -ge 12) { $Model="qwen3:8b" } else { $Model="qwen3:4b" }
        }
        $results.model = $Model
        if (-not $SkipModelPull) { Invoke-Checked "ollama" @("pull",$Model) ("Pull model " + $Model) }
        $probe = & ollama run $Model "Reply with exactly: BINESH_AI_READY" 2>&1 | Out-String
        $probeOk = $probe -match "BINESH_AI_READY"
        Add-Check "Model inference" $probeOk $probe.Trim()
        if (-not $probeOk) { throw "Local model inference test did not return the expected response." }
    }
    if (-not $SkipPython) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
        if (-not $python) { throw "Python was not found. Install Python 3.11+ and rerun." }
        Invoke-Checked $python.Source @("--version") "Python"
        if (-not (Test-Path ".venv")) { Invoke-Checked $python.Source @("-m","venv",".venv") "Create virtual environment" }
        $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
        Invoke-Checked $venvPython @("-m","pip","install","-r","requirements.txt") "Install agent dependencies"
        Invoke-Checked $venvPython @("-m","compileall","-q","agent","tests") "Compile Python sources"
    }
    $results.status="ready"
}
catch {
    $results.status="failed"
    $results.errors += $_.Exception.Message
}
finally {
    $results.duration_seconds=[math]::Round(((Get-Date)-$started).TotalSeconds,2)
    if (-not $ReportPath) { $ReportPath=Join-Path $repoRoot "agent-report.json" }
    $results | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportPath -Encoding UTF8
    Write-Host ""
    Write-Host "=== BINESH AGENT REPORT ==="
    Write-Host ("Status : " + $results.status)
    Write-Host ("Report : " + $ReportPath)
    Write-Host ("Checks : " + $results.checks.Count)
    Write-Host ("Errors : " + $results.errors.Count)
    if ($results.errors.Count -gt 0) { $results.errors | ForEach-Object { Write-Host ("ERROR: " + $_) }; exit 1 }
    Write-Host "Binesh AI local bootstrap is READY."
}