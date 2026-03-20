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

function Parse-BoolEnv {
  param(
    [string]$Raw,
    [bool]$Default = $false
  )

  if ([string]::IsNullOrWhiteSpace($Raw)) {
    return $Default
  }

  switch ($Raw.Trim().ToLowerInvariant()) {
    "1" { return $true }
    "true" { return $true }
    "yes" { return $true }
    "on" { return $true }
    "0" { return $false }
    "false" { return $false }
    "no" { return $false }
    "off" { return $false }
    default { return $Default }
  }
}

function Get-AutoUpdateEnabled {
  param([hashtable]$EnvVars)

  foreach ($key in @("AUTO_UPDATE_ENABLED", "ENABLE_AUTO_UPDATE")) {
    $raw = $EnvVars[$key]
    if ([string]::IsNullOrWhiteSpace($raw)) {
      continue
    }
    return (Parse-BoolEnv -Raw $raw -Default $false)
  }
  return $true
}

function Format-TaskResult {
  param([int]$Code)

  if ($Code -eq 0) { return "0x00000000 (sucesso)" }
  if ($Code -eq 267009) { return "0x00041301 (task em execucao)" }
  if ($Code -eq 267011) { return "0x00041303 (ainda nao executou)" }
  if ($Code -eq 267014) { return "0x00041306 (task finalizada)" }

  $hex = ('0x{0:X8}' -f $Code)
  return "$hex"
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
        $resultCode = [int]$info.LastTaskResult
        Write-Host "  LastResult: $resultCode ($(Format-TaskResult -Code $resultCode))"
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

function StartupTaskEnabled {
  param([hashtable]$EnvVars)
  foreach ($key in @("STARTUP_TASK_ENABLED", "EDGE_STARTUP_TASK_ENABLED")) {
    $raw = $EnvVars[$key]
    if ([string]::IsNullOrWhiteSpace($raw)) {
      continue
    }
    return (Parse-BoolEnv -Raw $raw -Default $true)
  }
  return $true
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
$autoEnabled = Get-AutoUpdateEnabled -EnvVars $envVars
$repo = $envVars["UPDATE_GITHUB_REPO"]
$startupEnabled = StartupTaskEnabled -EnvVars $envVars
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
if ($startupEnabled) {
  $startupOk = Show-TaskInfo -Name $StartupTaskName
} else {
  Write-Host "STARTUP_TASK_ENABLED=0 (task startup desabilitada por .env)"
  $startupOk = $false
}
Write-Host ""
Write-Host "=== Update task ==="
if ([string]::IsNullOrWhiteSpace($repo)) {
  Write-Host "UPDATE_GITHUB_REPO ausente (task de update nao aplicavel)."
  Write-Host ""
} elseif ($autoEnabled) {
  $updateOk = Show-TaskInfo -Name $UpdateTaskName
  Write-Host ""
} else {
  Write-Host "AUTO_UPDATE desabilitado por .env (AUTO_UPDATE_ENABLED=0)."
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

if ($agentOk -or ($startupEnabled -and $startupOk)) {
  exit 0
}
exit 1
