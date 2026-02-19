@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo Testar conexao (1 a 3 heartbeats)
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Abra o README.txt e preencha o .env.
  echo.
  echo Resultado: FALHA
  echo Codigo de saida: 1
  pause
  exit /b 1
)

echo Executando teste rapido. Aguarde...
dalevision-edge-agent.exe --once
set "raw_exit=%errorlevel%"

echo.
if "%raw_exit%"=="0" (
  echo Conexao OK. Agora rode Start_DaleVision_Agent.bat.
  echo Resultado: OK
  set "exit_code=0"
) else (
  echo Falha no teste de conexao.
  echo Rode Diagnose.bat e envie o ZIP para o suporte.
  echo Resultado: FALHA
  set "exit_code=1"
)

echo Codigo de saida: %exit_code%
echo.
pause
exit /b %exit_code%
