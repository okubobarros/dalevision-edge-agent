param(
  [string]$WorkDir = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

# Pasta de logs
$LogDir = Join-Path $WorkDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogPath = Join-Path $LogDir ("edge-agent-" + (Get-Date -Format "yyyy-MM-dd") + ".log")

# Ativa venv se existir
$VenvPy = Join-Path $WorkDir "venv\Scripts\python.exe"
if (!(Test-Path $VenvPy)) {
  Write-Host "❌ venv não encontrado. Rode install_edge_agent.ps1 primeiro."
  exit 1
}

# Loop watchdog: se cair, reinicia
while ($true) {
  try {
    $ts = (Get-Date).ToString("s")
    Add-Content -Path $LogPath -Value "[$ts] starting edge agent..."

    # >>> AJUSTE AQUI o comando real do seu agente <<<
    # Opção comum (FastAPI):
    # & $VenvPy -m uvicorn src.main:app --host 0.0.0.0 --port 7860
    #
    # Se seu agente tiver um entrypoint próprio:
    # & $VenvPy -m src.agent.lifecycle

    & $VenvPy -m uvicorn src.main:app --host 0.0.0.0 --port 7860 *>> $LogPath
  }
  catch {
    $ts = (Get-Date).ToString("s")
    Add-Content -Path $LogPath -Value "[$ts] edge agent crashed: $($_.Exception.Message)"
  }

  Start-Sleep -Seconds 3
}
