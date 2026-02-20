@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call "%~dp002 - Teste rápido (run once).bat"
exit /b %errorlevel%
