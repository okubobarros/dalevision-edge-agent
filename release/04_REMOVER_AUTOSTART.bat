@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Remover Autostart
echo ==========================================
echo.

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0scripts\\uninstall-service.ps1\" -TaskName \"DaleVisionEdgeAgent\""

net session >nul 2>&1
if %errorlevel%==0 (
  %PS_CMD%
  set "exit_code=%errorlevel%"
  echo.
  pause
  exit /b %exit_code%
)

echo Solicitando permissao de administrador...
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0scripts\\uninstall-service.ps1\"\" -TaskName \"\"DaleVisionEdgeAgent\"\"' -Wait -PassThru; exit $p.ExitCode"
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
  echo.
  echo ERRO: remocao cancelada ou falhou (codigo=%exit_code%).
)
echo.
pause
exit /b %exit_code%
