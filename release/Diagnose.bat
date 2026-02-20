@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call "%~dp003_DIAGNOSTICO_E_SUPORTE.bat"
exit /b %errorlevel%
