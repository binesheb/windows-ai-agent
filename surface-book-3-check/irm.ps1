# Surface Book 3 one-command launcher
$u='https://raw.githubusercontent.com/binesheb/windows-ai-agent/main/surface-book-3-check/SurfaceBook3Check.ps1'
$code=Invoke-RestMethod -Uri $u -UseBasicParsing
& ([scriptblock]::Create($code)) @args
