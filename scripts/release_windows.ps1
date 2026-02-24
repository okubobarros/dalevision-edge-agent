param(
  [string]$Version = "v0.2.1"
)

$ErrorActionPreference = "Stop"

# garantir template de .env placeholder (sem segredos)
$envTemplatePath = ".\release\.env"
if (-not (Test-Path $envTemplatePath)) {
$envTemplateContent = @"
CLOUD_BASE_URL=https://api.dalevision.com
STORE_ID=
EDGE_TOKEN=
AGENT_ID=edge-001
HEARTBEAT_INTERVAL_SECONDS=30
CAMERA_HEARTBEAT_INTERVAL_SECONDS=30
DASHBOARD_URL=https://app.dalevision.com/app/cameras?onboarding=true
AUTO_UPDATE_ENABLED=0
UPDATE_CHANNEL=stable
UPDATE_GITHUB_REPO=
UPDATE_INTERVAL_SECONDS=21600
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
Copy-Item .\release\Start_DaleVision_Agent.bat .\release\win\Start_DaleVision_Agent.bat -Force
Copy-Item .\release\Start_DaleVision_Agent.ps1 .\release\win\Start_DaleVision_Agent.ps1 -Force
Copy-Item .\release\Diagnose.bat .\release\win\Diagnose.bat -Force
Copy-Item .\release\update.ps1 .\release\win\update.ps1 -Force
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
  "Start_DaleVision_Agent.bat",
  "Start_DaleVision_Agent.ps1",
  "Diagnose.bat",
  "update.ps1",
  "install-service.ps1",
  "uninstall-service.ps1",
  "verify-service.ps1",
  "README.txt",
  ".env"
)
$missing = $required | Where-Object { -not (Test-Path (Join-Path .\release\win $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\win: $($missing -join ', ')"
}

# 6) zipar
$zipName = "dalevision-edge-agent-windows.zip"
Remove-Item .\$zipName -Force -ErrorAction SilentlyContinue
Compress-Archive -Path .\release\win\* -DestinationPath .\$zipName

# 7) sanity check
python -c "import zipfile; z=zipfile.ZipFile('$zipName'); names=[i.filename for i in z.infolist()]; required={'dalevision-edge-agent.exe','Start_DaleVision_Agent.bat','Start_DaleVision_Agent.ps1','Diagnose.bat','update.ps1','install-service.ps1','uninstall-service.ps1','verify-service.ps1','README.txt','.env','logs/.keep'}; missing=required-set(names); assert not missing, f'Missing {missing}'; print('ZIP_OK files=', names)"

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"
