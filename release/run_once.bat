@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo Este script e avancado.
echo Use 02_TESTE_RAPIDO.bat para o fluxo principal.
echo.

call "%~dp002_TESTE_RAPIDO.bat"
exit /b %errorlevel%
