param(
  [string]$Version = "v0.2.1",
  [string]$ModelUrl = $env:DALE_VISION_MODEL_URL
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$releaseRoot = Join-Path $repoRoot "release"
$releaseWin = Join-Path $releaseRoot "win"
$distExe = Join-Path $repoRoot "dist\dalevision-edge-agent.exe"
$modelPath = Join-Path $repoRoot "yolov8n.pt"
$envTemplatePath = Join-Path $releaseRoot ".env.template"
$buildInfoPath = Join-Path $releaseWin "BUILD_INFO.txt"

if ([string]::IsNullOrWhiteSpace($ModelUrl)) {
  $ModelUrl = ""
}

function Assert-FileExists {
  param(
    [string]$Path,
    [string]$Label
  )

  if (-not (Test-Path $Path)) {
    throw "Missing required source file: $Label ($Path)"
  }
}

function Assert-BinaryRunnable {
  param(
    [string]$Path
  )

  $stdoutPath = Join-Path $repoRoot "_release_exe_stdout.log"
  $stderrPath = Join-Path $repoRoot "_release_exe_stderr.log"
  Remove-Item -Force $stdoutPath, $stderrPath -ErrorAction SilentlyContinue
  try {
    $proc = Start-Process -FilePath $Path -ArgumentList "--help" -PassThru -Wait -NoNewWindow `
      -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    if ($proc.ExitCode -ne 0) {
      $stderr = if (Test-Path $stderrPath) { Get-Content -Raw $stderrPath } else { "" }
      $stdout = if (Test-Path $stdoutPath) { Get-Content -Raw $stdoutPath } else { "" }
      $detail = ($stderr + "`n" + $stdout).Trim()
      throw "Executable sanity check failed with exit code $($proc.ExitCode). $detail"
    }
  } finally {
    Remove-Item -Force $stdoutPath, $stderrPath -ErrorAction SilentlyContinue
  }
}

function Ensure-Model {
  param(
    [string]$Path,
    [string]$Url
  )

  if (Test-Path $Path) {
    return
  }

  $urls = @()
  if (-not [string]::IsNullOrWhiteSpace($Url)) {
    $urls += $Url
  } else {
    $urls += @(
      "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt",
      "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt",
      "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
    )
  }

  Write-Host "Modelo nao encontrado. Baixando yolov8n.pt..."
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

  $lastError = ""
  foreach ($candidate in $urls) {
    try {
      Write-Host "MODEL_URL=$candidate"
      Invoke-WebRequest -Uri $candidate -OutFile $Path
      if (Test-Path $Path) {
        return
      }
    } catch {
      $lastError = $_.Exception.Message
      Write-Host "Falha ao baixar de $candidate. Detalhes: $lastError"
    }
  }

  throw "Falha ao baixar yolov8n.pt. Defina DALE_VISION_MODEL_URL ou coloque o arquivo em $Path. Ultimo erro: $lastError"
}

# 0) garantir modelo
Ensure-Model -Path $modelPath -Url $ModelUrl

# 1) validar fontes obrigatorias
$requiredSources = @(
  @{ Path = $distExe; Label = "dalevision-edge-agent.exe (dist)" },
  @{ Path = $modelPath; Label = "yolov8n.pt" },
  @{ Path = $envTemplatePath; Label = ".env.template" },
  @{ Path = (Join-Path $releaseRoot "README.txt"); Label = "README.txt" },
  @{ Path = (Join-Path $releaseRoot "01_TESTE_RAPIDO.bat"); Label = "01_TESTE_RAPIDO.bat" },
  @{ Path = (Join-Path $releaseRoot "02_INSTALAR_AUTOSTART.bat"); Label = "02_INSTALAR_AUTOSTART.bat" },
  @{ Path = (Join-Path $releaseRoot "03_VERIFICAR_STATUS.bat"); Label = "03_VERIFICAR_STATUS.bat" },
  @{ Path = (Join-Path $releaseRoot "04_REMOVER_AUTOSTART.bat"); Label = "04_REMOVER_AUTOSTART.bat" },
  @{ Path = (Join-Path $releaseRoot "05_PARAR_AGENTE_E_LIBERAR_PASTA.bat"); Label = "05_PARAR_AGENTE_E_LIBERAR_PASTA.bat" },
  @{ Path = (Join-Path $releaseRoot "Diagnose.bat"); Label = "Diagnose.bat" },
  @{ Path = (Join-Path $releaseRoot "run_agent.cmd"); Label = "run_agent.cmd" },
  @{ Path = (Join-Path $releaseRoot "run_agent.vbs"); Label = "run_agent.vbs" },
  @{ Path = (Join-Path $releaseRoot "DaleVisionEdgeSetup.iss"); Label = "DaleVisionEdgeSetup.iss" },
  @{ Path = (Join-Path $repoRoot "scripts\install-service.ps1"); Label = "install-service.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\install-user.ps1"); Label = "install-user.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\uninstall-service.ps1"); Label = "uninstall-service.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\uninstall-user.ps1"); Label = "uninstall-user.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\verify-service.ps1"); Label = "verify-service.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\stop-agent.ps1"); Label = "stop-agent.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\update.ps1"); Label = "update.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\internal\Start_DaleVision_Agent.ps1"); Label = "internal/Start_DaleVision_Agent.ps1" },
  @{ Path = (Join-Path $repoRoot "scripts\internal\Start_DaleVision_Agent.bat"); Label = "internal/Start_DaleVision_Agent.bat" }
)

foreach ($item in $requiredSources) {
  Assert-FileExists -Path $item.Path -Label $item.Label
}
Assert-BinaryRunnable -Path $distExe

# 2) limpar release/win
Remove-Item -Recurse -Force $releaseWin -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path $repoRoot "dalevision-edge-agent-windows.zip") -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $releaseWin | Out-Null

# 3) copiar artefatos obrigatorios (SSOT: pasta release/)
Copy-Item $distExe (Join-Path $releaseWin "dalevision-edge-agent.exe") -Force
Copy-Item $modelPath (Join-Path $releaseWin "yolov8n.pt") -Force
Copy-Item (Join-Path $releaseRoot "README.txt") (Join-Path $releaseWin "README.txt") -Force
Copy-Item (Join-Path $releaseRoot "01_TESTE_RAPIDO.bat") (Join-Path $releaseWin "01_TESTE_RAPIDO.bat") -Force
Copy-Item (Join-Path $releaseRoot "02_INSTALAR_AUTOSTART.bat") (Join-Path $releaseWin "02_INSTALAR_AUTOSTART.bat") -Force
Copy-Item (Join-Path $releaseRoot "03_VERIFICAR_STATUS.bat") (Join-Path $releaseWin "03_VERIFICAR_STATUS.bat") -Force
Copy-Item (Join-Path $releaseRoot "04_REMOVER_AUTOSTART.bat") (Join-Path $releaseWin "04_REMOVER_AUTOSTART.bat") -Force
Copy-Item (Join-Path $releaseRoot "05_PARAR_AGENTE_E_LIBERAR_PASTA.bat") (Join-Path $releaseWin "05_PARAR_AGENTE_E_LIBERAR_PASTA.bat") -Force
Copy-Item (Join-Path $releaseRoot "Diagnose.bat") (Join-Path $releaseWin "Diagnose.bat") -Force
Copy-Item (Join-Path $releaseRoot "run_agent.cmd") (Join-Path $releaseWin "run_agent.cmd") -Force
Copy-Item (Join-Path $releaseRoot "run_agent.vbs") (Join-Path $releaseWin "run_agent.vbs") -Force
Copy-Item (Join-Path $releaseRoot "DaleVisionEdgeSetup.iss") (Join-Path $releaseWin "DaleVisionEdgeSetup.iss") -Force

# 3.5) gerar .env a partir do template
Copy-Item $envTemplatePath (Join-Path $releaseWin ".env") -Force

$scriptsDir = Join-Path $releaseWin "scripts"
$internalDir = Join-Path $scriptsDir "internal"
New-Item -ItemType Directory -Path $internalDir -Force | Out-Null
Copy-Item (Join-Path $repoRoot "scripts\install-service.ps1") (Join-Path $scriptsDir "install-service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\install-user.ps1") (Join-Path $scriptsDir "install-user.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\uninstall-service.ps1") (Join-Path $scriptsDir "uninstall-service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\uninstall-user.ps1") (Join-Path $scriptsDir "uninstall-user.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\install-service.ps1") (Join-Path $scriptsDir "install_service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\uninstall-service.ps1") (Join-Path $scriptsDir "uninstall_service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\verify-service.ps1") (Join-Path $scriptsDir "verify-service.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\stop-agent.ps1") (Join-Path $scriptsDir "stop-agent.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\update.ps1") (Join-Path $scriptsDir "update.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\internal\Start_DaleVision_Agent.ps1") (Join-Path $internalDir "Start_DaleVision_Agent.ps1") -Force
Copy-Item (Join-Path $repoRoot "scripts\internal\Start_DaleVision_Agent.bat") (Join-Path $internalDir "Start_DaleVision_Agent.bat") -Force
if (Test-Path (Join-Path $repoRoot "scripts\nssm.exe")) {
  Copy-Item (Join-Path $repoRoot "scripts\nssm.exe") (Join-Path $scriptsDir "nssm.exe") -Force
}

# 4.1) BUILD_INFO.txt
$buildTimestamp = Get-Date -Format o
$gitCommit = ""
try {
  $gitCommit = (& git rev-parse --short HEAD 2>$null).Trim()
} catch {
  $gitCommit = ""
}

$installServicePath = Join-Path $repoRoot "scripts\install-service.ps1"
$installBatPath = Join-Path $releaseRoot "02_INSTALAR_AUTOSTART.bat"

$hashInstallService = (Get-FileHash -Algorithm SHA256 -Path $installServicePath).Hash
$hashInstallBat = (Get-FileHash -Algorithm SHA256 -Path $installBatPath).Hash
$hashExe = (Get-FileHash -Algorithm SHA256 -Path $distExe).Hash

$buildInfo = @(
  "build_timestamp=$buildTimestamp",
  "git_commit=$gitCommit",
  "sha256_install_service_ps1=$hashInstallService",
  "sha256_02_instalar_autostart_bat=$hashInstallBat",
  "sha256_exe=$hashExe"
)
$buildInfo | Set-Content -Path $buildInfoPath

# 5) validar arquivos obrigatorios
$criticalPaths = @(
  (Join-Path $releaseWin "02_INSTALAR_AUTOSTART.bat"),
  (Join-Path $releaseWin "run_agent.cmd"),
  (Join-Path $releaseWin "scripts\\install-service.ps1"),
  (Join-Path $releaseWin "dalevision-edge-agent.exe")
)
$missingCritical = $criticalPaths | Where-Object { -not (Test-Path $_) }
if ($missingCritical.Count -gt 0) {
  throw "Missing critical files in release\\win: $($missingCritical -join ', ')"
}
Write-Host "SHA256 02_INSTALAR_AUTOSTART.bat: $((Get-FileHash -Algorithm SHA256 -Path (Join-Path $releaseWin '02_INSTALAR_AUTOSTART.bat')).Hash)"
Write-Host "SHA256 scripts/install-service.ps1: $((Get-FileHash -Algorithm SHA256 -Path (Join-Path $releaseWin 'scripts\\install-service.ps1')).Hash)"

$required = @(
  "dalevision-edge-agent.exe",
  "yolov8n.pt",
  ".env",
  "01_TESTE_RAPIDO.bat",
  "02_INSTALAR_AUTOSTART.bat",
  "03_VERIFICAR_STATUS.bat",
  "04_REMOVER_AUTOSTART.bat",
  "05_PARAR_AGENTE_E_LIBERAR_PASTA.bat",
  "Diagnose.bat",
  "run_agent.cmd",
  "run_agent.vbs",
  "BUILD_INFO.txt",
  "README.txt",
  "scripts/install-service.ps1",
  "scripts/install-user.ps1",
  "scripts/uninstall-service.ps1",
  "scripts/uninstall-user.ps1",
  "scripts/install_service.ps1",
  "scripts/uninstall_service.ps1",
  "scripts/verify-service.ps1",
  "scripts/stop-agent.ps1",
  "scripts/update.ps1",
  "scripts/internal/Start_DaleVision_Agent.ps1",
  "scripts/internal/Start_DaleVision_Agent.bat"
)
$nssmReleasePath = Join-Path $releaseWin "scripts/nssm.exe"
if (Test-Path $nssmReleasePath) {
  $required += "scripts/nssm.exe"
}
$missing = $required | Where-Object { -not (Test-Path (Join-Path $releaseWin $_)) }
if ($missing.Count -gt 0) {
  throw "Missing required files in release\win: $($missing -join ', ')"
}

# 5.5) validar staging/release nao contem arquivos proibidos
$forbiddenPatterns = @(
  "tools\\*",
  "outputs\\*",
  "configs\\*",
  "videos\\*",
  "edge-agent\\config\\rois\\*.yaml",
  "*.mp4",
  "*.avi",
  "*.mov",
  "*.mkv",
  "*.log"
)
$forbiddenFound = @()
foreach ($pattern in $forbiddenPatterns) {
  $forbiddenFound += Get-ChildItem -Path $releaseWin -Recurse -Force -Filter $pattern -ErrorAction SilentlyContinue
}
if ($forbiddenFound.Count -gt 0) {
  $paths = $forbiddenFound | Select-Object -ExpandProperty FullName
  throw "Release staging contains forbidden files:`n$($paths -join "`n")"
}

# 6) zipar
$zipName = Join-Path $repoRoot "dalevision-edge-agent-windows.zip"
Remove-Item $zipName -Force -ErrorAction SilentlyContinue
$zipPaths = @(
  (Join-Path $releaseWin "*")
)
Compress-Archive -Path $zipPaths -DestinationPath $zipName

# 7) sanity check do ZIP (via extração temporária)
$zipCheckDir = Join-Path $repoRoot "_zip_check"
Remove-Item -Recurse -Force $zipCheckDir -ErrorAction SilentlyContinue
Expand-Archive -Path $zipName -DestinationPath $zipCheckDir -Force
$names = Get-ChildItem -Path $zipCheckDir -Recurse -File | ForEach-Object {
  $_.FullName.Substring($zipCheckDir.Length + 1).Replace("\", "/")
}
Remove-Item -Recurse -Force $zipCheckDir -ErrorAction SilentlyContinue

$missingZip = @()
foreach ($req in $required) {
  $found = $false
  foreach ($name in $names) {
    if ($name -ieq $req -or $name -imatch ([regex]::Escape($req) + "$")) {
      $found = $true
      break
    }
  }
  if (-not $found) {
    $missingZip += $req
  }
}
if ($missingZip.Count -gt 0) {
  throw "Missing required files in ZIP: $($missingZip -join ', ')"
}
$forbiddenZipPatterns = @(
  "^tools/",
  "^videos/",
  "^outputs/",
  "^configs/",
  "^edge-agent/config/rois/.*\\.yaml$",
  "\\.(mp4|avi|mov|mkv)$",
  "\\.log$"
)
$foundForbiddenZip = @()
foreach ($entry in $names) {
  foreach ($pattern in $forbiddenZipPatterns) {
    if ($entry -match $pattern) {
      $foundForbiddenZip += $entry
      break
    }
  }
}
if ($foundForbiddenZip.Count -gt 0) {
  throw "ZIP contains forbidden files: $($foundForbiddenZip -join ', ')"
}
$rootPs1 = $names | Where-Object { $_.EndsWith(".ps1") -and -not $_.StartsWith("scripts/") }
if ($rootPs1.Count -gt 0) {
  throw "ZIP contains .ps1 outside scripts/: $($rootPs1 -join ', ')"
}

Write-Host "OK -> $zipName (ready for GitHub Release $Version)"

# Criar cópia 'latest' para facilitar links estáticos no Render/Vercel
$latestZip = Join-Path $repoRoot "dalevision-edge-agent-windows-latest.zip"
Copy-Item $zipName $latestZip -Force
Write-Host "OK -> $latestZip"
