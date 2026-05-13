# consultar-health-snapshot - Design

## Health

- 🟢 Health é append-only em `CameraHealthLog` mais atualização denormalizada na câmera.
- 🟢 Normalização garante status conhecido.
- 🟢 Onboarding e journey events são efeitos colaterais de status saudável.

## RTSP

- 🟢 Probe tenta OpenCV.
- 🟢 Se OpenCV não existe, usa TCP connect.
- 🟢 Hard timeout pode usar processo separado ou thread conforme setting.

## Snapshot

- 🟢 Backend upload usa signed URL e catálogo `CameraSnapshot`.
- 🟢 Edge upload usa endpoint em `apps.edge` e atualiza `last_snapshot_url`.
- 🟢 `dvsk` no fragmento da URL permite recuperar storage_key de fallback.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\services.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\views_snapshot.py`.
