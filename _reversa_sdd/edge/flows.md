# edge - Flows

## Fluxo 1 - Autenticar Edge Token

1. 🟢 Request chega com token em header/query/Authorization.
2. 🟢 `_extract_store_token` prioriza `X-EDGE-TOKEN`.
3. 🟢 Backend calcula SHA-256.
4. 🟢 Busca `EdgeToken` ativo por `token_hash`.
5. 🟢 Valida store solicitada quando aplicável.
6. 🟢 Verifica status/bloqueio da store.
7. 🟢 Atualiza `last_used_at`.
8. 🟢 Injeta `request.edge_store_id` e `request.store`.

## Fluxo 2 - Ingerir evento atual

1. 🟢 POST `/api/edge/events/`.
2. 🟢 `EdgeEventSerializer` valida payload.
3. 🟢 Resolve `event_name`, `source`, `data`, `store_id`, `receipt_id` e `trace_id`.
4. 🟢 Cache Redis tenta dedupe.
5. 🟢 Normaliza evento.
6. 🟢 Autentica usuário Knox ou Edge Token.
7. 🟢 Rejeita store inválida ou device retired.
8. 🟢 Atualiza `EdgeDevice` visto.
9. 🟢 Valida contratos vision/retail.
10. 🟢 Atualiza `stores.last_seen_at`.
11. 🟢 Valida câmera quando necessário.
12. 🟢 Insere `event_receipts`.
13. 🟢 Se duplicado, retorna `200 deduped=true`.
14. 🟢 Se novo, persiste raw quando aplicável.
15. 🟢 Incrementa minute stats.
16. 🟢 Despacha handler por `event_name`.

## Fluxo 3 - Projetar vision.queue_state.v1

1. 🟢 Evento passa pelos contratos vision.
2. 🟢 Receipt canônico é inserido.
3. 🟢 `insert_vision_atomic_event_if_new` insere amostra atômica.
4. 🟢 `apply_vision_queue_state` calcula bucket por `EDGE_QUEUE_BUCKET_SECONDS` ou 30s.
5. 🟢 Aplica mínimo de dwell `EDGE_QUEUE_MIN_DWELL_SECONDS` ou 8s.
6. 🟢 Estima staff ativo por payload e role inference.
7. 🟢 Se configurado, exclui staff da fila.
8. 🟢 Atualiza/insere `conversion_metrics`.
9. 🟢 Pode abrir/resolver `DetectionEvent` `queue_long`.
10. 🟢 Marca first metrics received se aplicável.

## Fluxo 4 - Processar heartbeat

1. 🟢 Evento normalizado como `edge_heartbeat`, `camera_heartbeat` ou `edge_camera_heartbeat`.
2. 🟢 Backend calcula snapshot de status antes do processamento.
3. 🟢 Extrai lista de câmeras do payload.
4. 🟢 Para cada câmera, resolve por `external_id`, UUID/id ou nome.
5. 🟢 Cria câmera nova se necessário e permitido pelo trial.
6. 🟢 Atualiza status, last_seen, last_error, snapshot URL e RTSP.
7. 🟢 Cria `CameraHealthLog`.
8. 🟢 Calcula transições.
9. 🟢 Emite status events de store/câmera quando há mudança.
10. 🟢 Marca receipt processed e retorna `201` ou `200`.

## Fluxo 5 - Ingerir alert

1. 🟢 Evento `alert` passa por autenticação, receipt e dedupe.
2. 🟢 Backend monta payload compatível com `AlertRuleViewSet.ingest`.
3. 🟢 Resolve usuário de serviço por `EDGE_SERVICE_USERNAME`.
4. 🟢 Chama view de alerts internamente com `force_authenticate`.
5. 🟢 Resposta recebe `receipt_id`, `trace_id`, `stored` e `deduped`.
6. 🟢 Falha marca receipt failed; sucesso marca processed.

## Fluxo 6 - MVP legado

1. 🟢 POST `/api/v1/ingest/events/`.
2. 🟢 Extrai token de `Authorization: Bearer`.
3. 🟢 Valida SHA-256 contra `EdgeToken`.
4. 🟢 Exige `event_id`, `event_type`, `camera_id` e `timestamp`.
5. 🟢 Rejeita `store_id` divergente.
6. 🟢 Insere em `event_receipts` com `ON CONFLICT DO NOTHING`.
7. 🟢 Atualiza `stores.last_seen_at`.
8. 🟢 Retorna `ok=true`.
