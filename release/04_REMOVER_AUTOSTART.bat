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
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%PS1%"" -TaskName ""DaleVisionEdgeAgent"" -UpdateTaskName ""DaleVisionEdgeAgentUpdate""'"
set "EC=%errorlevel%"
echo ELEVATED_EXIT_CODE=%EC%>> "%LOG%"

echo.
if "%EC%"=="0" (
  echo Remocao concluida.
) else (
  echo ERRO: remocao falhou ou foi cancelada (codigo=%EC%).
)
echo.
echo Log: %LOG%
pause
exit /b %EC%

