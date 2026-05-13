# edge - Requirements

## Escopo

- 🟢 Esta unit cobre o backend `apps.edge` do repositório `C:\workspace\dale-vision`.
- 🟢 O módulo recebe eventos do agente, autentica Edge Token, deduplica por receipt, atualiza presença operacional, persiste eventos canônicos, projeta métricas de visão e mantém estatísticas por minuto.
- 🟢 Endpoints principais: `/api/edge/events/`, `/api/edge/cameras/`, `/api/edge/stores/{store_id}/cameras/`, `/api/edge/cameras/{camera_id}/test_connection/`.
- 🟢 Endpoint legado/MVP: `/api/v1/ingest/events/`.
- 🟡 Update policy/report e snapshot usam o app `edge`, mas estão detalhados em units próprias (`edge-agent-update-installation` e `cameras`).

## Requisitos Funcionais

### RF-001 - Autenticar Edge Token

- 🟢 O backend deve extrair token de `X-EDGE-TOKEN`, `X_EDGE_TOKEN`, `HTTP_X_EDGE_TOKEN`, `X-STORE-TOKEN`, query param `edge_token`, `Authorization: Bearer` ou `Authorization: Token`.
- 🟢 Quando `X-EDGE-TOKEN` estiver presente, ele deve vencer sobre `Authorization`.
- 🟢 O token deve ser comparado por SHA-256 contra `EdgeToken.token_hash`.
- 🟢 Token inexistente/inativo deve retornar `401` com `code=edge_token_invalid`.
- 🟢 Token válido deve atualizar `EdgeToken.last_used_at`.
- 🟢 Se `requested_store_id` divergir da store do token, deve retornar `403` com `code=edge_store_mismatch`.
- 🟢 Loja bloqueada ou com `blocked_reason` edge-incompatível deve retornar `403` com `code=edge_store_disabled`.
- 🟢 Logs de token inválido devem mascarar token como digest parcial, não token claro.

### RF-002 - Aceitar autenticação de usuário para ingestão

- 🟢 `EdgeEventsIngestView` deve aceitar Knox `TokenAuthentication` quando o usuário tiver acesso à store.
- 🟢 Se usuário não tiver acesso, deve retornar `403`.
- 🟡 Este caminho existe para operações internas/testes e não substitui o Edge Token do agente.

### RF-003 - Validar envelope de evento

- 🟢 `EdgeEventSerializer` exige `event_name`.
- 🟢 Campos opcionais incluem `ts`, `source`, `data`, `meta`, `receipt_id`, `idempotency_key`, `event_version`, `event_id` e `org_id`.
- 🟢 Payload inválido deve retornar `400` com `detail=payload inválido`.
- 🟢 `store_id` deve ser extraído de `data.store_id`, `payload.store_id` ou `payload.agent.store_id`.
- 🟢 `store_id` ausente ou inválido deve retornar `400`.

### RF-004 - Deduplicar eventos

- 🟢 O backend deve gerar `receipt_id` quando `idempotency_key`/`receipt_id` não forem enviados.
- 🟢 Eventos `vision.*` devem usar bucket de minuto para idempotência.
- 🟢 Evento `retail.event.v1` deve usar bucket de 5 minutos.
- 🟢 Outros eventos devem usar hash de campos principais.
- 🟢 O backend deve usar cache Redis com chave `edge_dedupe:{store_id}:{receipt_id}` e TTL de 60 segundos para dedupe rápido.
- 🟢 O backend deve usar `event_receipts` com `ON CONFLICT (event_id) DO NOTHING` para dedupe canônico no Postgres.
- 🟢 Evento duplicado deve retornar `200` com `deduped=true`.

### RF-005 - Atualizar presença de store e device

- 🟢 Todo evento válido deve atualizar `stores.last_seen_at` com throttle de 30 segundos.
- 🟢 Heartbeat deve forçar atualização de `last_seen_at`.
- 🟢 O backend deve chamar `touch_edge_device_seen` com `store_id`, `device_key`, `installed_version`, `update_channel` e flag `seen_via_heartbeat`.
- 🟢 Device com status `retired` deve ser rejeitado com `403` e `code=edge_device_retired`.

### RF-006 - Persistir receipt canônico e raw event

- 🟢 Evento novo deve inserir registro em `public.event_receipts`.
- 🟢 Evento não-heartbeat deve inserir `EdgeEventRaw` em `edge_events_raw`.
- 🟢 Heartbeat não deve salvar JSON bruto em `EdgeEventRaw` para reduzir volume.
- 🟢 Falha operacional/SQL ao inserir receipt deve retornar `503` ou `500` com `reason=db_write_failed`.

### RF-007 - Validar contratos de visão

- 🟢 Eventos `vision.*` devem exigir `camera_id`, `ts`, `metric_type`, `ownership` e `roi_entity_id`.
- 🟢 Evento canônico de visão deve exigir `event_id`, `event_name`, `event_version`, `store_id`, `camera_id`, `roi_entity_id`, `ts`, `payload.metric_type` e `payload.ownership`.
- 🟢 Falha no contrato deve retornar `400` com `reason=vision_contract_invalid` ou `vision_canonical_contract_invalid`.

### RF-008 - Validar contrato retail.event.v1

- 🟢 `retail.event.v1` deve exigir `store_id`, `ts`, `event_type`, `value`, `source` e `confidence`.
- 🟢 Tipos aceitos incluem `person_enter`, `person_exit`, `queue_detected`, `queue_length`, `sale_completed`, `staff_detected` e `zone_dwell`.
- 🟢 `confidence` deve ser numérico e aceito em escala `0..1` ou `0..100`.
- 🟢 Timestamp inválido deve gerar erro `invalid_iso_ts`.
- 🟢 Falha deve retornar `400` com `reason=retail_event_contract_invalid`.

### RF-009 - Projetar métricas de visão

- 🟢 `vision.metrics.v1` deve projetar `traffic_metrics` e `conversion_metrics`.
- 🟢 `vision.crossing.v1` deve inserir evento atômico e acumular entrada em `traffic_metrics`.
- 🟢 `vision.queue_state.v1` deve inserir evento atômico, calcular fila por bucket e atualizar `conversion_metrics`.
- 🟢 `vision.checkout_proxy.v1` deve derivar `checkout_events` de eventos atômicos no bucket.
- 🟢 `vision.zone_occupancy.v1` deve derivar ocupação e dwell médio para `traffic_metrics`.
- 🟢 Projeções devem marcar receipt como processado em sucesso e como failed em exceção.

### RF-010 - Agregar estatísticas por minuto

- 🟢 O backend deve incrementar `EdgeEventMinuteStats` por `(store_id, event_name, minute_bucket)`.
- 🟢 Evento duplicado também pode incrementar estatística por minuto.
- 🟢 A tabela deve ter unicidade por `store_id`, `event_name` e `minute_bucket`.
- 🟢 O comando `prune_edge_event_minute_stats` deve remover linhas antigas, com retenção default de 7 dias.

### RF-011 - Processar camera health e heartbeat

- 🟢 `camera_health` deve atualizar `Camera.status`, `last_seen_at`, `last_error` e criar `CameraHealthLog`.
- 🟢 `edge_heartbeat`, `camera_heartbeat` e `edge_camera_heartbeat` devem criar/atualizar câmeras, registrar health log e emitir eventos de transição de status quando aplicável.
- 🟢 Heartbeat com câmera nova deve respeitar limite de câmeras do trial via `enforce_trial_camera_limit`.
- 🟢 `snapshot_url` excessivamente grande deve ser descartado.

### RF-012 - Encaminhar alertas do edge

- 🟢 Evento `alert` deve ser convertido para payload do `AlertRuleViewSet.ingest`.
- 🟢 O usuário de serviço deve ser `EDGE_SERVICE_USERNAME` ou `edge-agent`.
- 🟢 Ausência do usuário de serviço deve retornar `500` com mensagem explícita.
- 🟢 Falha do ingest de alerta deve marcar receipt como failed.

### RF-013 - Expor câmeras para o agente

- 🟢 `/api/edge/cameras/` deve retornar câmeras ativas da store do token.
- 🟢 `/api/edge/stores/{store_id}/cameras/` deve validar se o token pertence à store informada.
- 🟢 A serialização deve usar `_serialize_cameras_for_edge`.

### RF-014 - Endpoint MVP legado

- 🟢 `/api/v1/ingest/events/` deve aceitar `Authorization: Bearer <edge-token>`.
- 🟢 Deve exigir `event_id`, `event_type`, `camera_id` e `timestamp`.
- 🟢 Deve rejeitar `store_id` divergente com `403`.
- 🟢 Deve inserir em `event_receipts` com `ON CONFLICT DO NOTHING`.
- 🟢 Deve atualizar `stores.last_seen_at`.
- 🟡 Testes legados parecem referenciar campos antigos de `EdgeToken`; exigem validação antes de reuso.

## Requisitos Não Funcionais

- 🟢 Segurança: Edge Token nunca deve ser logado em claro.
- 🟢 Idempotência: toda ingestão deve tolerar retry do agente sem duplicar processamento canônico.
- 🟢 Observabilidade: respostas devem devolver `receipt_id`, `trace_id`, `stored` e `deduped` quando aplicável.
- 🟢 Performance: dedupe Redis de 60 segundos e throttle de `stores.last_seen_at` reduzem escrita em alta frequência.
- 🟢 Resiliência: falha em projeção deve marcar receipt failed, não apagar o raw receipt.
- 🟢 Compatibilidade: endpoints e headers legados devem continuar aceitos.

## Critérios de Aceitação

### Cenário: token válido ingere heartbeat

- 🟢 Dado um `EdgeToken` ativo para uma store.
- 🟢 Quando o agente enviar `edge_heartbeat` para `/api/edge/events/` com `X-EDGE-TOKEN`.
- 🟢 Então o backend deve autenticar, inserir receipt, atualizar last_seen, tocar edge device e responder `ok=true`.

### Cenário: retry do mesmo evento

- 🟢 Dado um evento já recebido com mesmo `receipt_id`.
- 🟢 Quando o agente reenviar o evento.
- 🟢 Então o backend deve responder `200`, `deduped=true` e não duplicar `event_receipts`.

### Cenário: visão sem contrato mínimo

- 🟢 Dado um evento `vision.queue_state.v1` sem `metric_type`, `ownership` ou `roi_entity_id`.
- 🟢 Quando o backend validar o contrato.
- 🟢 Então deve retornar `400` com `reason=vision_contract_invalid`.

### Cenário: fila projetada

- 🟢 Dado um evento `vision.queue_state.v1` válido.
- 🟢 Quando o backend processar o evento novo.
- 🟢 Então deve inserir evento atômico, atualizar `conversion_metrics`, atualizar estatística por minuto e marcar receipt processed.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\auth.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\mvp_ingest.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\vision_metrics.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\serializers.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\urls.py`.
