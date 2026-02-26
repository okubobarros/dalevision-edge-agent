@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PD=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows"
if exist "%PD%\scripts\verify-service.ps1" (
  set "TARGET=%PD%"
) else (
  set "TARGET=%ROOT%"
)

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

cd /d "%TARGET%"
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%TARGET%\\scripts\\verify-service.ps1"
echo.
pause
exit /b %errorlevel%
