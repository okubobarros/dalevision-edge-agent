@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "ARG1=%~1"

set "PD=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows"
if exist "%PD%\scripts\uninstall-service.ps1" (
  set "TARGET=%PD%"
) else (
  set "TARGET=%ROOT%"
)

echo ==========================================
echo DALE Vision Edge Agent - Remover Autostart
echo ==========================================
echo.

if not exist "%TARGET%\logs" mkdir "%TARGET%\logs" >nul 2>&1
set "LOG=%TARGET%\logs\service_uninstall.log"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo TARGET=%TARGET%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"
echo ARG1=%ARG1%>> "%LOG%"

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%TARGET%\scripts\uninstall-service.ps1\" -TaskName \"DaleVisionEdgeAgent\""

if not exist "%TARGET%\scripts\uninstall-service.ps1" (
  echo ERRO: script nao encontrado: %TARGET%\scripts\uninstall-service.ps1
  echo ERRO: script nao encontrado: %TARGET%\scripts\uninstall-service.ps1>> "%LOG%"
  echo.
  echo Log: %LOG%
  pause
  exit /b 2
)

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Solicitando permissao de administrador...
  echo Not admin - elevating self...>> "%LOG%"
  PowerShell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$p = Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList '--elevated' -WindowStyle Normal -Wait -PassThru; exit $p.ExitCode"
  set "exit_code=%errorlevel%"
  echo ELEVATED_EXIT_CODE=%exit_code%>> "%LOG%"
  echo.
  if "%exit_code%"=="0" (
    echo Remocao concluida. Confira o log abaixo.
  ) else (
    echo ERRO: remocao cancelada ou falhou (codigo=%exit_code%).
  )
  echo.
  echo Log: %LOG%
  pause
  exit /b %exit_code%
)

echo Running as admin.>> "%LOG%"
%PS_CMD% >> "%LOG%" 2>&1
set "exit_code=%errorlevel%"
echo UNINSTALL_EXIT_CODE=%exit_code%>> "%LOG%"

schtasks /Query /TN "DaleVisionEdgeAgent" >nul 2>&1
if %errorlevel%==0 (
  echo TASK_STILL_EXISTS=true>> "%LOG%"
  if "%exit_code%"=="0" set "exit_code=1"
) else (
  echo TASK_STILL_EXISTS=false>> "%LOG%"
)

if "%exit_code%"=="0" (
  echo.
  echo Autostart removido com sucesso (DaleVisionEdgeAgent).
) else (
  echo.
  echo ERRO: remocao falhou (codigo=%exit_code%).
)

echo.
echo Log: %LOG%
echo.
type "%LOG%"
echo.
pause
exit /b %exit_code%
