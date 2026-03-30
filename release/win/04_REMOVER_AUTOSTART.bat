@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "LOCAL_DV=%LOCALAPPDATA%\DaleVision"
set "TARGET=%ROOT%"
set "PS1=%TARGET%\scripts\uninstall-user.ps1"
set "LOGDIR=%LOCAL_DV%\logs"
set "LOG=%LOGDIR%\service_uninstall.log"

echo ==========================================
echo DALE Vision Edge Agent - Remover Autostart
echo ==========================================
echo.

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo TARGET=%TARGET%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"

if not exist "%PS1%" goto :missing_ps1

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
set "EC=%errorlevel%"
if "%EC%"=="" set "EC=1"
echo UNINSTALL_PS1_EXIT_CODE=%EC%>> "%LOG%"
if not "%EC%"=="0" goto :uninstall_fail

echo.
echo Remocao concluida.
echo.
echo Log: %LOG%
pause
exit /b 0

:uninstall_fail
echo.
echo ERRO: remocao falhou ou foi cancelada (codigo=%EC%).
echo.
echo Log: %LOG%
pause
exit /b %EC%

:missing_ps1
echo ERRO: script nao encontrado: %PS1%
echo ERRO: script nao encontrado: %PS1%>> "%LOG%"
echo.
echo Log: %LOG%
pause
exit /b 2
