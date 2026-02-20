@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo Este script e avancado.
echo Use Start_DaleVision_Agent.bat para o fluxo principal.
echo.

call "%~dp002_TESTE_RAPIDO.bat"
exit /b %errorlevel%
