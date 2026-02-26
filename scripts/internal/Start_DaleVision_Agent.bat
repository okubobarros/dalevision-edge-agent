@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0\\..\\.."

PowerShell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0Start_DaleVision_Agent.ps1" -InstallDir "%CD%"
exit /b %errorlevel%
