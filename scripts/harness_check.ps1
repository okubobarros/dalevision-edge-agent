param(
  [switch]$SkipTests,
  [switch]$Quick,
  [string]$EnvPath = ".env",
  [string]$AgentLogPath = "logs/agent.log"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$failures = New-Object System.Collections.Generic.List[string]
$checks = New-Object System.Collections.Generic.List[string]

function Add-Pass {
  param([string]$Message)
  $checks.Add($Message) | Out-Null
  Write-Host "[OK] $Message"
}

function Add-Fail {
  param([string]$Code, [string]$Message)
  $entry = "$Code - $Message"
  $failures.Add($entry) | Out-Null
  Write-Host "[FAIL] $entry"
}

function Read-EnvFile {
  param([string]$Path)

  $result = @{}
  if (-not (Test-Path -LiteralPath $Path)) {
    return $result
  }

  foreach ($lineRaw in (Get-Content -LiteralPath $Path)) {
    $line = $lineRaw.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) {
      continue
    }
    $parts = $line.Split("=", 2)
    if ($parts.Count -ne 2) {
      continue
    }
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($key -ne "") {
      $result[$key] = $value
    }
  }

  return $result
}

Write-Host "== Harness Check =="
Write-Host "Quick mode: $Quick | Skip tests: $SkipTests"

$requiredDocs = @(
  "docs/harness/README.md",
  "docs/harness/progress.md",
  "docs/harness/sensors.md",
  "specs/EDGE-SYSTEM-001-agent-runtime-reliability/spec.md",
  "specs/EDGE-SYSTEM-002-update-flow.md",
  "specs/EDGE-SYSTEM-003-onboarding-frictionless.md"
)

foreach ($doc in $requiredDocs) {
  if (Test-Path -LiteralPath $doc) {
    Add-Pass "Guide/memory presente: $doc"
  } else {
    Add-Fail "HARNESS_DOC_MISSING" "Arquivo ausente: $doc"
  }
}

$requiredEnvKeys = @("CLOUD_BASE_URL", "STORE_ID", "EDGE_TOKEN", "AGENT_ID")
$envData = Read-EnvFile -Path $EnvPath
if ($envData.Count -eq 0) {
  Add-Fail "ENV_FILE_MISSING" "Nao encontrei .env em '$EnvPath'."
} else {
  $missing = @()
  foreach ($key in $requiredEnvKeys) {
    if (-not $envData.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$envData[$key])) {
      $missing += $key
    }
  }

  if ($missing.Count -gt 0) {
    Add-Fail "ENV_REQUIRED_MISSING" ("Chaves obrigatorias ausentes no .env: " + ($missing -join ", "))
  } else {
    Add-Pass ".env contem chaves obrigatorias (sem exibir valores)."
  }
}

$logSecretPatterns = @(
  "EDGE_TOKEN\s*=",
  "Authorization\s*:",
  "Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*",
  "rtsp:\/\/[^ ]+:[^ @]+@"
)

if (Test-Path -LiteralPath $AgentLogPath) {
  $matches = @()
  foreach ($pattern in $logSecretPatterns) {
    $result = Select-String -Path $AgentLogPath -Pattern $pattern -SimpleMatch:$false
    if ($result) {
      $matches += $pattern
    }
  }

  if ($matches.Count -gt 0) {
    Add-Fail "LOG_SECRET_RISK" ("Padroes sensiveis encontrados em ${AgentLogPath}: " + ($matches -join " | "))
  } else {
    Add-Pass "Higiene de logs OK (sem padroes sensiveis em $AgentLogPath)."
  }
} else {
  Add-Pass "Log do agente nao encontrado em $AgentLogPath (checagem de segredo ignorada)."
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  Add-Fail "PYTHON_NOT_FOUND" "Python nao encontrado no PATH."
}

if (-not $SkipTests -and -not $Quick -and $pythonCmd) {
  Write-Host "Executando testes criticos..."
  $testArgs = @(
    "-m", "pytest", "-q",
    "tests/test_onboarding_readiness.py",
    "tests/test_setup_api.py",
    "tests/test_onboarding_events.py",
    "tests/test_onboarding_error_codes.py",
    "tests/test_heartbeat.py",
    "tests/test_doctor_pytest.py::test_doctor_generates_summary",
    "tests/test_activation_bootstrap.py"
  )

  $oldLocalAppData = [Environment]::GetEnvironmentVariable("LOCALAPPDATA", "Process")
  $oldProgramData = [Environment]::GetEnvironmentVariable("PROGRAMDATA", "Process")
  $harnessTmpRoot = Join-Path (Get-Location) ".tmp\\harness-check"
  New-Item -ItemType Directory -Path $harnessTmpRoot -Force | Out-Null
  [Environment]::SetEnvironmentVariable("LOCALAPPDATA", $harnessTmpRoot, "Process")
  [Environment]::SetEnvironmentVariable("PROGRAMDATA", $harnessTmpRoot, "Process")

  & python @testArgs

  [Environment]::SetEnvironmentVariable("LOCALAPPDATA", $oldLocalAppData, "Process")
  [Environment]::SetEnvironmentVariable("PROGRAMDATA", $oldProgramData, "Process")
  if ($LASTEXITCODE -ne 0) {
    Add-Fail "TEST_CRITICAL_FAILED" "Falha nos testes criticos de onboarding/runtime."
  } else {
    Add-Pass "Testes criticos de onboarding/runtime passaram."
  }
} elseif ($Quick -and $pythonCmd) {
  Write-Host "Quick mode: validando import basico do agente..."
  & python -c "import dalevision_edge_agent"
  if ($LASTEXITCODE -ne 0) {
    Add-Fail "RUNTIME_IMPORT_FAILED" "Import basico do agente falhou."
  } else {
    Add-Pass "Import basico do agente OK."
  }
}

Write-Host ""
Write-Host "== Resumo Harness Check =="
Write-Host "Checks OK: $($checks.Count)"
Write-Host "Falhas: $($failures.Count)"

if ($failures.Count -gt 0) {
  Write-Host ""
  Write-Host "Falhas encontradas:"
  foreach ($failure in $failures) {
    Write-Host " - $failure"
  }
  exit 1
}

exit 0
