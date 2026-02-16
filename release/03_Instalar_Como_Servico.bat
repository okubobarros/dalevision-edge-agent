@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ==========================================
echo 03 - Instalar como Servico (requer admin)
echo ==========================================
echo.
echo Este passo precisa de permissao de administrador.
echo.
powershell -ExecutionPolicy Bypass -File install-service.ps1
if not "%errorlevel%"=="0" (
  echo Falha ao instalar. Tente executar como Administrador.
  echo Para remover: schtasks /Delete /TN DaleVisionEdgeAgent /F
  pause
  exit /b 1
)
echo OK. O servico foi instalado.
pause
