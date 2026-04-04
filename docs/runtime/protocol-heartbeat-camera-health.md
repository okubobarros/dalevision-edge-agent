# Protocol — Heartbeat & Camera Health

Objetivo: sinalizar liveness do edge e saúde das câmeras sem enviar stream completo.

Heartbeat
- Envia para cloud no intervalo configurado; inclui `store_id`, `agent_id`, versão do agente, timestamp.
- SLA: sem gaps maiores que o intervalo configurado + tolerância.
- Status possíveis: `online`, `degraded`, `offline` (interpretado pelo backend).

Camera Health
- Consulta local das câmeras; resultado agregado no payload de heartbeat ou endpoint dedicado (conforme versão).
- Campos típicos: `camera_id`, `status`, `last_frame_ts`, `last_error`, `roi_version` (se aplicável).
- Compatibilidade: manter o schema atual; novas chaves devem ser opcionais.

Logs/diagnóstico
- Eventos de falha de camera/heartbeat registrados em `logs/agent.log` e usados nos runbooks de campo.
