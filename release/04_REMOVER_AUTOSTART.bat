@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

if not exist "%PS1%" (
  echo ERRO: script nao encontrado: %PS1%
  echo ERRO: script nao encontrado: %PS1%>> "%LOG%"
  echo.
  echo Log: %LOG%
  pause
  exit /b 2
)

if /I not "%ELEVATED_FLAG%"=="--elevated" (
  echo Solicitando permissao de administrador...
  echo ELEVATE_STEP=start>> "%LOG%"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%ComSpec%' -Verb RunAs -Wait -ArgumentList '/c ""%SELF%"" --elevated'"
  set "EC=%errorlevel%"
  echo ELEVATE_STEP=return code=!EC!>> "%LOG%"
  if not "!EC!"=="0" (
    echo ERRO: elevacao cancelada ou falhou (codigo=!EC!).
    echo.
    echo Log: %LOG%
    pause
    exit /b !EC!
  )
  exit /b 0
)

echo ELEVATE_STEP=already-elevated>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -TaskName "DaleVisionEdgeAgent" -StartupTaskName "DaleVisionEdgeAgentStartup" -UpdateTaskName "DaleVisionEdgeAgentUpdate"
set "EC=%errorlevel%"
echo UNINSTALL_PS1_EXIT_CODE=%EC%>> "%LOG%"

set "TASK_EXISTS=0"
schtasks /Query /TN "DaleVisionEdgeAgent" >nul 2>&1 && set "TASK_EXISTS=1"
set "TASK_STARTUP_EXISTS=0"
schtasks /Query /TN "DaleVisionEdgeAgentStartup" >nul 2>&1 && set "TASK_STARTUP_EXISTS=1"
set "TASK_UPDATE_EXISTS=0"
schtasks /Query /TN "DaleVisionEdgeAgentUpdate" >nul 2>&1 && set "TASK_UPDATE_EXISTS=1"
echo TASK_EXISTS_AFTER_UNINSTALL=%TASK_EXISTS%>> "%LOG%"
echo TASK_STARTUP_EXISTS_AFTER_UNINSTALL=%TASK_STARTUP_EXISTS%>> "%LOG%"
echo TASK_UPDATE_EXISTS_AFTER_UNINSTALL=%TASK_UPDATE_EXISTS%>> "%LOG%"

echo.
if "%EC%"=="0" (
  if "%TASK_EXISTS%"=="0" if "%TASK_STARTUP_EXISTS%"=="0" if "%TASK_UPDATE_EXISTS%"=="0" (
    echo Remocao concluida.
  ) else (
    echo ERRO: script retornou sucesso, mas ao menos uma task ainda existe.
    set "EC=3"
  )
) else (
  echo ERRO: remocao falhou ou foi cancelada (codigo=%EC%).
)
echo.
echo Log: %LOG%
pause
exit /b %EC%
