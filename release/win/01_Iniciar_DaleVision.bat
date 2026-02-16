@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo 01 - Iniciar DALE Vision
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Abra o README.txt e preencha o .env.
  pause
  exit /b 2
)

set "DALE_LOG_DIR=%CD%\logs"
if not "%PROGRAMDATA%"=="" (
  set "DALE_LOG_DIR=%PROGRAMDATA%\DaleVision\EdgeAgent\logs"
)
set "DASH_URL=https://app.dalevision.com/app/cameras?onboarding=true"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="DASHBOARD_URL" set "DASH_URL=%%B"
)

echo Agente rodando. Pode minimizar. Nao feche esta janela.
echo.
dalevision-edge-agent.exe
start "" "%DASH_URL%"

echo.
echo O agente foi encerrado. Se isso foi um erro, execute novamente.
pause
