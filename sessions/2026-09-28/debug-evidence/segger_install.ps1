$ErrorActionPreference = 'Stop'
$log = 'P:\Github\RIS-Robotics\segger_install_log.txt'
"SEGGER install started: $(Get-Date -Format o)" | Set-Content -LiteralPath $log -Encoding UTF8

$staleKeys = @(
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\132A9445F9095BD5CEE4933C0C25054C253BD8A3',
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\67EA26CAD232922E8506AD97DBD93123C434F28F',
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\BCE8431F6070A538518E2C2403B8E063956798AA'
)
foreach ($key in $staleKeys) {
  if (Test-Path -LiteralPath $key) {
    $item = Get-ItemProperty -LiteralPath $key
    if ($item.DisplayName -match '^Windows Driver Package - .*?(SEGGER|Segger)' -and $item.UninstallString -match '(?i)jlink(?:cdc|winusb)?\.inf') {
      "Removing orphaned J-Link driver uninstall record: $($item.DisplayName)" | Add-Content -LiteralPath $log
      Remove-Item -LiteralPath $key -Recurse -Force
    } else {
      throw "Safety check failed for registry key: $key"
    }
  }
}

$installer = 'P:\Github\RIS-Robotics\JLink_Windows_x86_64.exe'
$signature = Get-AuthenticodeSignature -FilePath $installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'SEGGER Microcontroller GmbH') {
  throw 'Installer signature is not a valid SEGGER Microcontroller GmbH signature.'
}
"Launching signed SEGGER installer silently: $installer /S" | Add-Content -LiteralPath $log
$p = Start-Process -FilePath $installer -ArgumentList '/S' -Wait -PassThru
"Installer exit code: $($p.ExitCode)" | Add-Content -LiteralPath $log
if ($p.ExitCode -ne 0) { throw "Installer failed with exit code $($p.ExitCode)" }
"SEGGER install completed: $(Get-Date -Format o)" | Add-Content -LiteralPath $log
Get-Content -LiteralPath $log
