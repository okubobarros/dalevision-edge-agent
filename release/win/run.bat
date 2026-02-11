@echo off
setlocal
cd /d %~dp0

echo ===============================
echo DALE Vision Edge Agent (Windows)
echo ===============================

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado nesta pasta.
  echo - Cole o .env gerado no Wizard aqui, ao lado deste run.bat
  echo - Exemplo: renomeie .env.example para .env e preencha
  pause
  exit /b 1
)

echo Iniciando agente...
echo (Se der erro, envie o arquivo agent.log)
dalevision-edge-agent.exe > agent.log 2>&1

echo ---
echo Agente finalizou. Veja agent.log
pause
