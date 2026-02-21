@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo Este script e avancado.
echo Use 03_INICIAR.bat para o fluxo principal.
echo.

call "%~dp003_INICIAR.bat"
exit /b %errorlevel%
