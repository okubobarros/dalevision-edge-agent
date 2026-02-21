@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

call "%~dp004_DIAGNOSTICO.bat"
exit /b %errorlevel%
