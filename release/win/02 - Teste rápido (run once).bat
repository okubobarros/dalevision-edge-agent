@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "EXE_NAME=DaleVision Edge Agent.exe"

echo ==========================================
echo Teste rapido (run once)
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Abra o README.txt e preencha o .env.
  echo.
  echo Resultado: FALHA
  echo Codigo de saida: 1
  exit /b 1
)

if not exist "%EXE_NAME%" (
  echo ERRO: executavel nao encontrado: %EXE_NAME%
  echo Verifique se o ZIP foi extraido corretamente.
  echo.
  echo Resultado: FALHA
  echo Codigo de saida: 1
  exit /b 1
)

echo Executando teste rapido. Aguarde...
"%EXE_NAME%" --once
set "raw_exit=%errorlevel%"

echo.
if "%raw_exit%"=="0" (
  echo Conexao OK. Agora rode "01 - Iniciar Agent.bat".
  echo Resultado: OK
  set "exit_code=0"
) else (
  echo Falha no teste de conexao.
  echo Rode "03 - Diagnostico (gerar ZIP).bat" e envie o ZIP para o suporte.
  echo Resultado: FALHA
  set "exit_code=1"
)

echo Codigo de saida: %exit_code%
exit /b %exit_code%
