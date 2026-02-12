param(
  [string]$Version = "v0.2.1"
)

$ErrorActionPreference = "Stop"

# garantir .env.example placeholder
$envExamplePath = ".\\release\\.env.example"
if (-not (Test-Path $envExamplePath)) {
  $envExampleContent = @'
CLOUD_BASE_URL=https://api.dalevision.com
STORE_ID=
EDGE_TOKEN=
AGENT_ID=edge-001
HEARTBEAT_INTERVAL_SECONDS=30
CAMERA_HEARTBEAT_INTERVAL_SECONDS=30
'@
  Set-Content -Path $envExamplePath -Value $envExampleContent
}

# 1) limpar release/win
Remove-Item -Recurse -Force .\release\win -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path .\release\win | Out-Null

# 2) copiar artefatos obrigatórios
Copy-Item .\dist\dalevision-edge-agent.exe .\release\win\dalevision-edge-agent.exe -Force
Copy-Item .\release\README.txt .\release\win\README.txt -Force
Copy-Item .\release\run.bat .\release\win\run.bat -Force

# 3) criar .env.example placeholder (nunca .env real)
Copy-Item .\release\.env.example .\release\win\.env.example -Force

# 4) remover quaisquer secrets/logs antes do zip
Remove-Item .\release\win\.env -Force -ErrorAction SilentlyContinue
Remove-Item .\release\win\stdout.log -Force -ErrorAction SilentlyContinue
if (Test-Path .\release\win\logs) {
  Remove-Item .\release\win\logs\* -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Path .\release\win\logs | Out-Null
}

# 5) validar arquivos obrigatórios
$required = @("dalevision-edge-agent.exe", "run.bat", "README.txt", ".env.example")
$missing = $required | Where-Object { -not (Test-Path (Join-Path .\release\win $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\\win: $($missing -join ', ')"
}
if (Test-Path .\release\win\.env) {
  throw "release\\win\\.env should not exist before zip"
}

# 6) zipar
$zipName = "dalevision-edge-agent-windows.zip"
Remove-Item .\$zipName -Force -ErrorAction SilentlyContinue
Compress-Archive -Path .\release\win\* -DestinationPath .\$zipName

# 7) sanity check
python -c "import zipfile; z=zipfile.ZipFile('$zipName'); names=[i.filename for i in z.infolist()]; required={'dalevision-edge-agent.exe','run.bat','README.txt','.env.example'}; missing=required-set(names); assert not missing, f'Missing {missing}'; assert '.env' not in names, 'Found .env in ZIP'; print('ZIP_OK files=', names)"

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"
