param(
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate"
)

$ErrorActionPreference = "Stop"

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
    return $true
  } catch {
    Write-Host "NOT installed: $Name"
    return $false
  }
}

$installRoot = $PSScriptRoot
$agentLog = Join-Path $installRoot "logs\agent.log"
$updateLog = Join-Path $installRoot "logs\update.log"

Write-Host "=== Agent task ==="
$agentOk = Show-TaskInfo -Name $TaskName
Write-Host ""
Write-Host "=== Update task ==="
$updateOk = Show-TaskInfo -Name $UpdateTaskName
Write-Host ""
Write-Host "Logs:"
Write-Host "  Agent:  $agentLog"
Write-Host "  Update: $updateLog"
Write-Host "Dica: Get-Content .\\logs\\agent.log -Tail 80"

if ($agentOk) {
  exit 0
}
exit 1
