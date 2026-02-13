@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "logs" mkdir "logs" >nul 2>&1
set "LOG_FILE=logs\stdout.log"
echo [%DATE% %TIME%] START run_once.bat > "%LOG_FILE%"

dalevision-edge-agent.exe --once >> "%LOG_FILE%" 2>&1
set "exit_code=%errorlevel%"
echo [%DATE% %TIME%] EXIT code=%exit_code% >> "%LOG_FILE%"

echo.
echo Exit code: %exit_code%
echo Pressione uma tecla para fechar...
pause >nul
exit /b %exit_code%
