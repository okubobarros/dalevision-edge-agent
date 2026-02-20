@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call "%~dp001 - Iniciar Agent.bat"
exit /b %errorlevel%
