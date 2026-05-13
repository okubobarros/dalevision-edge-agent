# consultar-status-edge - Design

## Snapshot Edge

- 🟢 `compute_store_edge_status_snapshot` é função central.
- 🟢 Usa thresholds fixos: 120s online, 300s degraded, 600s health recente.
- 🟢 Heartbeat edge vem de minute stats e event receipts.
- 🟢 Câmera usa health log recente, fallback por `last_seen_at` e eventos edge.
- 🟢 Payload passa por `_with_stable_contract`.

## Activation Status

- 🟢 `StoreActivationStatusService.get_status` chama snapshot edge.
- 🟢 Lê onboarding progress, cameras, ROI, EdgeDevice e EdgeRelease.
- 🟢 `derive_activation_contract` decide status técnico e próxima ação.
- 🟢 Funil usa eventos `onboarding_started`, `agent_first_heartbeat`, `camera_discovered`, `camera_validated`, `activation_completed`, `activation_failed`.

## Estados

- 🟢 `pending_download`.
- 🟢 `pending_install`.
- 🟢 `agent_seen`.
- 🟢 `ready_for_cameras`.
- 🟢 `activation_completed`.
- 🟢 `activation_failed`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_status.py`.
