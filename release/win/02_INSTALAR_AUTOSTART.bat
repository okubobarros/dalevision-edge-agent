@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Instalar Autostart
echo ==========================================
echo.

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0scripts\\install-service.ps1\" -InstallDir \"%~dp0\""

net session >nul 2>&1
if %errorlevel%==0 (
  %PS_CMD%
  set "exit_code=%errorlevel%"
  echo.
  pause
  exit /b %exit_code%
)

echo Solicitando permissao de administrador...
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "$p = Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0scripts\\install-service.ps1\"\" -InstallDir \"\"%~dp0\"\"' -Wait -PassThru; exit $p.ExitCode"
set "exit_code=%errorlevel%"

if not "%exit_code%"=="0" (
  echo.
  echo ERRO: instalacao cancelada ou falhou (codigo=%exit_code%).
)
echo.
pause
exit /b %exit_code%
