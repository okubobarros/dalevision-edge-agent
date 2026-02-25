@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "EXE_NAME=dalevision-edge-agent.exe"
set "LOG_DIR=%CD%\logs"
set "LOG_FILE=%LOG_DIR%\agent.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

if not exist "%EXE_NAME%" (
  echo ERRO: executavel nao encontrado: %EXE_NAME%
  echo Verifique se o ZIP foi extraido corretamente.
  if /I "%DALE_RUN_MODE%"=="service" exit /b 2
  echo.
  pause
  exit /b 2
)

if /I "%DALE_RUN_MODE%"=="service" (
  "%EXE_NAME%" >> "%LOG_FILE%" 2>&1
  exit /b %errorlevel%
)

echo ==========================================
echo DALE Vision Edge Agent - Iniciar
echo ==========================================
echo.
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
