@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================
echo Diagnostico para suporte
echo ==========================================
echo.

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
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="STORE_ID" set "STORE_ID=%%B"
  )
) else (
  echo AVISO: .env nao encontrado. Usando STORE_ID=unknown.
)

for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "$s=$env:STORE_ID; if ([string]::IsNullOrWhiteSpace($s)) { $s='unknown' }; $invalid=[IO.Path]::GetInvalidFileNameChars(); foreach ($ch in $invalid) { $s=$s -replace [regex]::Escape($ch), '_' }; $s=$s -replace '\s+','_'; Write-Output $s"`) do set "STORE_ID_SAFE=%%S"
for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd-HHmmss'"`) do set "TS=%%T"

set "ZIP_NAME=dalevision-diagnose-%STORE_ID_SAFE%-%TS%.zip"
set "ZIP_PATH=%DALE_LOG_DIR%\%ZIP_NAME%"

echo Rodando diagnostico...
dalevision-edge-agent.exe doctor --share
set "doctor_exit=%errorlevel%"

set "LAST_ZIP="
for /f "delims=" %%Z in ('dir /b /o-d "%DALE_LOG_DIR%\diagnostics-share-*.zip" 2^>nul') do (
  set "LAST_ZIP=%%Z"
  goto foundzip
)
:foundzip

if not "%LAST_ZIP%"=="" (
  copy "%DALE_LOG_DIR%\%LAST_ZIP%" "%ZIP_PATH%" >nul 2>&1
) else (
  echo Nao foi encontrado ZIP automatico. Gerando ZIP manual...
  powershell -NoProfile -Command "$src=$env:DALE_LOG_DIR; $dst=$env:ZIP_PATH; if (!(Test-Path $src)) { New-Item -ItemType Directory -Path $src | Out-Null }; $files=Get-ChildItem -Path $src -File -ErrorAction SilentlyContinue; if (!$files -or $files.Count -eq 0) { 'Sem logs encontrados.' | Set-Content -Path (Join-Path $src 'diagnostics.txt'); $files=Get-ChildItem -Path $src -File -ErrorAction SilentlyContinue }; if ($files -and $files.Count -gt 0) { Compress-Archive -Path $files.FullName -DestinationPath $dst -Force }" >nul 2>&1
)

if not exist "%ZIP_PATH%" (
  echo ERRO: nao foi possivel gerar o ZIP de diagnostico.
  echo Tente novamente ou contate o suporte.
  pause
  exit /b 1
)

if not "%USERPROFILE%"=="" (
  copy "%ZIP_PATH%" "%USERPROFILE%\Desktop\%ZIP_NAME%" >nul 2>&1
)

echo.
echo Diagnostico finalizado.
echo ZIP: %ZIP_NAME%
echo Local: %DALE_LOG_DIR%
echo Envie este ZIP para o suporte.
echo.
pause
exit /b 0
