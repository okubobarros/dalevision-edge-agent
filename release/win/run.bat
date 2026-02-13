@echo off
setlocal
cd /d %~dp0

echo ===============================
echo DALE Vision Edge Agent (Windows)
echo ===============================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado nesta pasta.
  echo 1) Abra o arquivo .env nesta pasta
  echo 2) Cole o conteudo gerado no Wizard (Copiar .env) e salve
  echo 3) Rode novamente run.bat
  echo.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$vals=@{}; Get-Content '.env' | ForEach-Object { if ($_ -match '^\s*#' -or $_ -notmatch '=') { continue }; $pair=$_.Split('=',2); $vals[$pair[0].Trim()]=$pair[1].Trim() };" ^
  "$store = $vals['STORE_ID']; $token = $vals['EDGE_TOKEN'];" ^
  "if ([string]::IsNullOrWhiteSpace($store) -or $store -match '<.*>') { Write-Host 'ERRO: STORE_ID invalido no .env. Copie novamente do Wizard.'; exit 10 };" ^
  "if ([string]::IsNullOrWhiteSpace($token) -or $token -match '<.*>') { Write-Host 'ERRO: EDGE_TOKEN invalido no .env. Copie novamente do Wizard.'; exit 11 };" ^
  "try { [guid]::Parse($store) | Out-Null } catch { Write-Host 'ERRO: STORE_ID deve ser UUID valido.'; exit 12 }"
if not "%errorlevel%"=="0" (
  echo.
  echo Corrija o .env e rode novamente.
  pause
  exit /b %errorlevel%
)

if not exist "logs" mkdir "logs"

echo Iniciando agente...
echo Logs: %CD%\logs\agent.log
echo Stdout/Stderr: %CD%\stdout.log
echo.

echo [%DATE% %TIME%] START run.bat > ".\stdout.log"
dalevision-edge-agent.exe >> ".\stdout.log" 2>&1
set "exit_code=%errorlevel%"
echo [%DATE% %TIME%] EXIT code=%exit_code% >> ".\stdout.log"

if not "%exit_code%"=="0" (
  echo ---
  echo ERRO: Agente encerrou com codigo %exit_code%.
  echo Confira stdout.log e logs\agent.log
  pause
  exit /b %exit_code%
)

echo ---
echo Agente encerrou normalmente.
echo Janela mantida aberta para diagnostico.
echo Se nao abrir ao dar duplo clique, rode manualmente: cmd /k run.bat
pause
