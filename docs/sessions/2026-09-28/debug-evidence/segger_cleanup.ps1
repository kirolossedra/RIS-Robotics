$ErrorActionPreference = 'Stop'
$log = 'P:\Github\RIS-Robotics\segger_cleanup_log.txt'
"SEGGER cleanup started: $(Get-Date -Format o)" | Set-Content -LiteralPath $log -Encoding UTF8

$uninstaller = 'C:\Program Files\SEGGER\JLink_V922\Uninstall.exe'
if (Test-Path -LiteralPath $uninstaller) {
  "Running registered J-Link V9.22 uninstaller: $uninstaller /S" | Add-Content -LiteralPath $log
  $p = Start-Process -FilePath $uninstaller -ArgumentList '/S' -Wait -PassThru
  "Uninstaller exit code: $($p.ExitCode)" | Add-Content -LiteralPath $log
} else {
  "Registered J-Link V9.22 uninstaller was not found." | Add-Content -LiteralPath $log
}

$remainingProduct = Get-ItemProperty @(
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
) -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq 'J-Link V922 (64bit Windows)' }

$oldDir = 'C:\Program Files\SEGGER\JLink_V922'
if (-not $remainingProduct -and (Test-Path -LiteralPath $oldDir)) {
  "Removing residual directory positively identified as uninstalled J-Link V9.22: $oldDir" | Add-Content -LiteralPath $log
  Remove-Item -LiteralPath $oldDir -Recurse -Force
}

foreach ($inf in @('oem17.inf','oem26.inf','oem44.inf')) {
  "Deleting confirmed SEGGER/J-Link driver package: $inf" | Add-Content -LiteralPath $log
  (& pnputil.exe /delete-driver $inf /uninstall /force 2>&1 | Out-String) | Add-Content -LiteralPath $log
  "pnputil exit code for ${inf}: $LASTEXITCODE" | Add-Content -LiteralPath $log
}

$machinePath = [Environment]::GetEnvironmentVariable('Path','Machine')
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
foreach ($scope in @('Machine','User')) {
  $value = [Environment]::GetEnvironmentVariable('Path',$scope)
  $entries = @($value -split ';' | Where-Object { $_ })
  $kept = @($entries | Where-Object { $_ -notmatch '(?i)\\SEGGER\\JLink(?:_V922)?(?:\\|$)' })
  if ($kept.Count -ne $entries.Count) {
    [Environment]::SetEnvironmentVariable('Path',($kept -join ';'),$scope)
    "Removed stale J-Link V9.22 PATH entry from $scope scope." | Add-Content -LiteralPath $log
  }
}

"SEGGER cleanup completed: $(Get-Date -Format o)" | Add-Content -LiteralPath $log
Get-Content -LiteralPath $log
