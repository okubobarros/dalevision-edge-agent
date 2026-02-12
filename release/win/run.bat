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
echo Logs: %CD%\logs\agent.log
echo (Se der erro, veja stdout.log)

dalevision-edge-agent.exe > stdout.log 2>&1

echo ---
echo Agente finalizou. Abra stdout.log e logs\agent.log
pause
