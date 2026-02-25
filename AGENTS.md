# DALE Vision Edge Agent - Local Instructions

## Principles
- Nao quebrar compatibilidade do protocolo atual (heartbeat e camera health).
- Diagnostico primeiro: mensagens claras, codigos curtos e orientacao para leigo.
- Logs legiveis e uteis para suporte remoto.
- Nunca logar senha ou segredos.

## Como rodar localmente
1. Preencha `.env` com `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID`.
2. Rodar agente:
   - `python -m dalevision_edge_agent.main`
3. Diagnosticos:
   - `python -m dalevision_edge_agent.main doctor --nvr-ip <IP_DO_NVR> --share`

## Como empacotar (zip release)
1. Gere o executavel (PyInstaller ou pipeline existente).
2. Rode o script:
   - `.\scripts\release_windows.ps1 -Version vX.Y.Z`
3. O ZIP final fica em `dalevision-edge-agent-windows.zip`.
4. O bundle inclui `Start_DaleVision_Agent.bat/.ps1` e tasks de autostart/update
   geradas via `install-service.ps1`.

## Logs e diagnostico
- `logs/agent.log` para logs do agente.
- `logs/diagnostics.json` e `logs/diagnostics.txt` para envio via WhatsApp.
- `logs/update.log` para auto-update (quando habilitado).

## Snapshot
- OpenCV e opcional.
- Se OpenCV nao existir, tenta ffmpeg no PATH.
- Se ambos falharem, loga mensagem clara e segue sem snapshot.

## Pull Requests
- Todo PR deve citar ao menos uma spec (ex.: `SPEC-002`).
- Se for bugfix, deve citar tambem um `BUG-*`.
