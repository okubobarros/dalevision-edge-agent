@echo off
setlocal EnableExtensions

set "SELF=%~f0"
set "ELEVATED_FLAG=%~1"

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PD=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows"
set "TARGET=%ROOT%"
if exist "%PD%\scripts\uninstall-service.ps1" set "TARGET=%PD%"

set "PS1=%TARGET%\scripts\uninstall-service.ps1"
set "LOGDIR=%TARGET%\logs"
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
echo ELEVATED_FLAG=%ELEVATED_FLAG%>> "%LOG%"

if not exist "%PS1%" goto :missing_ps1
if /I "%ELEVATED_FLAG%"=="--elevated" goto :run_uninstall

echo Solicitando permissao de administrador...
echo ELEVATE_STEP=start>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%SELF%' -Verb RunAs -Wait -ArgumentList '--elevated'"
set "EC=%errorlevel%"
echo ELEVATE_STEP=return code=%EC%>> "%LOG%"
if not "%EC%"=="0" goto :elevate_fail
exit /b 0

:run_uninstall
echo ELEVATE_STEP=already-elevated>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -TaskName "DaleVisionEdgeAgent" -StartupTaskName "DaleVisionEdgeAgentStartup" -UpdateTaskName "DaleVisionEdgeAgentUpdate"
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

:elevate_fail
echo ERRO: elevacao cancelada ou falhou (codigo=%EC%).
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
