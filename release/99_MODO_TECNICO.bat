@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo MODO TECNICO
echo Use 01_INICIAR_DALEVISION.bat para o fluxo principal.
echo.

call "%~dp001 - Iniciar Agent.bat"
exit /b %errorlevel%
