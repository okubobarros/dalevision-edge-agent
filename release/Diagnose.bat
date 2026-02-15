@echo off
cd /d "%~dp0"
echo Rodando diagnostico...
dalevision-edge-agent.exe doctor --share
pause
