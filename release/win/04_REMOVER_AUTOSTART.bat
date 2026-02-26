@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

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

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%TARGET%\\scripts\\uninstall-service.ps1\" -TaskName \"DaleVisionEdgeAgent\""

net session >nul 2>&1
if %errorlevel%==0 (
  %PS_CMD%
  set "exit_code=%errorlevel%"
  if "%exit_code%"=="0" (
    echo.
    echo Autostart removido com sucesso (DaleVisionEdgeAgent).
  ) else (
    echo.
    echo ERRO: remocao falhou (codigo=%exit_code%).
  )
  echo.
  pause
  exit /b %exit_code%
)

echo Solicitando permissao de administrador...
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%TARGET%\\scripts\\uninstall-service.ps1\"\" -TaskName \"\"DaleVisionEdgeAgent\"\"' -Wait -PassThru; exit $p.ExitCode"
set "exit_code=%errorlevel%"

echo.
echo Se a janela de administrador abriu, aguarde ela finalizar.
echo.
pause

if not "%exit_code%"=="0" (
  echo.
  echo ERRO: remocao cancelada ou falhou (codigo=%exit_code%).
  echo.
  pause
  exit /b %exit_code%
)
echo.
echo Autostart removido com sucesso (DaleVisionEdgeAgent).
echo.
pause
exit /b %exit_code%
