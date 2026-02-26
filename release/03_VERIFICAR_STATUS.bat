@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Verificar Status
echo ==========================================
echo.

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Este comando precisa de permissao de administrador.
  echo Abrindo com UAC...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Start-Process -FilePath '%ComSpec%' -ArgumentList '/c """"%~f0""""' -Verb RunAs -WindowStyle Normal -Wait"
  exit /b
)

PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\\verify-service.ps1"
echo.
pause
exit /b %errorlevel%
