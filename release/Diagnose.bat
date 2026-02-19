@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call "%~dp003 - Diagnóstico (gerar ZIP).bat"
exit /b %errorlevel%
