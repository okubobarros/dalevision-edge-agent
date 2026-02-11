@echo off
setlocal
cd /d %~dp0

echo ===============================
echo DALE Vision Edge Agent (Windows)
echo ===============================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado nesta pasta.
  echo - Cole o .env gerado no Wizard aqui, ao lado deste run.bat
  echo - Exemplo: renomeie .env.example para .env e preencha
  echo.
  pause
  exit /b 1
)

echo Iniciando agente...
echo (Se der erro, copie o log do terminal e envie ao suporte)
echo.

dalevision-edge-agent.exe

echo.
echo O agente encerrou. Pressione qualquer tecla para fechar.
pause >nul
