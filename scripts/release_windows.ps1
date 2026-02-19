param(
  [string]$Version = "v0.2.1"
)

$ErrorActionPreference = "Stop"

# garantir template de .env placeholder (sem segredos)
$envTemplatePath = ".\\release\\.env.example"
if (-not (Test-Path $envTemplatePath)) {
$envTemplateContent = @'
CLOUD_BASE_URL=https://api.dalevision.com
STORE_ID=
EDGE_TOKEN=
AGENT_ID=edge-001
HEARTBEAT_INTERVAL_SECONDS=30
CAMERA_HEARTBEAT_INTERVAL_SECONDS=30
DASHBOARD_URL=https://app.dalevision.com/app/cameras?onboarding=true
ENABLE_AUTO_UPDATE=0
UPDATE_CHECK_URL=
UPDATE_INTERVAL_SECONDS=21600
'@
  Set-Content -Path $envTemplatePath -Value $envTemplateContent
}

# 1) limpar release/win
Remove-Item -Recurse -Force .\release\win -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path .\release\win | Out-Null

# 2) copiar artefatos obrigatórios
Copy-Item .\dist\dalevision-edge-agent.exe .\release\win\"DaleVision Edge Agent.exe" -Force
# Opcional (se houver pipeline de assinatura): assinar o exe aqui antes do zip.
Copy-Item .\release\README.txt .\release\win\README.txt -Force
Copy-Item ".\\release\\01 - Iniciar Agent.bat" ".\\release\\win\\01 - Iniciar Agent.bat" -Force
Copy-Item ".\\release\\02 - Teste rápido (run once).bat" ".\\release\\win\\02 - Teste rápido (run once).bat" -Force
Copy-Item ".\\release\\03 - Diagnóstico (gerar ZIP).bat" ".\\release\\win\\03 - Diagnóstico (gerar ZIP).bat" -Force
Copy-Item .\scripts\install-service.ps1 ".\\release\\win\\04 - Instalar como Serviço (Admin).ps1" -Force

# 3) criar .env placeholder (nunca .env real com segredos)
Copy-Item .\release\.env.example .\release\win\.env -Force

# 4) remover quaisquer secrets/logs antes do zip
Remove-Item .\release\win\stdout.log -Force -ErrorAction SilentlyContinue
if (Test-Path .\release\win\logs) {
  Remove-Item .\release\win\logs\* -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Path .\release\win\logs | Out-Null
}

# 5) validar arquivos obrigatórios
$required = @(
  "DaleVision Edge Agent.exe",
  "01 - Iniciar Agent.bat",
  "02 - Teste rápido (run once).bat",
  "03 - Diagnóstico (gerar ZIP).bat",
  "04 - Instalar como Serviço (Admin).ps1",
  "README.txt",
  ".env"
)
$missing = $required | Where-Object { -not (Test-Path (Join-Path .\release\win $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\\win: $($missing -join ', ')"
}

# 6) zipar
$zipName = "dalevision-edge-agent-windows.zip"
Remove-Item .\$zipName -Force -ErrorAction SilentlyContinue
Compress-Archive -Path .\release\win\* -DestinationPath .\$zipName

# 7) sanity check
python -c "import zipfile; z=zipfile.ZipFile('$zipName'); names=[i.filename for i in z.infolist()]; required={'DaleVision Edge Agent.exe','01 - Iniciar Agent.bat','02 - Teste rápido (run once).bat','03 - Diagnóstico (gerar ZIP).bat','04 - Instalar como Serviço (Admin).ps1','README.txt','.env'}; missing=required-set(names); assert not missing, f'Missing {missing}'; assert '.env.example' not in names, 'Found .env.example in ZIP'; print('ZIP_OK files=', names)"

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"
