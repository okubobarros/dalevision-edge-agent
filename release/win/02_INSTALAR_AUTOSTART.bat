@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

echo ==========================================
echo DALE Vision Edge Agent - Instalar Autostart
echo ==========================================
echo.
echo Aguarde... preparando instalacao.
echo.

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs" >nul 2>&1
set "LOG=%ROOT%\logs\service_install.log"
echo ==== %date% %time% ====>> "%LOG%"
echo ROOT=%ROOT%>> "%LOG%"
echo BAT_PATH=%~f0>> "%LOG%"
echo BAT_SHA256=>> "%LOG%"
echo Calculando hash do instalador...
certutil -hashfile "%~f0" SHA256 >> "%LOG%" 2>&1
set "PS1=%ROOT%\scripts\install-service.ps1"
echo PS1_PATH=%PS1%>> "%LOG%"
if exist "%PS1%" (
  echo PS1_EXISTS=true>> "%LOG%"
  echo PS1_SHA256=>> "%LOG%"
  echo Calculando hash do script de instalacao...
  certutil -hashfile "%PS1%" SHA256 >> "%LOG%" 2>&1
) else (
  echo PS1_EXISTS=false>> "%LOG%"
)

set "PS=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
echo Installing autostart for current user (ONLOGON).>> "%LOG%"
echo PS=%PS%>> "%LOG%"
echo PS1=%PS1%>> "%LOG%"
echo Iniciando instalacao do autostart...

"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -InstallDir "%ROOT%" >> "%LOG%" 2>&1
set "EC=%errorlevel%"
echo EXIT_CODE=%EC%>> "%LOG%"
echo.>> "%LOG%"

echo Log: %LOG%
type "%LOG%"
echo.
if "%EC%"=="0" (
  echo OK: Autostart instalado.
) else (
  echo ERRO: Autostart falhou. Veja o log acima.
)
pause
