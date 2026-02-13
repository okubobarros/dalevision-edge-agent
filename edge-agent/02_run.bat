@echo off
setlocal

cd /d %~dp0

set ROOT=%~dp0
set LOGS_DIR=%ROOT%logs
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Rotate task logs (copy + truncate) before redirect writes
powershell -NoProfile -Command ^
  "$logs='%LOGS_DIR%';" ^
  "function Rotate($name) { $log=Join-Path $logs $name; if (Test-Path $log) { $size=(Get-Item $log).Length; if ($size -gt 5MB) { $ts=Get-Date -Format 'yyyyMMdd-HHmmss'; $base=[IO.Path]::GetFileNameWithoutExtension($log); $arch=Join-Path $logs ($base + '.' + $ts + '.log'); Copy-Item $log $arch -Force; Clear-Content $log; } } }" ^
  "Rotate 'task.out.log'; Rotate 'task.err.log';" ^
  "foreach ($pat in @('task.out.*.log','task.err.*.log')) { $items=Get-ChildItem $logs -Filter $pat -ErrorAction SilentlyContinue | Sort-Object LastWriteTime; if ($items.Count -gt 10) { $items[0..($items.Count-11)] | Remove-Item -Force } }"

if exist "venv\Scripts\python.exe" (
  set PY=venv\Scripts\python.exe
) else if exist "..\venv\Scripts\python.exe" (
  set PY=..\venv\Scripts\python.exe
) else (
  set PY=python
)

echo [DALE Vision] Starting Edge Agent (run)...
set "MODE_ARGS="
set "HAS_HEARTBEAT_ONLY=0"
for %%A in (%*) do (
  if /I "%%~A"=="--heartbeat-only" set "HAS_HEARTBEAT_ONLY=1"
)
if "%HAS_HEARTBEAT_ONLY%"=="0" (
  set "MODE_ARGS=--heartbeat-only"
  echo [DALE Vision] Mode: heartbeat-only (default).
)

%PY% -m src.agent.main --config .\config\agent.yaml %MODE_ARGS% %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [DALE Vision] Agent stopped with exit code %EXIT_CODE%.
  echo Check logs\edge-agent.log and logs\task.err.log for details.
  pause
  endlocal
  exit /b %EXIT_CODE%
)

echo.
echo [DALE Vision] Agent exited normally.
pause

endlocal
