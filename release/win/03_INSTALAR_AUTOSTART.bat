@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Instalar Autostart
echo ==========================================
echo.

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0install-service.ps1\" -InstallDir \"%~dp0\""

net session >nul 2>&1
if %errorlevel%==0 (
  %PS_CMD%
  echo.
  pause
  exit /b %errorlevel%
)

echo Solicitando permissao de administrador...
PowerShell -NoProfile -Command "Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0install-service.ps1\"\" -InstallDir \"\"%~dp0\"\"'"
echo.
echo Se a janela do UAC foi cancelada, tente novamente.
pause
exit /b 0
