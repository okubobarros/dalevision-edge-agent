param(
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate"
)

$ErrorActionPreference = "Stop"

function Read-EnvFile {
  param([string]$Path)
  $result = @{}
  if (-not (Test-Path $Path)) {
    return $result
  }
  Get-Content -Path $Path | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) {
      return
    }
    $parts = $line.Split("=", 2)
    if ($parts.Count -eq 2) {
      $key = $parts[0].Trim()
      $value = $parts[1].Trim()
      if ($key -ne "") {
        $result[$key] = $value
      }
    }
  }
  return $result
}

function Show-TaskInfo {
  param(
    [string]$Name
  )

  try {
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction Stop
    $info = Get-ScheduledTaskInfo -TaskName $Name -ErrorAction SilentlyContinue
    Write-Host "OK: $Name"
    if ($info) {
      Write-Host "  State: $($info.State)"
      if ($info.LastRunTime) {
        Write-Host "  LastRun: $($info.LastRunTime)"
      }
      if ($info.LastTaskResult -ne $null) {
        Write-Host "  LastResult: $($info.LastTaskResult)"
      }
      if ($info.NextRunTime) {
        Write-Host "  NextRun: $($info.NextRunTime)"
      }
    }
    if ($task -and $task.Actions) {
      $action = $task.Actions | Select-Object -First 1
      if ($action.Execute) {
        $args = $action.Arguments
        if ([string]::IsNullOrWhiteSpace($args)) { $args = "" }
        Write-Host "  Action: $($action.Execute) $args"
      }
    }
    return $true
  } catch {
    $schtasks = "$env:WINDIR\\System32\\schtasks.exe"
    if (Test-Path $schtasks) {
      $out = & $schtasks /Query /TN $Name 2>&1
      if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: $Name (via schtasks)"
        Write-Host $out
        return $true
      }
    }
    Write-Host "NOT installed: $Name"
    return $false
  }
}

$installRoot = Split-Path -Parent $PSScriptRoot
$programDataRoot = $env:PROGRAMDATA
if ([string]::IsNullOrWhiteSpace($programDataRoot)) {
  $programDataRoot = "C:\ProgramData"
}
$agentLogPrimary = Join-Path $programDataRoot "DaleVision\logs\agent.log"
$agentLogFallback = Join-Path $installRoot "logs\agent.log"
$agentLog = $agentLogPrimary
if (-not (Test-Path $agentLog) -and (Test-Path $agentLogFallback)) {
  $agentLog = $agentLogFallback
}
$updateLog = Join-Path $installRoot "logs\update.log"
$envPath = Join-Path $installRoot ".env"
$envVars = Read-EnvFile -Path $envPath
$autoEnabled = ($envVars["AUTO_UPDATE_ENABLED"] -eq "1")
$buildInfo = Join-Path $installRoot "BUILD_INFO.txt"

if (Test-Path $buildInfo) {
  Write-Host "=== BUILD_INFO (top 10) ==="
  Get-Content -Path $buildInfo -TotalCount 10 | ForEach-Object { Write-Host $_ }
  Write-Host ""
}

Write-Host "=== Agent logon task ==="
$agentOk = Show-TaskInfo -Name $TaskName
Write-Host ""
Write-Host "=== Agent startup task ==="
$startupOk = Show-TaskInfo -Name $StartupTaskName
Write-Host ""
Write-Host "=== Update task ==="
if ($autoEnabled) {
  $updateOk = Show-TaskInfo -Name $UpdateTaskName
  Write-Host ""
} else {
  Write-Host "AUTO_UPDATE_ENABLED=0 (task opcional desabilitada)"
  Write-Host ""
}
Write-Host "Logs:"
Write-Host "  Agent:  $agentLog"
if ($agentLog -ne $agentLogPrimary) {
  Write-Host "  Agent (primary esperado): $agentLogPrimary"
}
Write-Host "  Update: $updateLog"
if (Test-Path $agentLog) {
  Write-Host ""
  Write-Host "Ultimas 80 linhas do agent.log:"
  Get-Content -Path $agentLog -Tail 80 | ForEach-Object { Write-Host "  $_" }

  $lastHeartbeat = $null
  try {
    $lastHeartbeat = Get-Content -Path $agentLog | Select-String -Pattern "Heartbeat" | Select-Object -Last 1
  } catch {
    $lastHeartbeat = $null
  }
  if ($lastHeartbeat) {
    Write-Host ""
    Write-Host "Ultimo heartbeat:"
    Write-Host ("  " + $lastHeartbeat.Line)
  }
} else {
  Write-Host ""
  Write-Host "agent.log nao encontrado."
}

if (Test-Path $updateLog) {
  Write-Host ""
  Write-Host "Ultimas 30 linhas do update.log:"
  Get-Content -Path $updateLog -Tail 30 | ForEach-Object { Write-Host "  $_" }
}

if ($agentOk -or $startupOk) {
  exit 0
}
exit 1
