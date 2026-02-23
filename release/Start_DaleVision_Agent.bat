@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "EXE_NAME=dalevision-edge-agent.exe"
set "LOG_DIR=%CD%\logs"
set "LOG_FILE=%LOG_DIR%\agent.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Preencha o arquivo .env com os dados da loja.
  if not "%DALE_RUN_MODE%"=="service" (
    pause
  )
  exit /b 2
)

if not exist "%EXE_NAME%" (
  echo ERRO: executavel nao encontrado: %EXE_NAME%
  echo Verifique se o ZIP foi extraido corretamente.
  if not "%DALE_RUN_MODE%"=="service" (
    pause
  )
  exit /b 2
)

echo ==========================================
echo DALE Vision Edge Agent - Iniciar
echo ==========================================
if not "%DALE_RUN_MODE%"=="service" (
  echo Modo teste (manual).
)
echo Logs: %LOG_FILE%
echo.

:loop
echo [%DATE% %TIME%] Iniciando agente...>> "%LOG_FILE%"
"%EXE_NAME%" >> "%LOG_FILE%" 2>&1
set "exit_code=%errorlevel%"
echo [%DATE% %TIME%] Agente finalizou com exit_code=%exit_code%>> "%LOG_FILE%"

if "%exit_code%"=="0" (
  exit /b 0
)

echo Agente encerrou com erro (exit_code=%exit_code%). Reiniciando em 5s...
timeout /t 5 /nobreak >nul
goto :loop
