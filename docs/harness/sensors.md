# Sensors (Feedback Loop)

Este documento define sinais minimos para medir onboarding/ativacao sem depender de interpretacao manual.

## 1. Gates locais
- `scripts/harness_check.ps1` deve validar:
  - `.env` com chaves obrigatorias.
  - higiene de logs (sem segredo).
  - testes criticos de onboarding/runtime.

## 2. Eventos de funil
- `onboarding_started`
- `agent_first_heartbeat`
- `camera_discovered`
- `camera_validated`
- `activation_completed`
- `activation_failed`

Observacao:
- No Edge, estes eventos sao emitidos para `/api/edge/events/` com idempotencia (`receipt_id`/`idempotency_key`) e sanitizacao de segredos.

Campos minimos por evento:
- `store_id`
- `agent_id`
- `timestamp`
- `error_code` (quando falha)
- `trace_id` (quando houver)

## 3. Codigos de erro curtos
- `NVR_AUTH_FAIL`
- `NVR_UNREACHABLE`
- `RTSP_TIMEOUT`
- `SNAPSHOT_UNAVAILABLE`
- `HEARTBEAT_REJECTED`
- `DOCTOR_SHARE_FAIL`

Mapeamento no runtime Edge:
- `camera_health.error=auth_failed` -> `NVR_AUTH_FAIL`
- `camera_health.error=rtsp_timeout` -> `RTSP_TIMEOUT`
- Demais falhas de camera -> `NVR_UNREACHABLE`
- Heartbeat `401/403` -> `HEARTBEAT_REJECTED`

## 4. Alertas recomendados
- Ativacao falhando acima de 10% por janela de 24h.
- Tempo mediano de ativacao acima de 15 minutos.
- Doctor share falhando acima de 5%.
- Heartbeat ausente acima do SLA esperado por loja.
