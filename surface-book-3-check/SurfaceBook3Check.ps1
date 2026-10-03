[CmdletBinding()]
param(
 [decimal]$AskingPrice=0,
 [switch]$Quick,
 [switch]$NoStress,
 [string]$OutputDirectory="$env:USERPROFILE\Desktop\SurfaceBook3-Diagnostic"
)
$ErrorActionPreference='SilentlyContinue'
New-Item -ItemType Directory -Force $OutputDirectory | Out-Null
$R=[System.Collections.Generic.List[object]]::new();$F=@();$W=@()
function Add($c,$t,$s,$v,$d=''){
 $R.Add([pscustomobject]@{Category=$c;Test=$t;Status=$s;Value=$v;Details=$d})
 if($s -eq 'FAIL'){$script:F+="$c / $t : $d"}elseif($s -eq 'WARN'){$script:W+="$c / $t : $d"}
}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$cs=Get-CimInstance Win32_ComputerSystem;$bios=Get-CimInstance Win32_BIOS;$cpu=Get-CimInstance Win32_Processor|select -First 1;$os=Get-CimInstance Win32_OperatingSystem
$model="$($cs.Manufacturer) $($cs.Model)";$serial=if($bios.SerialNumber){$bios.SerialNumber.Trim()}else{'N/A'};$ram=[math]::Round($cs.TotalPhysicalMemory/1GB,1)
Add Identity Manufacturer $(if($cs.Manufacturer -match 'Microsoft'){'PASS'}else{'WARN'}) $cs.Manufacturer 'Expected Microsoft'
Add Identity Model $(if($cs.Model -match 'Surface Book 3'){'PASS'}else{'FAIL'}) $cs.Model 'Expected Surface Book 3'
Add Identity Serial INFO $serial
Add Identity BIOS INFO "$($bios.SMBIOSBIOSVersion) / $($bios.ReleaseDate)"
Add Identity Windows INFO "$($os.Caption) build $($os.BuildNumber)"
Add Identity RAM $(if($ram -ge 31){'PASS'}elseif($ram -ge 15){'WARN'}else{'FAIL'}) "$ram GB" 'Target: 32 GB'
$cpuName=$cpu.Name.Trim()
Add CPU Processor $(if($cpuName -match 'i7-1065G7'){'PASS'}else{'WARN'}) $cpuName 'Target: i7-1065G7'
Add CPU CoresThreads INFO "$($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) threads"
$g=Get-CimInstance Win32_VideoController;$gt=($g|%{"$($_.Name) [$([math]::Round($_.AdapterRAM/1GB,1)) GB]"}) -join '; '
$g1660=($g.Name -match 'GTX 1660 Ti');$gnv=($g.Name -match 'NVIDIA')
Add GPU Adapters $(if($g1660){'PASS'}elseif($gnv){'WARN'}else{'FAIL'}) $gt 'Target: GTX 1660 Ti 6 GB'
$d=Get-CimInstance Win32_VideoController|sort CurrentHorizontalResolution -Descending|select -First 1
$res="$($d.CurrentHorizontalResolution)x$($d.CurrentVerticalResolution) @ $($d.CurrentRefreshRate)Hz";$native=($d.CurrentHorizontalResolution -eq 3240 -and $d.CurrentVerticalResolution -eq 2160)
Add Display Resolution $(if($native){'PASS'}else{'WARN'}) $res '15-inch reference: 3240x2160'
Add Display Touch INFO 'MANUAL' 'Use MANUAL-CHECKLIST.md'
$pd=Get-PhysicalDisk
foreach($x in $pd){$s=if($x.HealthStatus -eq 'Healthy'){'PASS'}elseif($x.HealthStatus -eq 'Warning'){'WARN'}else{'FAIL'};Add Storage $x.FriendlyName $s "$($x.MediaType) / $([math]::Round($x.Size/1GB)) GB / $($x.HealthStatus)" "$($x.OperationalStatus -join ',')"}
$c=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'";$free=if($c.Size){[math]::Round(100*$c.FreeSpace/$c.Size,1)}else{0}
Add Storage CFree $(if($free -ge 20){'PASS'}elseif($free -ge 10){'WARN'}else{'FAIL'}) "$free% free"
if(!$Quick -and $admin){
 $scan=chkdsk C: /scan 2>&1|Out-String;$scan|Set-Content "$OutputDirectory\chkdsk-scan.txt";Add Storage NTFSScan $(if($scan -match 'found problems|corrupt|cannot continue'){'FAIL'}else{'PASS'}) Completed 'See chkdsk-scan.txt'
}else{Add Storage NTFSScan WARN 'Skipped' 'Run elevated without -Quick'}
$bat=@();$st=Get-CimInstance -Namespace root\wmi -Class BatteryStaticData;$fc=Get-CimInstance -Namespace root\wmi -Class BatteryFullChargedCapacity;$cc=Get-CimInstance -Namespace root\wmi -Class BatteryCycleCount
if($st){foreach($b in $st){$f=$fc|? Tag -eq $b.Tag|select -First 1;$q=$cc|? Tag -eq $b.Tag|select -First 1;$h=if($b.DesignedCapacity -and $f.FullChargedCapacity){[math]::Round(100*$f.FullChargedCapacity/$b.DesignedCapacity,1)}else{$null};$bat+=[pscustomobject]@{Tag=$b.Tag;Health=$h;Cycles=$q.CycleCount;Design=$b.DesignedCapacity;Full=$f.FullChargedCapacity}}}
else{foreach($b in Get-CimInstance Win32_Battery){$h=if($b.DesignCapacity){[math]::Round(100*$b.FullChargeCapacity/$b.DesignCapacity,1)}else{$null};$bat+=[pscustomobject]@{Tag=$b.DeviceID;Health=$h;Cycles=$null;Design=$b.DesignCapacity;Full=$b.FullChargeCapacity}}}
$hs=@()
foreach($b in $bat){$hs+=$b.Health;$s=if($null -eq $b.Health){'WARN'}elseif($b.Health -ge 80){'PASS'}elseif($b.Health -ge 60){'WARN'}else{'FAIL'};Add Battery $b.Tag $s "$($b.Health)% / $($b.Cycles) cycles" "Design $([math]::Round($b.Design/1000)) Wh; full $([math]::Round($b.Full/1000)) Wh"}
$min=if($hs.Count){($hs|measure -Minimum).Minimum}else{0};Add Battery MinimumHealth $(if($min -ge 80){'PASS'}elseif($min -ge 60){'WARN'}else{'FAIL'}) "$min%"
$batt="$OutputDirectory\battery-report.html";powercfg /batteryreport /output $batt|Out-Null;Add Battery Report $(if(Test-Path $batt){'PASS'}else{'WARN'}) $batt
$pnp=@(Get-PnpDevice|? Status -ne OK);Add Devices PnPErrors $(if(!$pnp.Count){'PASS'}else{'FAIL'}) "$($pnp.Count) non-OK devices"
if($pnp.Count){$pnp|select Status,Class,FriendlyName,InstanceId|Export-Csv "$OutputDirectory\device-errors.csv" -NoTypeInformation}
if($admin -and !$Quick){
 $di=dism /online /cleanup-image /checkhealth 2>&1|Out-String;$di|Set-Content "$OutputDirectory\dism.txt";Add Windows DISM $(if($di -match 'No component store corruption detected'){'PASS'}else{'WARN'}) Completed
 $sf=sfc /verifyonly 2>&1|Out-String;$sf|Set-Content "$OutputDirectory\sfc.txt";Add Windows SFC $(if($sf -match 'did not find any integrity violations'){'PASS'}elseif($sf -match 'found integrity violations'){'FAIL'}else{'WARN'}) Completed
}else{Add Windows Integrity WARN Skipped 'Run elevated without -Quick'}
$ev=@();$since=(Get-Date).AddDays(-14);foreach($l in 'System','Application'){$ev+=@(Get-WinEvent -FilterHashtable @{LogName=$l;StartTime=$since;Level=1,2} -MaxEvents 100)}
$ec=$ev.Count;Add Stability ErrorEvents $(if($ec -lt 10){'PASS'}elseif($ec -lt 30){'WARN'}else{'FAIL'}) "$ec events in 14 days";if($ec){$ev|select TimeCreated,LogName,ProviderName,Id,LevelDisplayName,Message|Export-Csv "$OutputDirectory\critical-events.csv" -NoTypeInformation}
$score=0
if($cs.Model -match 'Surface Book 3'){$score+=10};if($cpuName -match 'i7-1065G7'){$score+=8};if($ram -ge 31){$score+=7};if($g1660){$score+=15}elseif($gnv){$score+=8}
if($min -ge 90){$score+=20}elseif($min -ge 80){$score+=17}elseif($min -ge 70){$score+=13}elseif($min -ge 60){$score+=7}else{$score+=2}
if($pd.Count -and @($pd|? HealthStatus -eq Healthy).Count -eq $pd.Count){$score+=12}else{$score+=4};if($free -ge 20){$score+=5}elseif($free -ge 10){$score+=3};if(!$pnp.Count){$score+=8}elseif($pnp.Count -lt 3){$score+=4};if($ec -lt 10){$score+=7}elseif($ec -lt 30){$score+=3};if($native){$score+=8}else{$score+=4};$score=[math]::Min(100,$score)
$cap=if($score -ge 90){54000}elseif($score -ge 80){50000}elseif($score -ge 70){44000}elseif($score -ge 60){37000}else{30000};if($min -lt 60){$cap-=8000}elseif($min -lt 70){$cap-=5000}elseif($min -lt 80){$cap-=2500};$cap=[math]::Max(20000,[math]::Round($cap,-3))
$verdict=if($F.Count){'WALK AWAY / FIX ISSUES'}elseif($AskingPrice -and $score -ge 85 -and $AskingPrice -le $cap){'BUY'}elseif($score -lt 60 -or ($AskingPrice -and $AskingPrice -gt $cap+8000)){'WALK AWAY'}else{'NEGOTIATE'}
$sum=[pscustomobject]@{Timestamp=(Get-Date).ToString('s');Model=$model;Serial=$serial;CPU=$cpuName;RAMGB=$ram;GPU=$gt;Resolution=$res;MinBatteryHealth=$min;FreeSpace=$free;PnPErrors=$pnp.Count;Errors14d=$ec;Score=$score;AskingPrice=$AskingPrice;PriceCeiling=$cap;Verdict=$verdict}
$sum|ConvertTo-Json|Set-Content "$OutputDirectory\summary.json";$R|Export-Csv "$OutputDirectory\results.csv" -NoTypeInformation
@"
# Surface Book 3 Manual Checklist
- [ ] No swelling or display lifting
- [ ] No cracked display
- [ ] Dead/stuck pixel test: black/white/red/green/blue
- [ ] Touch works across entire screen, no ghost touch
- [ ] Keyboard every key
- [ ] Trackpad click/gestures
- [ ] Front/rear cameras
- [ ] Windows Hello
- [ ] Speakers/mics
- [ ] Wi-Fi/Bluetooth
- [ ] USB-A x2 / USB-C / SD / 3.5mm
- [ ] Surface Connect base and tablet
- [ ] Detach and reattach twice
- [ ] GPU returns after reattachment
- [ ] Charger stable while hinge moves
- [ ] Serial matches paperwork
- [ ] No BIOS password / organization lock
- [ ] Seller permits full test/return
## Walk-away
Battery swelling, display lifting, missing GPU, detach failure, intermittent charging, SSD failure, repeated WHEA/storage/display errors or unexplained shutdowns.
"@|Set-Content "$OutputDirectory\MANUAL-CHECKLIST.md"
Write-Host "SURFACE BOOK 3 RESULT" -ForegroundColor Cyan;Write-Host "Model: $model";Write-Host "CPU: $cpuName";Write-Host "RAM: $ram GB";Write-Host "GPU: $gt";Write-Host "Display: $res";Write-Host "Min battery: $min%";Write-Host "Score: $score/100";if($AskingPrice){Write-Host "Asking: ₹$AskingPrice"};Write-Host "Private-sale ceiling: ₹$cap";Write-Host "VERDICT: $verdict" -ForegroundColor $(if($verdict -eq 'BUY'){'Green'}elseif($verdict -like 'NEGOTIATE*'){'Yellow'}else{'Red'});if($F.Count){Write-Host "CRITICAL:" -ForegroundColor Red;$F|%{Write-Host " - $_" -ForegroundColor Red}};if($W.Count){Write-Host "WARNINGS:" -ForegroundColor Yellow;$W|select -Unique|%{Write-Host " - $_" -ForegroundColor Yellow}};Write-Host "Reports: $OutputDirectory" -ForegroundColor Green
