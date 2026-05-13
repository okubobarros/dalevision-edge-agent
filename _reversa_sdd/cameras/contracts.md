# cameras - Contracts

## Camera

- 🟢 Tabela: `cameras`.
- 🟢 Campos principais: `id`, `store_id`, `zone_id`, `name`, `external_id`, `brand`, `model`, `ip`, `onvif`, `active`, `rtsp_url`, `username`, `password`, `indicators`, `status`, `last_seen_at`, `last_snapshot_url`, `last_error`, `created_at`, `updated_at`.

## CameraHealthLog

- 🟢 Tabela: `camera_health_logs`.
- 🟢 Campos: `id`, `camera_id`, `checked_at`, `status`, `latency_ms`, `snapshot_url`, `error`.

## CameraROIConfig

- 🟢 Tabela: `camera_roi_configs`.
- 🟢 Unicidade: `(camera, version)`.
- 🟢 Campos: `camera`, `version`, `config_json`, `updated_at`, `updated_by`.

## CameraSnapshot

- 🟢 Tabela: `camera_snapshots`.
- 🟢 Campos: `camera`, `snapshot_url`, `storage_key`, `captured_at`, `metadata`, `created_at`.

## GET/POST /api/v1/cameras/

- 🟢 GET aceita query `store_id`.
- 🟢 POST exige store e papel de gestão.
- 🟢 Resposta pública mascara RTSP e oculta senha/RTSP real.

## GET/PUT /api/v1/cameras/{id}/roi/

- 🟢 GET retorna latest, active e history.
- 🟢 PUT recebe:

```json
{
  "config_json": {
    "status": "published",
    "zones": [],
    "lines": [],
    "metrics_enabled": true,
    "image": {},
    "meta": {}
  },
  "reason_for_change": "ajuste operacional",
  "snapshot_id": "optional"
}
```

## GET /api/v1/cameras/{id}/roi/latest/

- 🟢 Aceita usuário autenticado ou Edge Token.
- 🟢 Retorna ROI published mais recente ou versão 0.

## POST /api/v1/cameras/{id}/health/

```json
{
  "status": "online",
  "latency_ms": 123,
  "error": null,
  "snapshot_url": "https://...",
  "ts": "2026-05-07T00:00:00Z"
}
```

## POST /api/v1/cameras/{id}/test_connection/

- 🟢 Resposta:

```json
{
  "ok": true,
  "latency_ms": 120,
  "fps_est": 15.2,
  "frames_read": 30,
  "reason": null,
  "error_msg": "",
  "extra": {},
  "elapsed_ms": 1000,
  "status": "ok"
}
```

## POST /api/v1/cameras/{id}/snapshot/upload/

- 🟢 Multipart: `file` ou `snapshot`.
- 🟢 Content types: `image/jpeg`, `image/png`.
- 🟢 Retorna `camera_id`, `snapshot_id`, `storage_key`, `snapshot_url`, `expires_in=600`.

## GET /api/v1/cameras/{id}/snapshot/

- 🟢 Retorna signed URL de snapshot mais recente, fallback por `last_snapshot_url` ou erro.

## POST /api/edge/cameras/{camera_id}/snapshot/

- 🟢 Multipart: `snapshot`.
- 🟢 Autenticação: Edge Token.
- 🟢 Retorna `{ "snapshot_url": "...", "status": "stored" }`.
