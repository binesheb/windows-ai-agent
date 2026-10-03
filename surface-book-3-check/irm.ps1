# Surface Book 3 one-command launcher
$u='https://raw.githubusercontent.com/binesheb/windows-ai-agent/surface-book-3-check/surface-book-3-check/SurfaceBook3Check.ps1'
$code=Invoke-RestMethod -Uri $u -UseBasicParsing
$p=Read-Host 'Enter seller asking price in INR (press Enter if unknown)'
if($p -match '^\s*$') { & ([scriptblock]::Create($code)) }
else {
  $n=0
  if([decimal]::TryParse(($p -replace '[₹,\s]',''),[Globalization.NumberStyles]::Number,[Globalization.CultureInfo]::InvariantCulture,[ref]$n)) {
    & ([scriptblock]::Create($code)) -AskingPrice $n
  } else {
    Write-Host 'Invalid price; running diagnostics without price analysis.' -ForegroundColor Yellow
    & ([scriptblock]::Create($code))
  }
}
