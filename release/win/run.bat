@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>&1
set "LOG_FILE=logs\stdout.log"
echo [%DATE% %TIME%] START run.bat %* > "%LOG_FILE%"

echo ===============================
>> "%LOG_FILE%" echo ===============================
echo DALE Vision Edge Agent - Windows
>> "%LOG_FILE%" echo DALE Vision Edge Agent - Windows
echo ===============================
>> "%LOG_FILE%" echo ===============================
echo.
>> "%LOG_FILE%" echo.
echo Checklist:
>> "%LOG_FILE%" echo Checklist:
echo   - Caminho atual: %CD%
>> "%LOG_FILE%" echo   - Caminho atual: %CD%

set "MISSING_REQUIRED=0"
if exist "run.bat" (
  echo   - run.bat: OK
  >> "%LOG_FILE%" echo   - run.bat: OK
) else (
  echo   - run.bat: FALTA
  >> "%LOG_FILE%" echo   - run.bat: FALTA
  set "MISSING_REQUIRED=1"
)

if exist "dalevision-edge-agent.exe" (
  echo   - dalevision-edge-agent.exe: OK
  >> "%LOG_FILE%" echo   - dalevision-edge-agent.exe: OK
) else (
  echo   - dalevision-edge-agent.exe: FALTA
  >> "%LOG_FILE%" echo   - dalevision-edge-agent.exe: FALTA
  set "MISSING_REQUIRED=1"
)

if exist ".env" (
  echo   - .env: OK
  >> "%LOG_FILE%" echo   - .env: OK
) else (
  echo   - .env: FALTA
  >> "%LOG_FILE%" echo   - .env: FALTA
  set "MISSING_REQUIRED=1"
)

if "!MISSING_REQUIRED!"=="1" (
  echo ERRO: Arquivos obrigatorios ausentes. Corrija e rode novamente.
  >> "%LOG_FILE%" echo ERRO: Arquivos obrigatorios ausentes. Corrija e rode novamente.
  >> "%LOG_FILE%" echo [%DATE% %TIME%] EXIT code=2
  exit /b 2
)

echo.
>> "%LOG_FILE%" echo.
echo Variaveis do .env mascaradas:
>> "%LOG_FILE%" echo Variaveis do .env mascaradas:
set "ENV_TMP=%TEMP%\dalevision_envcheck_%RANDOM%.log"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$vals=@{}; Get-Content '.env' | ForEach-Object { if ($_ -match '^\s*#' -or $_ -notmatch '=') { continue }; $pair=$_.Split('=',2); $vals[$pair[0].Trim()]=$pair[1].Trim() };" ^
  "function Test-Invalid([string]$v) { if ([string]::IsNullOrWhiteSpace($v)) { return $true }; $t=$v.Trim().ToLowerInvariant(); if ($t.Contains('<') -or $t.Contains('>') -or $t.Contains('changeme')) { return $true }; return $false };" ^
  "function Mask([string]$v) { if ([string]::IsNullOrEmpty($v)) { return '(vazio)' }; if ($v.Length -le 8) { return $v }; return ($v.Substring(0,4) + '...' + $v.Substring($v.Length-4)) };" ^
  "$base=$vals['CLOUD_BASE_URL']; $store=$vals['STORE_ID']; $token=$vals['EDGE_TOKEN'];" ^
  "$baseOut='(vazio)'; if (-not [string]::IsNullOrWhiteSpace($base)) { $baseOut=$base };" ^
  "Write-Output ('  - CLOUD_BASE_URL=' + $baseOut);" ^
  "Write-Output ('  - STORE_ID=' + (Mask $store));" ^
  "Write-Output ('  - EDGE_TOKEN=' + (Mask $token));" ^
  "if (Test-Invalid $base) { Write-Output 'ERRO: CLOUD_BASE_URL ausente/placeholder no .env'; exit 2 };" ^
  "if (Test-Invalid $store) { Write-Output 'ERRO: STORE_ID ausente/placeholder no .env'; exit 2 };" ^
  "if (Test-Invalid $token) { Write-Output 'ERRO: EDGE_TOKEN ausente/placeholder no .env'; exit 2 };" ^
  "exit 0" > "%ENV_TMP%" 2>&1
set "ENV_CHECK_EXIT=!errorlevel!"
type "%ENV_TMP%"
type "%ENV_TMP%" >> "%LOG_FILE%"
del /f /q "%ENV_TMP%" >nul 2>&1
if not "!ENV_CHECK_EXIT!"=="0" (
  echo ERRO: .env invalido. Corrija os valores e rode novamente.
  >> "%LOG_FILE%" echo ERRO: .env invalido. Corrija os valores e rode novamente.
  >> "%LOG_FILE%" echo [%DATE% %TIME%] EXIT code=2
  exit /b 2
)

echo.
>> "%LOG_FILE%" echo.
echo Iniciando agente...
>> "%LOG_FILE%" echo Iniciando agente...
echo   - stdout/stderr: %CD%\logs\stdout.log
>> "%LOG_FILE%" echo   - stdout/stderr: %CD%\logs\stdout.log
echo   - agent log: %CD%\logs\agent.log
>> "%LOG_FILE%" echo   - agent log: %CD%\logs\agent.log
echo.
>> "%LOG_FILE%" echo.

dalevision-edge-agent.exe %* >> "%LOG_FILE%" 2>&1
set "exit_code=%errorlevel%"

echo.
>> "%LOG_FILE%" echo.
echo Processo finalizado. Exit code=%exit_code%
>> "%LOG_FILE%" echo Processo finalizado. Exit code=%exit_code%
>> "%LOG_FILE%" echo [%DATE% %TIME%] EXIT code=%exit_code%

echo.
echo Pressione uma tecla para fechar...
pause >nul
exit /b %exit_code%
