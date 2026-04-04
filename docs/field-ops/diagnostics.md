# Diagnostics

- Logs: `logs/agent.log`, `logs/diagnostics.json`, `logs/diagnostics.txt`, `logs/update.log`.
- Comando rápido: `dalevision-edge-agent.exe doctor --share` (ou `python -m ... doctor`).
- Scan NVR: `dalevision-edge-agent.exe scan --mode nvr --range auto`.
- Conteúdo de diagnóstico: versão do agente, config sanitizada, estado de câmeras, heartbeat recente, erros.
- Política: nunca registrar segredos; orientar mensagens claras e curtas para leigo.
