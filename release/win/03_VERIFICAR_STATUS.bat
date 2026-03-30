@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "LOCAL_DV=%LOCALAPPDATA%\DaleVision"
set "LOG=%LOCAL_DV%\logs\agent.log"
set "RUNLOG=%LOCAL_DV%\logs\run_agent.log"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DaleVision Edge Agent.lnk"

echo ==========================================
echo DALE Vision Edge Agent - Verificar Status
echo ==========================================
echo.
if exist "%STARTUP%" (
  echo Startup shortcut: OK
) else (
  echo Startup shortcut: AUSENTE
)
echo.
tasklist /FI "IMAGENAME eq dalevision-edge-agent.exe" | find /I "dalevision-edge-agent.exe" >nul
if %errorlevel%==0 (
  echo Processo: RODANDO
) else (
  echo Processo: PARADO
)
echo.
if exist "%RUNLOG%" (
  echo Ultimas linhas de run_agent.log:
  powershell -NoProfile -Command "Get-Content -Path '%RUNLOG%' -Tail 20"
) else (
  echo run_agent.log nao encontrado em %RUNLOG%
)
echo.
if exist "%LOG%" (
  echo Ultimas linhas de agent.log:
  powershell -NoProfile -Command "Get-Content -Path '%LOG%' -Tail 30"
) else (
  echo agent.log nao encontrado em %LOG%
)
echo.
pause
exit /b 0
