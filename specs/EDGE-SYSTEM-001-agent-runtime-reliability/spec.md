# EDGE-SYSTEM-001 — Agent Runtime Reliability

Estado: draft
Owner: Edge/Eng
Última atualização: 2026-04-04

## Contexto
Garantir operação contínua do Edge Agent em loja (Windows), com sinal de liveness, saúde das câmeras, envio de eventos, update seguro e diagnóstico rápido.

## Problema
Quedas de rede, instabilidade de câmera e falhas de dependências (OpenCV, atualização) podem bloquear a jornada de ativação e operação. Precisamos de comportamento previsível e compatível com o protocolo atual.

## Objetivos operacionais
- Manter heartbeat consistente para o backend detectar liveness.
- Reportar saúde de câmeras sem quebrar protocolo atual.
- Garantir entrega de eventos com offline-first (outbox).
- Permitir diagnóstico rápido em campo (doctor/scan + logs).
- Atualizar agente de forma segura e recuperável.

## Contratos que não podem quebrar
- Payload de heartbeat/camera health atual (campos existentes devem permanecer; novos campos apenas opcionais).
- Endpoints: `GET /api/edge/update-policy/`, `POST /api/edge/update-report/`, `POST /api/v1/ingest/events/` (idempotente), heartbeat endpoint atual.
- Eventos de update: `started`, `downloaded`, `verified`, `activated`, `healthy`, `failed`.

## Behavior esperado do runtime
- Loop principal envia heartbeat no intervalo configurado; inclui versão do agente, store_id, agent_id, status.
- Camera health agregado no heartbeat ou endpoint dedicado (conforme versão) com status por câmera.
- Outbox (SQLite) armazena eventos quando offline e reenvia ao recuperar conexão.
- Logs legíveis, sem segredos.

## Falha de rede
- Heartbeat: se falhar, registrar erro e retry com backoff simples; não derrubar processo.
- Outbox: acumula eventos até limite configurado; reenvia em reconexão mantendo ordem temporal; idempotência por event_id/trace_id.
- Update: não aplica download parcial; permanece na versão corrente; marca `failed` no report quando disponível.

## Falha de câmera
- Health marca câmera como `offline/degraded` com `last_error` e `last_frame_ts` se disponível.
- Não bloqueia heartbeat; continua reportando outras câmeras.
- Se RTSP inválido/timeout, log claro e manter estado `degraded` até próximo sucesso.

## Sem OpenCV
- Pipeline de visão degrada: não gerar métricas/detecções, mas mantém heartbeat e camera health.
- Logs indicam ausência de OpenCV/ffmpeg; snapshot opcional falha com mensagem clara.

## Diagnóstico
- Comando `... doctor --share` gera pacote com logs/estado sanitizado.
- `scan --mode nvr` ajuda a validar câmeras em campo.
- Logs principais: `logs/agent.log`, `logs/diagnostics.*`, `logs/update.log`.
- Mensagens curtas e orientadas a leigo; nunca incluir segredos.

## Update
- Política via `GET /api/edge/update-policy/`.
- Se `target_version` > atual: download → checksum → swap (fora de SERVICE_MODE) → reinício → report `healthy` no boot.
- Fallback legado: `UPDATE_CHECK_URL` só se policy indisponível.
- Em `SERVICE_MODE`, não aplicar swap automático; logar e aguardar operador.

## Observabilidade
- Métricas: sucesso/erro de heartbeat, latência de heartbeat, backlog do outbox, falhas de câmera, sucesso/falha de update.
- Logs estruturados com trace_id/event_id quando houver payload.
- Alertas recomendados (backend): heartbeat ausente > SLA; outbox crescendo; update failed.

## Rollout / Fallback / Rollback
- Feature flags no backend para mudanças de payload (novos campos opcionais).
- Rollback: manter pacote anterior para swap manual; se update falhar, permanecer na versão antiga.
- Fallback de ingest: reenvio pelo outbox; fallback de update via `UPDATE_CHECK_URL` (legado) apenas quando policy indisponível.

## Critérios de aceite
- Heartbeat enviado no intervalo configurado, com sucesso ≥99% em rede estável; tolerância a queda sem crash.
- Camera health reportado mesmo com câmeras individuais offline/degraded.
- Outbox entrega eventos após reconexão sem perdas (idempotente) em teste de queda de rede simulada.
- Update: aplicado com verificação de checksum; em falha, agente segue operando na versão anterior.
- Sem OpenCV: agente continua ativo e reporta degradação, sem crash.
- Doctor gera pacote com logs e não contém segredos.

## Evidências esperadas
- Logs mostrando sequência heartbeat success/retry e recovery.
- Dump do outbox antes/depois de reconexão com eventos entregues.
- Registro de update-report com fases completas ou failure registrada.
- Execução do `doctor --share` contendo estado de saúde e sem segredos.
