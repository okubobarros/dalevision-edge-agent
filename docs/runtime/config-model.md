# Config Model

Principais variáveis (derivadas do README/AGENTS):
- Identidade: `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN`, `AGENT_ID`.
- Camera source: `CAMERA_SOURCE_MODE` (`api_first`, `local_only`), `CAMERA_SYNC_ENABLED`, `VISION_REMOTE_CAMERA_SYNC_ENABLED`, `CAMERAS_JSON`.
- Heartbeat/health: `HEARTBEAT_INTERVAL_SECONDS`, `CAMERA_SYNC_FATAL` (0 para tolerar falhas).
- Vision: `VISION_ENABLED`, `VISION_ALERTS_ENABLED`, `VISION_SOURCE`, `VISION_VIDEO_PATH`, `VISION_ROI_PATH`, `VISION_BUCKET_SECONDS`, etc.
- Outbox: `VISION_OUTBOX_ENABLED`, `VISION_OUTBOX_PATH`, `VISION_OUTBOX_BATCH_SIZE`, `VISION_OUTBOX_MAX_ATTEMPTS`.
- Auto-update: `AUTO_UPDATE_ENABLED`, `UPDATE_INTERVAL_SECONDS`, `UPDATE_CHECK_URL` (fallback).
- Service mode: `SERVICE_MODE` desabilita swap automático durante update.

Princípios
- Sem segredos em log.
- Defaults seguros: heartbeat sempre ativo; sync tolerante a falha temporária.
- Campos novos devem ser backward compatible ou feature-flagged.
