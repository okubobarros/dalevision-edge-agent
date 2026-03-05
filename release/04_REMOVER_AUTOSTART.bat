@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PD=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows"
set "TARGET=%ROOT%"
if exist "%PD%\scripts\uninstall-service.ps1" set "TARGET=%PD%"
set "TASK_NAME=DaleVisionEdgeAgent"
set "UPDATE_TASK_NAME=DaleVisionEdgeAgentUpdate"

echo ==========================================
echo DALE Vision Edge Agent - Remover Autostart
echo ==========================================
echo.

if not exist "%TARGET%\logs" mkdir "%TARGET%\logs" >nul 2>&1
set "LOG=%TARGET%\logs\service_uninstall.log"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo TARGET=%TARGET%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"

net session >nul 2>&1
if %errorlevel% neq 0 goto :elevate
goto :run_admin

:elevate
echo Solicitando permissao de administrador...
echo Not admin - elevating self...>> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs -ArgumentList '--elevated' -WindowStyle Normal -Wait"
set "EC=%errorlevel%"
echo ELEVATED_EXIT_CODE=%EC%>> "%LOG%"
echo.
if "%EC%"=="0" (
  echo Remocao concluida. Confira o log abaixo.
) else (
  echo ERRO: remocao cancelada ou falhou (codigo=%EC%).
)
echo.
echo Log: %LOG%
pause
exit /b %EC%

:run_admin
echo Running as admin.>> "%LOG%"
schtasks /Delete /TN "%TASK_NAME%" /F >> "%LOG%" 2>&1
set "DEL_MAIN=%errorlevel%"
echo DELETE_%TASK_NAME%_EXIT=%DEL_MAIN%>> "%LOG%"
schtasks /Delete /TN "%UPDATE_TASK_NAME%" /F >> "%LOG%" 2>&1
set "DEL_UPDATE=%errorlevel%"
echo DELETE_%UPDATE_TASK_NAME%_EXIT=%DEL_UPDATE%>> "%LOG%"

set "EC=0"
if "%DEL_MAIN%" NEQ "0" (
  schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
  if %errorlevel%==0 set "EC=1"
)
if "%DEL_UPDATE%" NEQ "0" (
  schtasks /Query /TN "%UPDATE_TASK_NAME%" >nul 2>&1
  if %errorlevel%==0 set "EC=1"
)
echo UNINSTALL_EXIT_CODE=%EC%>> "%LOG%"

schtasks /Query /TN "DaleVisionEdgeAgent" >nul 2>&1
if %errorlevel%==0 echo TASK_STILL_EXISTS=true>> "%LOG%"
if %errorlevel%==0 if "%EC%"=="0" set "EC=1"
if not %errorlevel%==0 echo TASK_STILL_EXISTS=false>> "%LOG%"

if "%EC%"=="0" (
  echo.
  echo Autostart removido com sucesso (DaleVisionEdgeAgent).
) else (
  echo.
  echo ERRO: remocao falhou (codigo=%EC%).
)

echo.
echo Log: %LOG%
echo.
type "%LOG%"
echo.
pause
exit /b %EC%
