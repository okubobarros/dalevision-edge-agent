# stores - Contracts

## POST /api/v1/stores/{store_id}/activation-token/

```json
{
  "ok": true,
  "store_id": "uuid",
  "activation_token": "secret",
  "expires_at": "iso",
  "issued_at": "iso",
  "expires_in_seconds": 86400,
  "server_now_utc": "iso",
  "single_use": true,
  "method": {"id": "store_activation_token_issue", "version": "v1"}
}
```

- 🟢 Requer usuário autenticado e papel de gestão.

## POST /api/v1/stores/activate/

```json
{
  "token": "activation-token",
  "device_key": "optional-device-key",
  "installed_version": "vX.Y.Z",
  "update_channel": "stable"
}
```

```json
{
  "ok": true,
  "store_id": "uuid",
  "device_id": "uuid",
  "device_key": "edge-device",
  "installed_version": "vX.Y.Z",
  "update_channel": "stable",
  "edge_token": "secret",
  "method": {"id": "store_activate_device", "version": "v1"}
}
```

## GET /api/v1/stores/{store_id}/download-agent/

```json
{
  "ok": true,
  "store_id": "uuid",
  "download_url": "https://backend/api/v1/stores/{id}/download-agent/file/?dl=signed",
  "filename": "DaleVisionEdgeSetup.exe",
  "onboarding_ref": "onb-...",
  "activation_token_embedded": false,
  "expires_at": null,
  "method": {"id": "store_download_agent", "version": "v1"}
}
```

## GET /api/v1/stores/{store_id}/edge-status/

- 🟢 Resposta contém `ok`, `online`, `store_id`, `connectivity_status`, `pipeline_status`, `store_status`, `last_heartbeat_at`, `agent_id`, `version`, contadores e lista de câmeras.
- 🟢 Reason conhecido inclui `store_not_found`, `forbidden`, `no_heartbeat`, `recent_heartbeat`, `stale_heartbeat`, `heartbeat_expired`, `all_cameras_online`, `partial_camera_coverage`, `camera_health_stale`, `db_unavailable`, `edge_status_fallback`.

## GET /api/v1/stores/{store_id}/activation-status/

- 🟢 Retorna `technical_status`, `value_status`, `activation_state`, `state_version`, `setup_blocked`, `blocking_reason`, `next_action`, `edge_last_seen_at`, `installed_version`, `cameras`, `legacy`, `device`, `release_target_version`, `onboarding_funnel`.

## GET /api/v1/stores/{store_id}/cameras

- 🟢 Com Edge Token válido retorna lista operacional:

```json
[
  {
    "id": "uuid",
    "camera_id": "uuid",
    "store_id": "uuid",
    "zone_id": "uuid-or-null",
    "name": "Camera",
    "external_id": "external",
    "active": true,
    "status": "online",
    "brand": "brand",
    "model": "model",
    "onvif": false,
    "connection_type": "rtsp_direct",
    "ip": "192.168.0.10",
    "username": "user",
    "password": "secret",
    "rtsp_url": "rtsp://...",
    "rtsp_url_masked": "rtsp://***",
    "indicators": [],
    "updated_at": "iso"
  }
]
```

## GET /api/v1/edge/releases/latest/

- 🟢 Query: `channel=stable|canary`.
- 🟢 Retorna release ativa ou fallback:

```json
{
  "ok": true,
  "channel": "stable",
  "current_version": "vX.Y.Z",
  "minimum_supported_version": "vA.B.C",
  "download_url": "https://...",
  "package_sha256": "hex",
  "package_size_bytes": 123,
  "release_notes": "notes",
  "windows_setup_url": "https://...",
  "method": {"id": "edge_release_latest", "version": "v1"}
}
```

## PUT /api/v1/stores/{store_id}/edge-update-policy/

- 🟢 Requer gestão.
- 🟢 Campos obrigatórios efetivos: `target_version`, `package.url`, `package.sha256`.
- 🟢 Retorna policy serializada com rollout, package, health gate e rollback policy.

## POST /api/v1/stores/{store_id}/edge/update/

- 🟢 Requer gestão.
- 🟢 Body opcional: `device_key`, `force_update`, `package_sha256`.
- 🟢 Retorna `202` quando update foi solicitado, `200` se já estava up-to-date, `409` quando release/SHA ausente.
