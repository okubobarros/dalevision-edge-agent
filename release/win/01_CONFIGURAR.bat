@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo DALE Vision Edge Agent - Configurar
echo ==========================================
echo.

if not exist ".env" (
  if exist ".env.example" (
    copy ".env.example" ".env" >nul
  )
)

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Verifique se o ZIP foi extraido corretamente.
  pause
  exit /b 2
)

echo Abrindo .env para edicao...
start "" notepad ".env"
echo.
echo Quando terminar, salve o arquivo e pressione Enter para validar.
pause >nul

set "CLOUD_BASE_URL="
set "STORE_ID="
set "EDGE_TOKEN="
set "AGENT_ID="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="CLOUD_BASE_URL" set "CLOUD_BASE_URL=%%B"
  if /I "%%A"=="STORE_ID" set "STORE_ID=%%B"
  if /I "%%A"=="EDGE_TOKEN" set "EDGE_TOKEN=%%B"
  if /I "%%A"=="AGENT_ID" set "AGENT_ID=%%B"
)

set "MISSING="
if "%CLOUD_BASE_URL%"=="" set "MISSING=%MISSING% CLOUD_BASE_URL"
if "%STORE_ID%"=="" set "MISSING=%MISSING% STORE_ID"
if "%EDGE_TOKEN%"=="" set "MISSING=%MISSING% EDGE_TOKEN"

if not "%MISSING%"=="" (
  echo ERRO: campos obrigatorios faltando:%MISSING%
  echo Preencha o .env e rode novamente.
  pause
  exit /b 1
)

if "%AGENT_ID%"=="" (
  echo AVISO: AGENT_ID nao definido. O suporte pode solicitar este campo.
)

echo.
echo OK: configuracao basica pronta.
echo Proximo passo: 02_TESTE_RAPIDO.bat
echo.
pause
exit /b 0
