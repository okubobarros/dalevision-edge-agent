@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

set "PS=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
set "PS1=%ROOT%\scripts\internal\Start_DaleVision_Agent.ps1"
set "LOG=%ROOT%\logs\run_agent.log"
if not exist "%ROOT%logs" mkdir "%ROOT%logs" >nul 2>&1

echo RUN_AGENT_START>> "%LOG%"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
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

for /f "usebackq delims=" %%A in (`"%PS%" -NoProfile -Command ^
  "$root = '%ROOT%\\dalevision-edge-agent.exe'; " ^
  "$root = [IO.Path]::GetFullPath($root).ToLowerInvariant(); " ^
  "Get-Process -Name 'dalevision-edge-agent' -ErrorAction SilentlyContinue | Where-Object { " ^
  "  $_.Path -and ([IO.Path]::GetFullPath($_.Path).ToLowerInvariant() -eq $root) " ^
  "} | Select-Object -ExpandProperty Id"`) do (
  set "PID=%%A"
)
if defined PID (
  echo AGENT_ALREADY_RUNNING PID=%PID%>> "%LOG%"
  exit /b 0
)

"%PS%" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%PS1%" -InstallDir "%ROOT%" >> "%LOG%" 2>&1
set "EC=%errorlevel%"
echo EXIT_CODE=%EC%>> "%LOG%"
exit /b %EC%
