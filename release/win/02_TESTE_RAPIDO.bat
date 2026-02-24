@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "EXE_NAME=dalevision-edge-agent.exe"
set "LOG_DIR=%CD%\logs"
set "LOG_FILE=%LOG_DIR%\agent.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

echo ==========================================
echo DALE Vision Edge Agent - Teste Rapido
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Edite o .env e preencha os dados da loja.
  echo.
  pause
  exit /b 2
)

set "STORE_ID="
set "EDGE_TOKEN="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="STORE_ID" set "STORE_ID=%%B"
  if /I "%%A"=="EDGE_TOKEN" set "EDGE_TOKEN=%%B"
)

if "%STORE_ID%"=="" (
  echo ERRO: STORE_ID vazio no .env.
  echo Preencha STORE_ID e tente novamente.
  echo.
  pause
  exit /b 2
)

if "%EDGE_TOKEN%"=="" (
  echo ERRO: EDGE_TOKEN vazio no .env.
  echo Preencha EDGE_TOKEN e tente novamente.
  echo.
  pause
  exit /b 2
)

if not exist "%EXE_NAME%" (
  echo ERRO: executavel nao encontrado: %EXE_NAME%
  echo Verifique se o ZIP foi extraido corretamente.
  echo.
  pause
  exit /b 2
)

echo Logs: %LOG_FILE%
echo.
echo Iniciando agente (janela aberta). Pressione CTRL+C para parar.
echo.

"%EXE_NAME%" >> "%LOG_FILE%" 2>&1
set "exit_code=%errorlevel%"

echo.
if not "%exit_code%"=="0" (
  echo O agente foi encerrado com erro (exit_code=%exit_code%).
  echo Rode Diagnose.bat e envie o ZIP para o suporte.
) else (
  echo O agente foi encerrado.
)
echo.
pause
exit /b %exit_code%
