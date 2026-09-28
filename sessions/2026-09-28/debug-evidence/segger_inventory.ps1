$ErrorActionPreference = 'SilentlyContinue'
$out = [ordered]@{}

$uninstallRoots = @(
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$out.InstalledProducts = Get-ItemProperty $uninstallRoots |
  Where-Object { $_.DisplayName -match 'SEGGER|J-Link|nRF Command Line Tools|nRF Util' } |
  Select-Object DisplayName, DisplayVersion, Publisher, InstallLocation, UninstallString, QuietUninstallString, PSPath

$pathScopes = [ordered]@{
  Machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  User = [Environment]::GetEnvironmentVariable('Path', 'User')
  Process = $env:Path
}
$out.SeggerPathEntries = foreach ($scope in $pathScopes.Keys) {
  foreach ($entry in ($pathScopes[$scope] -split ';')) {
    if ($entry -match 'SEGGER|JLink|J-Link') { [pscustomobject]@{ Scope=$scope; Entry=$entry } }
  }
}

$searchRoots = @(
  $env:ProgramFiles,
  ${env:ProgramFiles(x86)},
  $env:ProgramData,
  $env:LOCALAPPDATA,
  $env:APPDATA,
  'C:\Nordic',
  'C:\nrf',
  'C:\SEGGER',
  'P:\Github'
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$dlls = foreach ($root in $searchRoots) {
  Get-ChildItem -LiteralPath $root -Filter 'JLinkARM.dll' -File -Recurse -Force |
    ForEach-Object {
      $v = $_.VersionInfo
      [pscustomobject]@{ Path=$_.FullName; FileVersion=$v.FileVersion; ProductVersion=$v.ProductVersion; Size=$_.Length; Modified=$_.LastWriteTime }
    }
}
$out.JLinkDlls = $dlls | Sort-Object Path -Unique

$driverText = (& pnputil.exe /enum-drivers /files 2>&1 | Out-String)
$out.PnpUtilRaw = $driverText
$blocks = $driverText -split '(?:\r?\n){2,}'
$out.SeggerDriverBlocks = $blocks | Where-Object { $_ -match '(?im)SEGGER|J-Link|JLink' }

$commands = @('nrfjprog.exe','nrfutil.exe','JLink.exe','JLinkExe.exe','JLinkConfig.exe')
$out.CommandLocations = foreach ($cmd in $commands) {
  $hits = @(Get-Command $cmd -All -ErrorAction SilentlyContinue)
  if ($hits.Count) { foreach ($hit in $hits) { [pscustomobject]@{ Command=$cmd; Path=$hit.Source; Version=$hit.Version.ToString() } } }
  else { [pscustomobject]@{ Command=$cmd; Path=$null; Version=$null } }
}

$nordicRoots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA, 'C:\Nordic', 'C:\nrf') | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$out.NordicExecutables = foreach ($root in $nordicRoots) {
  Get-ChildItem -LiteralPath $root -Include 'nrfjprog.exe','nrfutil.exe' -File -Recurse -Force |
    ForEach-Object { [pscustomobject]@{ Path=$_.FullName; FileVersion=$_.VersionInfo.FileVersion; ProductVersion=$_.VersionInfo.ProductVersion } }
}

$events = Get-WinEvent -FilterHashtable @{ LogName='System'; Id=1001 } -MaxEvents 100 |
  Where-Object { $_.Message -match 'JLink|J-Link|SEGGER|bugcheck|BugCheck' } |
  Select-Object -First 2 TimeCreated, Id, ProviderName, Message
$appCrashes = Get-WinEvent -FilterHashtable @{ LogName='Application'; Id=1000,1001 } -MaxEvents 200 |
  Where-Object { $_.Message -match 'JLink|J-Link|SEGGER|nrfjprog' } |
  Select-Object -First 2 TimeCreated, Id, ProviderName, Message
$out.RecentSystemBugchecks = $events
$out.RecentApplicationCrashes = $appCrashes

$dumpDirs = @('C:\Windows\Minidump','C:\Windows\MEMORY.DMP','C:\Windows\LiveKernelReports')
$out.Dumps = foreach ($d in $dumpDirs) {
  if (Test-Path -LiteralPath $d) {
    Get-Item -LiteralPath $d | ForEach-Object {
      if ($_.PSIsContainer) { Get-ChildItem -LiteralPath $_.FullName -File -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 10 FullName, Length, LastWriteTime }
      else { $_ | Select-Object FullName, Length, LastWriteTime }
    }
  }
}

$out | ConvertTo-Json -Depth 8
