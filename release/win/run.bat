@echo off
setlocal
cd /d %~dp0

echo ===============================
echo DALE Vision Edge Agent (Windows)
echo ===============================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado nesta pasta.
  echo 1) Renomeie .env.example para .env
  echo 2) Abra .env e cole o conteudo gerado no Wizard (Copiar .env)
  echo 3) Rode novamente run.bat
  echo.
  pause
  exit /b 1
)

if not exist "logs" mkdir "logs"

echo Iniciando agente...
echo Logs: %CD%\logs\agent.log
echo Stdout/Stderr: %CD%\stdout.log
echo.

dalevision-edge-agent.exe > ".\stdout.log" 2>&1
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
  echo ---
  echo ERRO: Agente encerrou com codigo %exit_code%.
  echo Confira stdout.log e logs\agent.log
  pause
  exit /b %exit_code%
)

echo ---
echo Agente encerrou normalmente.
