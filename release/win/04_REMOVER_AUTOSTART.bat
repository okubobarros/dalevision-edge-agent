@echo off
setlocal EnableExtensions

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

if not exist "%PS1%" (
  echo ERRO: script nao encontrado: %PS1%
  echo ERRO: script nao encontrado: %PS1%>> "%LOG%"
  echo.
  echo Log: %LOG%
  pause
  exit /b 2
)

echo Solicitando permissao de administrador...
echo Elevating uninstall command...>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Start-Process -FilePath 'powershell.exe' -Verb RunAs -PassThru -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%PS1%"" -TaskName ""DaleVisionEdgeAgent"" -StartupTaskName ""DaleVisionEdgeAgentStartup"" -UpdateTaskName ""DaleVisionEdgeAgentUpdate""'; exit $p.ExitCode"
set "EC=%errorlevel%"
echo ELEVATED_EXIT_CODE=%EC%>> "%LOG%"

set "TASK_EXISTS=0"
schtasks /Query /TN "DaleVisionEdgeAgent" >nul 2>&1 && set "TASK_EXISTS=1"
echo TASK_EXISTS_AFTER_UNINSTALL=%TASK_EXISTS%>> "%LOG%"

echo.
if "%EC%"=="0" (
  if "%TASK_EXISTS%"=="0" (
    echo Remocao concluida.
  ) else (
    echo ERRO: script retornou sucesso, mas a task ainda existe.
    set "EC=3"
  )
) else (
  echo ERRO: remocao falhou ou foi cancelada (codigo=%EC%).
)
echo.
echo Log: %LOG%
pause
exit /b %EC%
