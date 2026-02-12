@echo off
setlocal
cd /d %~dp0

echo ===============================
echo DALE Vision Edge Agent (Windows)
echo ===============================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado nesta pasta.
  echo - Cole o .env gerado no Wizard aqui, ao lado deste run.bat
  echo - Exemplo: renomeie .env.example para .env e preencha
  pause
  exit /b 1
)

set "EDGE_TOKEN="
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R /C:"^EDGE_TOKEN=" ".env"`) do (
  if /I "%%A"=="EDGE_TOKEN" set "EDGE_TOKEN=%%B"
)

if not defined EDGE_TOKEN (
  echo ERRO: EDGE_TOKEN nao encontrado no .env.
  echo - Refaça o .env copiando do Wizard.
  pause
  exit /b 1
)

if "%EDGE_TOKEN%"=="" (
  echo ERRO: EDGE_TOKEN vazio no .env.
  echo - Refaça o .env copiando do Wizard.
  pause
  exit /b 1
)

if not exist "logs" mkdir "logs"

echo Iniciando agente...
echo Logs: %CD%\logs\agent.log
echo Stdout/Stderr: %CD%\logs\stdout.log
echo.

dalevision-edge-agent.exe > "logs\stdout.log" 2>&1
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
  echo ---
  echo ERRO: Agente encerrou com codigo %exit_code%.
  echo Confira logs\stdout.log e logs\agent.log
  pause
  exit /b %exit_code%
)

echo ---
echo Agente encerrou normalmente.
