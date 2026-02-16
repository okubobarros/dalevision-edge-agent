@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo 1) Conectar (Teste rapido)
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
  set "DALE_LOG_DIR=%PROGRAMDATA%\DaleVision\logs"
)
set "DASH_URL=https://app.dalevision.com/app/cameras?onboarding=true"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="DASHBOARD_URL" set "DASH_URL=%%B"
)

dalevision-edge-agent.exe --once
set "exit_code=%errorlevel%"
echo.
if "%exit_code%"=="0" (
  echo ✅ Conectado. Volte ao site e clique em "Adicionar camera".
  start "" "%DASH_URL%"
) else (
  echo ❌ Falha no teste rapido. Consulte o README.txt.
)
echo.
pause
exit /b %exit_code%
