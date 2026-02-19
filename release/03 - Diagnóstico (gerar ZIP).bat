@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "EXE_NAME=DaleVision Edge Agent.exe"
set "OUTPUT_DIR=%CD%\output"

echo ==========================================
echo Diagnostico para suporte (gera ZIP)
echo ==========================================
echo.

if not exist ".env" (
  echo ERRO: arquivo .env nao encontrado.
  echo Abra o README.txt e preencha o .env.
  exit /b 2
)

if not exist "%EXE_NAME%" (
  echo ERRO: executavel nao encontrado: %EXE_NAME%
  echo Verifique se o ZIP foi extraido corretamente.
  exit /b 2
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%" >nul 2>&1

set "DALE_LOG_DIR=%CD%\logs"
if not "%PROGRAMDATA%"=="" (
  set "DALE_LOG_DIR=%PROGRAMDATA%\DaleVision\logs"
  if not exist "%DALE_LOG_DIR%" mkdir "%DALE_LOG_DIR%" >nul 2>&1
  if errorlevel 1 (
    set "DALE_LOG_DIR=%CD%\logs"
  )
)
if not exist "%DALE_LOG_DIR%" mkdir "%DALE_LOG_DIR%" >nul 2>&1

set "STORE_ID="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="STORE_ID" set "STORE_ID=%%B"
)
if "%STORE_ID%"=="" set "STORE_ID=unknown"

for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "$s=$env:STORE_ID; if ([string]::IsNullOrWhiteSpace($s)) { $s='unknown' }; $invalid=[IO.Path]::GetInvalidFileNameChars(); foreach ($ch in $invalid) { $s=$s -replace [regex]::Escape($ch), '_' }; $s=$s -replace '\s+','_'; Write-Output $s"`) do set "STORE_ID_SAFE=%%S"
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd-HHmmss'"`) do set "TS=%%T"

set "ZIP_NAME=dalevision-diagnose-%STORE_ID_SAFE%-%TS%.zip"
set "ZIP_PATH=%OUTPUT_DIR%\%ZIP_NAME%"
set "INFO_FILE=%OUTPUT_DIR%\diagnostics.txt"

echo Rodando diagnostico...
"%EXE_NAME%" doctor --share
set "doctor_exit=%errorlevel%"

(
  echo DateTime: %DATE% %TIME%
  echo Computer: %COMPUTERNAME%
  echo User: %USERNAME%
  echo StoreId: %STORE_ID%
  echo LogDir: %DALE_LOG_DIR%
  echo DoctorExit: %doctor_exit%
) > "%INFO_FILE%"

powershell -NoProfile -Command "$logDir=$env:DALE_LOG_DIR; $out=$env:ZIP_PATH; $info=$env:INFO_FILE; if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }; $files=@(); $logFiles=Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue; if ($logFiles) { $files += $logFiles.FullName }; if (Test-Path $info) { $files += $info }; if (-not $files -or $files.Count -eq 0) { 'Sem logs encontrados.' | Set-Content -Path $info; $files=@($info) }; Compress-Archive -Path $files -DestinationPath $out -Force" >nul 2>&1

if not exist "%ZIP_PATH%" (
  echo ERRO: nao foi possivel gerar o ZIP de diagnostico.
  echo Tente novamente ou contate o suporte.
  exit /b 1
)

echo.
echo Diagnostico finalizado.
echo ZIP: %ZIP_NAME%
echo Local: %OUTPUT_DIR%
echo Envie este ZIP para o suporte.
echo.
pause
exit /b 0
