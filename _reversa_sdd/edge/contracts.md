# edge - Contracts

## POST /api/edge/events/

### Request

```json
{
  "event_name": "vision.queue_state.v1",
  "event_version": 1,
  "ts": "2026-03-14T10:20:10Z",
  "source": "edge",
  "receipt_id": "optional-id",
  "idempotency_key": "optional-idempotency-key",
  "data": {
    "store_id": "uuid",
    "camera_id": "camera-external-or-uuid",
    "ts": "2026-03-14T10:20:10Z",
    "metric_type": "queue",
    "ownership": "primary",
    "roi_entity_id": "queue-zone-1"
  },
  "meta": {}
}
```

- 🟢 `event_name` é obrigatório.
- 🟢 `data` é opcional no serializer, mas vários eventos exigem campos dentro dele.
- 🟢 `receipt_id` e `idempotency_key` são opcionais.

### Autenticação

- 🟢 `X-EDGE-TOKEN: <token>`.
- 🟢 `X-STORE-TOKEN: <token>`.
- 🟢 `Authorization: Bearer <token>`.
- 🟢 `Authorization: Token <token>`.
- 🟢 `?edge_token=<token>`.
- 🟢 Knox user token também é aceito quando usuário possui acesso à store.

### Response sucesso

```json
{
  "ok": true,
  "receipt_id": "receipt",
  "trace_id": "trace",
  "stored": true,
  "deduped": false
}
```

- 🟢 Evento novo normalmente retorna `201`.
- 🟢 Evento deduplicado retorna `200`.

### Erros conhecidos

- 🟢 `400 payload inválido`.
- 🟢 `400 store_id inválido ou ausente`.
- 🟢 `400 vision_contract_invalid`.
- 🟢 `400 vision_canonical_contract_invalid`.
- 🟢 `400 retail_event_contract_invalid`.
- 🟢 `400 camera_not_found`.
- 🟢 `401 edge_token_invalid`.
- 🟢 `403 edge_store_mismatch`.
- 🟢 `403 edge_store_disabled`.
- 🟢 `403 edge_device_retired`.
- 🟢 `503 db_write_failed`.

## GET /api/edge/cameras/

- 🟢 Autentica Edge Token.
- 🟢 Usa store do token.
- 🟢 Retorna câmeras ativas ordenadas por `updated_at` desc.
- 🟢 Usa `_serialize_cameras_for_edge`.

## GET /api/edge/stores/{store_id}/cameras/

- 🟢 Autentica Edge Token com `requested_store_id`.
- 🟢 Rejeita token de outra store.
- 🟢 Retorna câmeras ativas da store informada.

## POST /api/edge/cameras/{camera_id}/test_connection/

- 🟢 Autentica token da store da câmera.
- 🟢 Se payload contém `ok`, usa resultado enviado pelo agente.
- 🟢 Se payload não contém `ok`, tenta probe RTSP no backend.
- 🟢 Atualiza `Camera.status`, `last_seen_at`/`last_error` e cria `CameraHealthLog`.

## POST /api/v1/ingest/events/

### Request

```json
{
  "event_id": "stable-event-id",
  "event_type": "queue_count",
  "camera_id": "cam_01",
  "timestamp": "2026-03-14T10:20:10Z",
  "store_id": "optional-store-id"
}
```

- 🟢 Token vem de `Authorization: Bearer`.
- 🟢 Campos obrigatórios: `event_id`, `event_type`, `camera_id`, `timestamp`.
- 🟢 `store_id` enviado deve bater com store do token.

### Response sucesso

```json
{
  "ok": true,
  "event_id": "stable-event-id"
}
```

## Tabelas/Modelos

### EdgeToken

- 🟢 `store_id`.
- 🟢 `token_hash`.
- 🟢 `token_plaintext`.
- 🟢 `active`.
- 🟢 `created_at`.
- 🟢 `last_used_at`.

### EdgeEventMinuteStats

- 🟢 Tabela `edge_event_minute_stats`.
- 🟢 Único por `store_id`, `event_name`, `minute_bucket`.
- 🟢 Campos: `count`, `last_event_at`, `created_at`, `updated_at`.

### EdgeEventRaw

- 🟢 Tabela `edge_events_raw`.
- 🟢 `event_id` único.
- 🟢 `schema_version` default `1.1`.
- 🟢 `event_type`, `global_id`, `store_id`, `camera_id`, `zone_id`, `occurred_at`, `confidence`, `payload`.

### event_receipts

- 🟢 Tabela SQL pública usada por SQL direto.
- 🟢 `event_id` é chave de idempotência.
- 🟢 Guarda `event_name`, `event_version`, `ts`, `source`, `raw`, `meta`.
- 🟢 Recebe `processed_at`, `last_error`, `attempt_count` por funções de marcação.
