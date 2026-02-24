@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Verificar Status
echo ==========================================
echo.

PowerShell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify-service.ps1"
echo.
pause
exit /b %errorlevel%
