@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Iniciar
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Abra o README.txt e preencha o .env.
  pause
  exit /b 2
)

set "DASH_URL=https://app.dalevision.com/app/cameras?onboarding=true"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="DASHBOARD_URL" set "DASH_URL=%%B"
)

echo Agente iniciando.
echo Deixe esta janela aberta.
echo.

start "" "%DASH_URL%"
dalevision-edge-agent.exe
set "exit_code=%errorlevel%"

echo.
if not "%exit_code%"=="0" (
  echo O agente foi encerrado com erro.
  echo Rode Diagnose.bat e envie o ZIP para o suporte.
) else (
  echo O agente foi encerrado.
)
echo.
pause
exit /b %exit_code%
