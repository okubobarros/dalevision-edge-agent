@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Remover Servico
echo ==========================================
echo.

set "PS_CMD=PowerShell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0uninstall-service.ps1\" -TaskName \"DaleVisionEdgeAgent\""

net session >nul 2>&1
if %errorlevel%==0 (
  %PS_CMD%
  echo.
  pause
  exit /b %errorlevel%
)

echo Solicitando permissao de administrador...
PowerShell -NoProfile -Command "Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0uninstall-service.ps1\"\" -TaskName \"\"DaleVisionEdgeAgent\"\"'"
echo.
echo Se a janela do UAC foi cancelada, tente novamente.
pause
exit /b 0
