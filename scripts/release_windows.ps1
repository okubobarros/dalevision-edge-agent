param(
  [string]$Version = "v0.2.1"
)

$ErrorActionPreference = "Stop"

# garantir template de .env placeholder (sem segredos)
$envTemplatePath = ".\release\.env"
if (-not (Test-Path $envTemplatePath)) {
$envTemplateContent = @"
CLOUD_BASE_URL=
STORE_ID=
EDGE_TOKEN=
AGENT_ID=
HEARTBEAT_INTERVAL_SECONDS=
CAMERA_HEARTBEAT_INTERVAL_SECONDS=
DASHBOARD_URL=
AUTO_UPDATE_ENABLED=0
UPDATE_CHANNEL=stable
UPDATE_GITHUB_REPO=
UPDATE_INTERVAL_SECONDS=
"@
  Set-Content -Path $envTemplatePath -Value $envTemplateContent
}

# 1) limpar release/win
Remove-Item -Recurse -Force .\release\win -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path .\release\win | Out-Null

# 2) copiar artefatos obrigatorios (SSOT: pasta release/)
Copy-Item .\dist\dalevision-edge-agent.exe ".\release\win\dalevision-edge-agent.exe" -Force
# Opcional (se houver pipeline de assinatura): assinar o exe aqui antes do zip.
Copy-Item .\release\README.txt .\release\win\README.txt -Force
Copy-Item .\release\02_TESTE_RAPIDO.bat .\release\win\02_TESTE_RAPIDO.bat -Force
Copy-Item .\release\03_INSTALAR_AUTOSTART.bat .\release\win\03_INSTALAR_AUTOSTART.bat -Force
Copy-Item .\release\04_VERIFICAR_STATUS.bat .\release\win\04_VERIFICAR_STATUS.bat -Force
Copy-Item .\release\05_REMOVER_SERVICO.bat .\release\win\05_REMOVER_SERVICO.bat -Force
Copy-Item .\release\Diagnose.bat .\release\win\Diagnose.bat -Force
$includeUpdate = Test-Path .\release\update.ps1
if ($includeUpdate) {
  Copy-Item .\release\update.ps1 .\release\win\update.ps1 -Force
}
Copy-Item .\scripts\install-service.ps1 ".\release\win\install-service.ps1" -Force
Copy-Item .\scripts\uninstall-service.ps1 ".\release\win\uninstall-service.ps1" -Force
Copy-Item .\scripts\verify-service.ps1 ".\release\win\verify-service.ps1" -Force

# 3) criar .env placeholder (sem segredos)
Copy-Item .\release\.env .\release\win\.env -Force

# 4) remover quaisquer secrets/logs antes do zip
Remove-Item .\release\win\stdout.log -Force -ErrorAction SilentlyContinue
if (Test-Path .\release\win\logs) {
  Remove-Item .\release\win\logs\* -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Path .\release\win\logs | Out-Null
}
New-Item -ItemType File -Path .\release\win\logs\.keep -Force | Out-Null

# 5) validar arquivos obrigatorios
$required = @(
  "dalevision-edge-agent.exe",
  "02_TESTE_RAPIDO.bat",
  "03_INSTALAR_AUTOSTART.bat",
  "04_VERIFICAR_STATUS.bat",
  "05_REMOVER_SERVICO.bat",
  "Diagnose.bat",
  "install-service.ps1",
  "uninstall-service.ps1",
  "verify-service.ps1",
  "README.txt",
  ".env"
)
$requiredOptional = @()
if ($includeUpdate) {
  $requiredOptional += "update.ps1"
}
$requiredAll = $required + $requiredOptional
$missing = $requiredAll | Where-Object { -not (Test-Path (Join-Path .\release\win $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\win: $($missing -join ', ')"
}

# 6) zipar
$zipName = "dalevision-edge-agent-windows.zip"
Remove-Item .\$zipName -Force -ErrorAction SilentlyContinue
Compress-Archive -Path .\release\win\* -DestinationPath .\$zipName

# 7) sanity check
$requiredSet = @(
  "dalevision-edge-agent.exe",
  "02_TESTE_RAPIDO.bat",
  "03_INSTALAR_AUTOSTART.bat",
  "04_VERIFICAR_STATUS.bat",
  "05_REMOVER_SERVICO.bat",
  "Diagnose.bat",
  "install-service.ps1",
  "uninstall-service.ps1",
  "verify-service.ps1",
  "README.txt",
  ".env",
  "logs/.keep"
)
if ($includeUpdate) {
  $requiredSet += "update.ps1"
}
$requiredJson = ($requiredSet | ForEach-Object { "'$_'" }) -join ","
python -c "import zipfile; z=zipfile.ZipFile('$zipName'); names=[i.filename for i in z.infolist()]; required={$requiredJson}; missing=required-set(names); assert not missing, f'Missing {missing}'; print('ZIP_OK files=', names)"

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"
