param(
  [string]$TaskName = "DaleVisionEdgeAgent"
)

$ErrorActionPreference = "Stop"

try {
  $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
  $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue

  Write-Host "Service installed OK"
  if ($info) {
    Write-Host "State: $($info.State)"
    if ($info.LastRunTime) {
      Write-Host "LastRun: $($info.LastRunTime)"
    }
    if ($info.LastTaskResult -ne $null) {
      Write-Host "LastResult: $($info.LastTaskResult)"
    }
  }
  Write-Host "To remove: schtasks /Delete /TN `"$TaskName`" /F"
  exit 0
} catch {
  Write-Host "Service NOT installed."
  Write-Host "To install: install-service.ps1"
  Write-Host "To remove (if exists): schtasks /Delete /TN `"$TaskName`" /F"
  exit 1
}
