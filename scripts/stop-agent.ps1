param(
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
  [string]$InstallDir = ""
)

$ErrorActionPreference = "Continue"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  if ($script:LogPath) {
    Add-Content -Path $script:LogPath -Value $line
  }
  Write-Host $Message
}

function End-Task {
  param([string]$Name)
  if ([string]::IsNullOrWhiteSpace($Name)) { return }
  try {
    & schtasks.exe /End /TN $Name | Out-Null
    Write-Log "TASK_END ok: $Name"
  } catch {
    Write-Log "TASK_END skip: $Name"
  }
}

function Stop-ProcessesByPattern {
  param(
    [string]$Name,
    [string]$CommandLineLike,
    [string]$Label
  )
  try {
    $procs = Get-CimInstance Win32_Process -Filter "Name='$Name'" -ErrorAction Stop |
      Where-Object { $_.CommandLine -like $CommandLineLike }
  } catch {
    $procs = @()
  }
  foreach ($p in $procs) {
    try {
      Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
      Write-Log "PROC_STOP ok: $Label pid=$($p.ProcessId)"
    } catch {
      Write-Log "PROC_STOP fail: $Label pid=$($p.ProcessId)"
    }
  }
}

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  $InstallDir = Split-Path -Parent $scriptDir
}

$logDir = Join-Path $InstallDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$script:LogPath = Join-Path $logDir "stop_agent.log"

Write-Log "STOP001 stopping edge agent processes install_dir=$InstallDir"

End-Task -Name $TaskName
End-Task -Name $StartupTaskName
End-Task -Name $UpdateTaskName

Stop-ProcessesByPattern -Name "dalevision-edge-agent.exe" -CommandLineLike "*" -Label "dalevision-edge-agent.exe"
Stop-ProcessesByPattern -Name "wscript.exe" -CommandLineLike "*run_agent.vbs*" -Label "wscript(run_agent.vbs)"
Stop-ProcessesByPattern -Name "powershell.exe" -CommandLineLike "*Start_DaleVision_Agent.ps1*" -Label "powershell(Start_DaleVision_Agent.ps1)"

Start-Sleep -Milliseconds 800
Write-Log "STOP002 done"

