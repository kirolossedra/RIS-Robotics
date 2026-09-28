$ErrorActionPreference = 'SilentlyContinue'
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime

$present = Get-PnpDevice -PresentOnly
$matches = foreach ($dev in $present) {
  $props = Get-PnpDeviceProperty -InstanceId $dev.InstanceId
  $map = @{}
  foreach ($p in $props) { $map[$p.KeyName] = $p.Data }
  $friendly = [string]$map['DEVPKEY_Device_FriendlyName']
  if (-not $friendly) { $friendly = [string]$dev.FriendlyName }
  $manufacturer = [string]$map['DEVPKEY_Device_Manufacturer']
  $hardwareIds = @($map['DEVPKEY_Device_HardwareIds'])
  $isMatch = $friendly -match '(?i)J-?Link|SEGGER' -or
             $manufacturer -match '(?i)SEGGER' -or
             (($hardwareIds -join ';') -match '(?i)VID_1366|SEGGER|JLINK|J-LINK')
  if ($isMatch) {
    $driverInf = [string]$map['DEVPKEY_Device_DriverInfPath']
    $signed = Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceID -eq $dev.InstanceId } | Select-Object -First 1
    [pscustomobject]@{
      Status = $dev.Status
      ProblemCode = $dev.Problem
      ConfigManagerErrorCode = $signed.ConfigManagerErrorCode
      Class = if ($dev.Class) { $dev.Class } else { [string]$map['DEVPKEY_Device_Class'] }
      FriendlyName = $friendly
      InstanceId = $dev.InstanceId
      Parent = [string]$map['DEVPKEY_Device_Parent']
      Manufacturer = $manufacturer
      HardwareIds = $hardwareIds
      DriverProvider = if ($signed.DriverProviderName) { $signed.DriverProviderName } else { [string]$map['DEVPKEY_Device_DriverProvider'] }
      DriverVersion = if ($signed.DriverVersion) { $signed.DriverVersion } else { [string]$map['DEVPKEY_Device_DriverVersion'] }
      DriverDate = if ($signed.DriverDate) { $signed.DriverDate } else { $map['DEVPKEY_Device_DriverDate'] }
      DriverInf = if ($signed.InfName) { $signed.InfName } else { $driverInf }
      Service = [string]$map['DEVPKEY_Device_Service']
      ProblemStatus = [string]$map['DEVPKEY_Device_ProblemStatus']
    }
  }
}

$matchIds = @($matches.InstanceId)
$parents = @($matches.Parent | Where-Object { $_ } | Select-Object -Unique)
$related = foreach ($dev in $present) {
  $props = Get-PnpDeviceProperty -InstanceId $dev.InstanceId
  $map = @{}
  foreach ($p in $props) { $map[$p.KeyName] = $p.Data }
  $parent = [string]$map['DEVPKEY_Device_Parent']
  $hw = @($map['DEVPKEY_Device_HardwareIds'])
  if ($dev.InstanceId -notin $matchIds -and
      ($parent -in $parents -or $dev.InstanceId -in $parents -or (($hw -join ';') -match '(?i)VID_1366'))) {
    [pscustomobject]@{
      Status=$dev.Status; ProblemCode=$dev.Problem; Class=$dev.Class; FriendlyName=$dev.FriendlyName
      InstanceId=$dev.InstanceId; Parent=$parent; Manufacturer=[string]$map['DEVPKEY_Device_Manufacturer']; HardwareIds=$hw
    }
  }
}

$problemDevices = foreach ($dev in $present | Where-Object { $_.Status -ne 'OK' -or ($_.Problem -and $_.Problem -ne 'CM_PROB_NONE') }) {
  $props = Get-PnpDeviceProperty -InstanceId $dev.InstanceId
  $map = @{}
  foreach ($p in $props) { $map[$p.KeyName] = $p.Data }
  $hw = @($map['DEVPKEY_Device_HardwareIds'])
  $parent = [string]$map['DEVPKEY_Device_Parent']
  if ($dev.InstanceId -in $matchIds -or $parent -in $parents -or $dev.InstanceId -in $parents -or (($hw -join ';') -match '(?i)VID_1366|SEGGER|JLINK|J-LINK')) {
    [pscustomobject]@{
      Status=$dev.Status; ProblemCode=$dev.Problem; Class=$dev.Class; FriendlyName=$dev.FriendlyName
      InstanceId=$dev.InstanceId; Parent=$parent; HardwareIds=$hw
    }
  }
}

$events = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$boot; Level=2,3} |
  Where-Object {
    $_.ProviderName -match '(?i)Kernel-PnP|USB|DriverFrameworks|UserPnp|WHEA' -or
    $_.Message -match '(?i)J-?Link|SEGGER|VID_1366|USB|driver.*(?:fail|error)|failed.*driver'
  } | Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message

[ordered]@{
  BootTime = $boot
  CapturedAt = Get-Date
  Matches = @($matches)
  RelatedDevices = @($related)
  MatchingProblemDevices = @($problemDevices)
  RelevantSystemEvents = @($events)
} | ConvertTo-Json -Depth 8
