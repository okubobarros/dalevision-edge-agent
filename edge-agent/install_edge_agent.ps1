param(
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$StoreId,
  [Parameter(Mandatory=$true)][string]$EdgeToken,
  [Parameter(Mandatory=$true)][string]$AgentId = "edge-001",
  [string]$TaskName = "DALE Edge Agent",
  [int]$Port = 7860,
  [string]$RunAsUser = "",
  [string]$RunAsPassword = ""
)

$ErrorActionPreference = "Stop"

function Test-IsAdmin {
  try {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch { return $false }
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "== DALE Edge Agent Installer =="

if (-not (Test-IsAdmin)) {
  Write-Host "⚠️  Rode este script como ADMIN para criar o Task Scheduler corretamente." -ForegroundColor Yellow
  Write-Host "    (Right click PowerShell -> Run as Administrator)" -ForegroundColor Yellow
}

# 0) logs
$logsDir = Join-Path $root "logs"
if (-not (Test-Path $logsDir)) {
  New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# 1) venv local (padrão: .\venv)
$venvPath = Join-Path $root "venv"
if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
  Write-Host "== venv not found. Running 01_setup.bat =="
  & (Join-Path $root "01_setup.bat")
}

$py = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $py)) {
  throw "venv não encontrado em $venvPath. Execute 01_setup.bat manualmente."
}

# 2) Escrever config/env (simples)
$envFile = Join-Path $root ".env"
$envLines = @(
  "DALE_CLOUD_BASE_URL=$BaseUrl"
  "DALE_STORE_ID=$StoreId"
  "DALE_EDGE_TOKEN=$EdgeToken"
  "DALE_AGENT_ID=$AgentId"
  "DALE_STATUS_PORT=$Port"
)
$envLines | Set-Content -Path $envFile -Encoding UTF8
Write-Host "✅ .env escrito em: $envFile"

# 3) Criar Task Scheduler (auto-start)
$runBat = Join-Path $root "02_run.bat"
if (-not (Test-Path $runBat)) {
  throw "02_run.bat não encontrado em $runBat"
}

$cmd = "cmd.exe /c `"cd /d `"$root`" && `"$runBat`" --heartbeat-only >> logs\\task.out.log 2>> logs\\task.err.log`""
Write-Host "== Create/Update Scheduled Task: $TaskName =="

try {
  schtasks /Delete /TN $TaskName /F | Out-Null
} catch {}

if (-not $RunAsUser) {
  $RunAsUser = "$env:USERDOMAIN\$env:USERNAME"
}

if ((Test-IsAdmin) -and $RunAsPassword) {
  schtasks /Create /TN $TaskName /SC ONSTART /RU $RunAsUser /RP $RunAsPassword /RL HIGHEST /TR $cmd /F | Out-Null
  Write-Host "✅ Task criada (ONSTART, usuário atual): $TaskName"
} else {
  schtasks /Create /TN $TaskName /SC ONLOGON /RU $RunAsUser /RL LIMITED /TR $cmd /F | Out-Null
  Write-Host "✅ Task criada (ONLOGON do usuário): $TaskName"
  Write-Host "ℹ️  Para rodar mesmo sem usuário logado, execute como admin com -RunAsPassword."
}

Write-Host ""
Write-Host "➡️  Inicie agora com:"
Write-Host "   schtasks /Run /TN `"$TaskName`""
Write-Host ""
Write-Host "➡️  Status local:"
Write-Host "   http://127.0.0.1:$Port/status"
