@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "TASK_NAME=DaleVisionEdgeAgent"
set "UPDATE_TASK_NAME=DaleVisionEdgeAgentUpdate"
set "LOGDIR=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows\logs"
set "LOG=%LOGDIR%\service_uninstall.log"

echo ==========================================
echo DALE Vision Edge Agent - Remover Autostart
echo ==========================================
echo.

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"

net session >nul 2>&1
if errorlevel 1 goto :elevate
goto :run

:elevate
echo Solicitando permissao de administrador...
echo Not admin - elevating self...>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs -WindowStyle Normal -Wait"
echo.
echo Log: %LOG%
pause
exit /b

:run
echo Running as admin.>> "%LOG%"
echo Removendo "%TASK_NAME%"...
schtasks /Delete /TN "%TASK_NAME%" /F >> "%LOG%" 2>&1
echo Removendo "%UPDATE_TASK_NAME%"...
schtasks /Delete /TN "%UPDATE_TASK_NAME%" /F >> "%LOG%" 2>&1

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if errorlevel 1 (
  echo TASK_STILL_EXISTS=false>> "%LOG%"
  echo.
  echo Autostart removido com sucesso (ou ja nao existia).
) else (
  echo TASK_STILL_EXISTS=true>> "%LOG%"
  echo.
  echo ERRO: tarefa "%TASK_NAME%" ainda existe.
)

echo.
echo Log: %LOG%
echo.
type "%LOG%"
echo.
pause
exit /b
