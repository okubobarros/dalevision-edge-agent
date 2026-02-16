@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==========================================
echo Diagnostico para suporte
echo ==========================================
echo.
set "DALE_LOG_DIR=%CD%\logs"
if not "%PROGRAMDATA%"=="" (
  set "DALE_LOG_DIR=%PROGRAMDATA%\DaleVision\logs"
)
set "DASH_URL=https://app.dalevision.com/app/cameras?onboarding=true"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="DASHBOARD_URL" set "DASH_URL=%%B"
)
echo Rodando diagnostico...
dalevision-edge-agent.exe doctor --share
for /f "delims=" %%Z in ('dir /b /o-d "%DALE_LOG_DIR%\diagnostics-share-*.zip" 2^>nul') do (
  set "LAST_ZIP=%%Z"
  goto foundzip
)
:foundzip
if not "%LAST_ZIP%"=="" (
  if not "%USERPROFILE%"=="" (
    copy "%DALE_LOG_DIR%\%LAST_ZIP%" "%USERPROFILE%\Desktop\%LAST_ZIP%" >nul 2>&1
  )
)
echo.
echo Diagnostico finalizado. O ZIP esta na pasta de logs (e na Area de Trabalho).
start "" "%DASH_URL%"
echo.
pause
