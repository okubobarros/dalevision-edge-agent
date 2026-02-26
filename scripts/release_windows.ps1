param(
  [string]$Version = "v0.2.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$releaseRoot = Join-Path $repoRoot "release"
$releaseWin = Join-Path $releaseRoot "win"
$distExe = Join-Path $repoRoot "dist\dalevision-edge-agent.exe"
$envTemplate = Join-Path $releaseRoot ".env.template"

function Assert-FileExists {
  param(
    [string]$Path,
    [string]$Label
  )

  if (-not (Test-Path $Path)) {
    throw "Missing required source file: $Label ($Path)"
  }
}

# 0) validar fontes obrigatorias
$requiredSources = @(
  @{ Path = $distExe; Label = "dalevision-edge-agent.exe (dist)" },
  @{ Path = (Join-Path $releaseRoot "README.txt"); Label = "README.txt" },
  @{ Path = (Join-Path $releaseRoot "02_TESTE_RAPIDO.bat"); Label = "02_TESTE_RAPIDO.bat" },
  @{ Path = (Join-Path $releaseRoot "03_INSTALAR_AUTOSTART.bat"); Label = "03_INSTALAR_AUTOSTART.bat" },
  @{ Path = (Join-Path $releaseRoot "04_VERIFICAR_STATUS.bat"); Label = "04_VERIFICAR_STATUS.bat" },
  @{ Path = (Join-Path $releaseRoot "05_REMOVER_SERVICO.bat"); Label = "05_REMOVER_SERVICO.bat" },
  @{ Path = (Join-Path $releaseRoot "Start_DaleVision_Agent.bat"); Label = "Start_DaleVision_Agent.bat" },
  @{ Path = (Join-Path $releaseRoot "Start_DaleVision_Agent.ps1"); Label = "Start_DaleVision_Agent.ps1" },
  @{ Path = (Join-Path $releaseRoot "Diagnose.bat"); Label = "Diagnose.bat" },
  @{ Path = (Join-Path $releaseRoot "update.ps1"); Label = "update.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\install-service.ps1"); Label = "install-service.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\uninstall-service.ps1"); Label = "uninstall-service.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\verify-service.ps1"); Label = "verify-service.ps1" },
  @{ Path = $envTemplate; Label = ".env.template" }
)

foreach ($item in $requiredSources) {
  Assert-FileExists -Path $item.Path -Label $item.Label
}

# 1) limpar release/win
Remove-Item -Recurse -Force $releaseWin -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $releaseWin | Out-Null

# 2) copiar artefatos obrigatorios (SSOT: pasta release/)
Copy-Item $distExe (Join-Path $releaseWin "dalevision-edge-agent.exe") -Force
Copy-Item (Join-Path $releaseRoot "README.txt") (Join-Path $releaseWin "README.txt") -Force
Copy-Item (Join-Path $releaseRoot "02_TESTE_RAPIDO.bat") (Join-Path $releaseWin "02_TESTE_RAPIDO.bat") -Force
Copy-Item (Join-Path $releaseRoot "03_INSTALAR_AUTOSTART.bat") (Join-Path $releaseWin "03_INSTALAR_AUTOSTART.bat") -Force
Copy-Item (Join-Path $releaseRoot "04_VERIFICAR_STATUS.bat") (Join-Path $releaseWin "04_VERIFICAR_STATUS.bat") -Force
Copy-Item (Join-Path $releaseRoot "05_REMOVER_SERVICO.bat") (Join-Path $releaseWin "05_REMOVER_SERVICO.bat") -Force
Copy-Item (Join-Path $releaseRoot "Start_DaleVision_Agent.bat") (Join-Path $releaseWin "Start_DaleVision_Agent.bat") -Force
Copy-Item (Join-Path $releaseRoot "Start_DaleVision_Agent.ps1") (Join-Path $releaseWin "Start_DaleVision_Agent.ps1") -Force
Copy-Item (Join-Path $releaseRoot "Diagnose.bat") (Join-Path $releaseWin "Diagnose.bat") -Force
Copy-Item (Join-Path $releaseRoot "update.ps1") (Join-Path $releaseWin "update.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\install-service.ps1") (Join-Path $releaseWin "install-service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\uninstall-service.ps1") (Join-Path $releaseWin "uninstall-service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\verify-service.ps1") (Join-Path $releaseWin "verify-service.ps1") -Force
Copy-Item $envTemplate (Join-Path $releaseWin ".env.template") -Force

# 3) logs/.keep
$logDir = Join-Path $releaseWin "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
New-Item -ItemType File -Path (Join-Path $logDir ".keep") -Force | Out-Null

# 4) validar arquivos obrigatorios
$required = @(
  "dalevision-edge-agent.exe",
  "02_TESTE_RAPIDO.bat",
  "03_INSTALAR_AUTOSTART.bat",
  "04_VERIFICAR_STATUS.bat",
  "05_REMOVER_SERVICO.bat",
  "Start_DaleVision_Agent.bat",
  "Start_DaleVision_Agent.ps1",
  "Diagnose.bat",
  "update.ps1",
  "install-service.ps1",
  "uninstall-service.ps1",
  "verify-service.ps1",
  "README.txt",
  ".env.template",
  "logs/.keep"
)
$missing = $required | Where-Object { -not (Test-Path (Join-Path $releaseWin $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\win: $($missing -join ', ')"
}
if (Test-Path (Join-Path $releaseWin ".env")) {
  throw "Unexpected .env in release\win. Use .env.template only."
}

# 5) zipar
$zipName = Join-Path $repoRoot "dalevision-edge-agent-windows.zip"
Remove-Item $zipName -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $releaseWin "*") -DestinationPath $zipName

# 6) sanity check do ZIP
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipName)
$names = $zip.Entries | ForEach-Object { $_.FullName }
$zip.Dispose()

$missingZip = $required | Where-Object { $names -notcontains $_ }
if ($missingZip.Count -gt 0) {
  throw "Missing required files in ZIP: $($missingZip -join ', ')"
}
if ($names -contains ".env") {
  throw "ZIP contains .env (should include only .env.template)."
}

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"
