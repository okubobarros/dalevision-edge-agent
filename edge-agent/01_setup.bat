@echo off
setlocal

cd /d %~dp0

set RUN_SETUP=0
if /I "%1"=="--run" set RUN_SETUP=1

REM Cria venv local se não existir
if not exist "venv\Scripts\python.exe" (
  echo [DALE Vision] Creating venv...
  python -m venv venv
)

set PY=venv\Scripts\python.exe

echo [DALE Vision] Installing minimal PILOT deps...
%PY% -m pip install --upgrade pip
%PY% -m pip install fastapi uvicorn requests python-dotenv pyyaml

if /I "%INSTALL_MULTIPART%"=="1" (
  %PY% -m pip install python-multipart
)

if "%RUN_SETUP%"=="1" (
  echo [DALE Vision] Starting Edge Setup on http://localhost:7860 ...
  start "" http://localhost:7860
  %PY% -m src.agent setup
) else (
  echo [DALE Vision] Setup OK. To run the setup UI: 01_setup.bat --run
)

endlocal
