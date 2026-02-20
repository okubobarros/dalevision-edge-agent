@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo Este script e avancado.
echo Use Start_DaleVision_Agent.bat para o fluxo principal.
echo.

call "%~dp099_MODO_TECNICO.bat"
exit /b %errorlevel%
