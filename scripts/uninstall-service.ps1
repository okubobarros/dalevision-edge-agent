param(
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate",
  [bool]$StopRunningProcess = $true
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Write-Host $line
}

function Invoke-SchtasksSafe {
  param([string[]]$Args)

  $oldEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  try {
    $output = & schtasks.exe @Args 2>&1
    $code = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $oldEap
  }

  return @{
    Code = $code
    Output = ($output | Out-String).Trim()
  }
}

function Is-TaskNotFoundOutput {
  param([string]$Text)
  if ([string]::IsNullOrWhiteSpace($Text)) { return $false }
  return (
    $Text -match "O sistema nao pode encontrar o arquivo especificado" -or
    $Text -match "O sistema não pode encontrar o arquivo especificado" -or
    $Text -match "The system cannot find the file specified"
  )
}

function Remove-TaskIfExists {
  param([string]$Name)

  $res = Invoke-SchtasksSafe -Args @("/Delete", "/TN", $Name, "/F")
  if ($res.Code -eq 0) {
    Write-Log "Tarefa '$Name' removida."
    return
  }

  if (Is-TaskNotFoundOutput -Text $res.Output) {
    Write-Log "Tarefa '$Name' nao encontrada."
    return
  }

  throw "Falha ao remover '$Name'. ExitCode=$($res.Code) Output=$($res.Output)"
}

function Stop-ProcessesByPattern {
  param(
    [string]$Name,
    [string]$CommandLineLike,
    [string]$Label
  )

  $procs = @()
  try {
    $procs = Get-CimInstance Win32_Process -Filter "Name='$Name'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like $CommandLineLike }
  } catch {
    $procs = @()
  }

  foreach ($p in $procs) {
    try {
      Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
      Write-Log ("Processo encerrado: " + $Label + " pid=" + $p.ProcessId)
    } catch {
      Write-Log ("Aviso: falha ao encerrar " + $Label + " pid=" + $p.ProcessId + " erro=" + $_.Exception.Message)
    }
  }
}

function Stop-AgentRuntime {
  # Processo principal do agente
  $agent = Get-Process -Name "dalevision-edge-agent" -ErrorAction SilentlyContinue
  foreach ($p in $agent) {
    try {
      Stop-Process -Id $p.Id -Force -ErrorAction Stop
      Write-Log ("Processo encerrado: dalevision-edge-agent pid=" + $p.Id)
    } catch {
      Write-Log ("Aviso: falha ao encerrar dalevision-edge-agent pid=" + $p.Id + " erro=" + $_.Exception.Message)
    }
  }

  # Launchers criados pelo autostart
  Stop-ProcessesByPattern -Name "wscript.exe" -CommandLineLike "*run_agent.vbs*" -Label "wscript(run_agent.vbs)"
  Stop-ProcessesByPattern -Name "powershell.exe" -CommandLineLike "*Start_DaleVision_Agent.ps1*" -Label "powershell(Start_DaleVision_Agent.ps1)"
}

try {
  Write-Log "UNINSTALL_START"
  $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Log "ERRO: permissao insuficiente."
    Write-Log "Execute este script como Administrador."
    exit 5
  }

  Write-Log "Removendo tarefa '$TaskName'..."
  Remove-TaskIfExists -Name $TaskName
  Write-Log "Removendo tarefa '$StartupTaskName'..."
  Remove-TaskIfExists -Name $StartupTaskName
  Write-Log "Removendo tarefa '$UpdateTaskName'..."
  Remove-TaskIfExists -Name $UpdateTaskName
  if ($StopRunningProcess) {
    Stop-AgentRuntime
  }
  Write-Log "RESULT: REMOVED"
  exit 0
} catch {
  Write-Log "ERRO: $($_.Exception.Message)"
  exit 1
}
