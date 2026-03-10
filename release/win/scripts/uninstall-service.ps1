param(
  [string]$TaskName = "DaleVisionEdgeAgent",
  [string]$StartupTaskName = "DaleVisionEdgeAgentStartup",
  [string]$UpdateTaskName = "DaleVisionEdgeAgentUpdate"
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Write-Host $line
}

function Remove-TaskIfExists {
  param([string]$Name)
  $queryOutput = cmd.exe /c "schtasks /Query /TN `"$Name`"" 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Log "Tarefa '$Name' nao encontrada."
    return
  }
  Write-Log "Removendo tarefa '$Name'..."
  $deleteOutput = cmd.exe /c "schtasks /Delete /TN `"$Name`" /F" 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Falha ao remover '$Name'. Detalhes: $deleteOutput"
  }
  Write-Log "Tarefa '$Name' removida."
}

try {
  Write-Log "UNINSTALL_START"
  $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Log "ERRO: permissao insuficiente."
    Write-Log "Execute este script como Administrador."
    exit 5
  }

  Remove-TaskIfExists -Name $TaskName
  Remove-TaskIfExists -Name $StartupTaskName
  Remove-TaskIfExists -Name $UpdateTaskName
  Write-Log "RESULT: REMOVED"
  exit 0
} catch {
  Write-Log "ERRO: $($_.Exception.Message)"
  exit 1
}
