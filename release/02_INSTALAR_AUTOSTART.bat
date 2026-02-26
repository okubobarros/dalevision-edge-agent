@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ==========================================
echo DALE Vision Edge Agent - Instalar Autostart
echo ==========================================
echo.

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs" >nul 2>&1
set "LOG=%ROOT%\logs\service_install.log"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"
echo BAT_SHA256=>> "%LOG%"
certutil -hashfile "%~f0" SHA256 >> "%LOG%" 2>&1
set "PS1=%ROOT%\scripts\install-service.ps1"
echo PS1_PATH=%PS1%>> "%LOG%"
if exist "%PS1%" (
  echo PS1_EXISTS=true>> "%LOG%"
  echo PS1_SHA256=>> "%LOG%"
  certutil -hashfile "%PS1%" SHA256 >> "%LOG%" 2>&1
) else (
  echo PS1_EXISTS=false>> "%LOG%"
)

REM --- Elevation check ---
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Not admin - elevating self...>> "%LOG%"
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Start-Process -FilePath '%ComSpec%' -ArgumentList '/c """"%~f0""""' -Verb RunAs -WindowStyle Normal -Wait"
  exit /b
)

REM --- Ensure install location in ProgramData (SYSTEM can write) ---
set "TARGET_BASE=C:\ProgramData\DaleVision\EdgeAgent"
set "TARGET=%TARGET_BASE%\dalevision-edge-agent-windows"
if /I not "%ROOT%"=="%TARGET%" (
  echo Copying to %TARGET% ...>> "%LOG%"
  if not exist "%TARGET_BASE%" mkdir "%TARGET_BASE%" >nul 2>&1
  robocopy "%ROOT%" "%TARGET%" /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS >> "%LOG%" 2>&1
  echo Relaunching from %TARGET%>> "%LOG%"
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Start-Process -FilePath '%ComSpec%' -ArgumentList '/c """"%TARGET%\02_INSTALAR_AUTOSTART.bat""""' -Verb RunAs -WindowStyle Normal -Wait"
  exit /b
)

set "PS=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
echo Running as admin.>> "%LOG%"
echo PS=%PS%>> "%LOG%"
echo PS1=%PS1%>> "%LOG%"

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -InstallDir "%ROOT%" >> "%LOG%" 2>&1
set "EC=%errorlevel%"
echo EXIT_CODE=%EC%>> "%LOG%"
echo.>> "%LOG%"

echo Log: %LOG%
type "%LOG%"
echo.
pause
