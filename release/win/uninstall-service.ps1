param(
  [string]$TaskName = "DaleVisionEdgeAgent"
)

$ErrorActionPreference = "Stop"

function Write-Log {
  param([string]$Message)
  $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "$timestamp $Message"
  Write-Host $line
}

try {
  $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Log "ERRO: permissao insuficiente."
    Write-Log "Execute este script como Administrador."
    Write-Log "Pressione Enter para sair."
    Read-Host | Out-Null
    exit 1
  }

  $queryOutput = cmd.exe /c "schtasks /Query /TN `"$TaskName`"" 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Log "Tarefa '$TaskName' nao encontrada. Nada a remover."
    exit 0
  }

  Write-Log "Removendo tarefa '$TaskName'..."
  $deleteOutput = cmd.exe /c "schtasks /Delete /TN `"$TaskName`" /F" 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Falha ao remover a tarefa. Detalhes: $deleteOutput"
  }

  Write-Log "Tarefa removida com sucesso."
} catch {
  Write-Log "ERRO: $($_.Exception.Message)"
  Write-Log "Pressione Enter para sair."
  Read-Host | Out-Null
  exit 1
}
