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
%PY% -m src.agent.main --config .\config\agent.yaml %*

endlocal
