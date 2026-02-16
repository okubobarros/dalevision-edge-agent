@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==========================================
echo 02 - Testar Conexao (Diagnostico)
echo ==========================================
echo.
set "DALE_LOG_DIR=%CD%\logs"
if not "%PROGRAMDATA%"=="" (
  set "DALE_LOG_DIR=%PROGRAMDATA%\DaleVision\EdgeAgent\logs"
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
echo Agora vamos buscar NVRs na rede...
dalevision-edge-agent.exe scan --mode nvr --range auto
echo.
echo Se voce souber o IP do NVR, pode testar RTSP agora.
set /p NVR_IP="IP do NVR (ou ENTER para pular): "
if "%NVR_IP%"=="" goto end
set /p NVR_USER="Usuario do NVR: "
set /p NVR_PASS="Senha do NVR: "
echo.
dalevision-edge-agent.exe test-rtsp --ip %NVR_IP% --user %NVR_USER% --pass %NVR_PASS% --scan-channels
:end
echo.
echo Diagnostico finalizado. O ZIP esta na pasta de logs.
start "" "%DASH_URL%"
echo.
pause
