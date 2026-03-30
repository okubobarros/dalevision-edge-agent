@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "LOCAL_DV=%LOCALAPPDATA%\DaleVision"
set "ROAM_DV=%APPDATA%\DaleVision"
set "DALE_APP_DIR=%LOCAL_DV%\app"
set "DALE_CONFIG_DIR=%ROAM_DV%"
set "DALE_LOG_DIR=%LOCAL_DV%\logs"
set "DALE_CACHE_DIR=%LOCAL_DV%\cache"
set "DALE_ENV_PATH=%DALE_CONFIG_DIR%\.env"
set "DALE_AGENT_CONFIG_PATH=%DALE_CONFIG_DIR%\agent_config.json"

if not exist "%DALE_APP_DIR%" mkdir "%DALE_APP_DIR%" >nul 2>&1
if not exist "%DALE_CONFIG_DIR%" mkdir "%DALE_CONFIG_DIR%" >nul 2>&1
if not exist "%DALE_LOG_DIR%" mkdir "%DALE_LOG_DIR%" >nul 2>&1
if not exist "%DALE_CACHE_DIR%" mkdir "%DALE_CACHE_DIR%" >nul 2>&1

cd /d "%ROOT%"

set "PS=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PS1=%ROOT%\scripts\internal\Start_DaleVision_Agent.ps1"
set "LOG=%DALE_LOG_DIR%\run_agent.log"

echo RUN_AGENT_START>> "%LOG%"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo DALE_APP_DIR=%DALE_APP_DIR%>> "%LOG%"
echo DALE_CONFIG_DIR=%DALE_CONFIG_DIR%>> "%LOG%"
echo DALE_LOG_DIR=%DALE_LOG_DIR%>> "%LOG%"
echo DALE_CACHE_DIR=%DALE_CACHE_DIR%>> "%LOG%"
echo DALE_ENV_PATH=%DALE_ENV_PATH%>> "%LOG%"
echo PS=%PS%>> "%LOG%"
echo PS1=%PS1%>> "%LOG%"
if not exist "%PS%" (
  echo PS_MISSING>> "%LOG%"
  exit /b 2
)
if not exist "%PS1%" (
  echo PS1_MISSING>> "%LOG%"
  exit /b 3
)

"%PS%" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%PS1%" -InstallDir "%ROOT%" -ConfigDir "%DALE_CONFIG_DIR%" -LogDir "%DALE_LOG_DIR%" -CacheDir "%DALE_CACHE_DIR%" >> "%LOG%" 2>&1
set "EC=%errorlevel%"
echo EXIT_CODE=%EC%>> "%LOG%"
exit /b %EC%
