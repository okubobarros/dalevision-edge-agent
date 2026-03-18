@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "PD=C:\ProgramData\DaleVision\EdgeAgent\dalevision-edge-agent-windows"
set "TARGET=%ROOT%"
if exist "%PD%\scripts\stop-agent.ps1" set "TARGET=%PD%"

set "PS1=%TARGET%\scripts\stop-agent.ps1"
set "LOGDIR=%TARGET%\logs"
set "LOG=%LOGDIR%\stop_agent.log"

echo ================================================
echo DALE Vision Edge Agent - Parar e Liberar Pasta
echo ================================================
echo.

if not exist "%LOGDIR%" mkdir "%LOGDIR%" >nul 2>&1

if not exist "%PS1%" (
  echo ERRO: script nao encontrado: %PS1%
  echo.
  pause
  exit /b 2
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -InstallDir "%TARGET%" -TaskName "DaleVisionEdgeAgent" -StartupTaskName "DaleVisionEdgeAgentStartup" -UpdateTaskName "DaleVisionEdgeAgentUpdate"
set "EC=%errorlevel%"
if "%EC%"=="" set "EC=1"

echo.
if "%EC%"=="0" (
  echo Agente parado. Agora voce pode substituir/excluir a pasta com seguranca.
  echo Log: %LOG%
) else (
  echo Falha ao parar agente (codigo=%EC%).
  echo Tente "04_REMOVER_AUTOSTART.bat" para remocao completa.
  echo Log: %LOG%
)
echo.
pause
exit /b %EC%

