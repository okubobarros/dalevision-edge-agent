# Spec Impact Matrix

Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

| Spec/Capacidade | Componentes impactados | APIs/Contratos | Entidades | Regressao prioritaria | Confianca |
|---|---|---|---|---|---|
| Edge activation | Edge `activation.py`, `stores/views_activation.py`, `edge/auth.py` | activation token, `X-EDGE-TOKEN`, download signed token | Store, ActivationToken, EdgeToken, EdgeDevice | TTL, uso unico, store match, remocao do token local | 🟢 CONFIRMADO |
| Heartbeat | Edge heartbeat loop, `apps/edge`, `views_edge_status.py` | `heartbeat`, minute stats, status API | EdgeEventMinuteStats, EdgeDevice, Store | Sucesso -> ACTIVE, rede -> DEGRADED, auth -> ERROR | 🟢 CONFIRMADO |
| Camera health | Edge camera health, backend edge/cameras | `camera_health` | Camera, CameraHealth, CameraHealthLog | NVR offline, camera offline, ultimo status | 🟢 CONFIRMADO |
| Snapshot/diagnostico | Snapshot, Doctor, logs | diagnostics.json/txt, snapshot best-effort | CameraSnapshot | Sem OpenCV, sem ffmpeg, credencial invalida | 🟢 CONFIRMADO |
| Vision events | Edge vision, `apps/edge`, `core` | `vision.*`, `retail.event.v1`, `event_id` | DetectionEvent, EventMedia, EdgeEventRaw | Duplicidade, payload canonico, midia ausente | 🟢 CONFIRMADO |
| Auto-update | Updater, Windows scheduler, release/policy | latest release, update report, health gate | EdgeRelease, EdgeUpdatePolicy, EdgeUpdateEvent | Rollback, min version, canary/stable | 🟢 CONFIRMADO |
| Trial/paywall | Middleware, billing, entitlements | `402 TRIAL_EXPIRED`, whitelists | Subscription, BillingCustomer, AuditLog | Edge nao bloqueado, staff bypass, schema drift | 🟢 CONFIRMADO |
| RBAC cameras/stores | permissions, ViewSets, SupportGrant | owner/admin/manager/viewer | OrgMember, SupportAccessGrant, Camera | Viewer read-only, support grant expira | 🟢 CONFIRMADO parcial |
| Frontend operations | React dashboard/cameras/copilot, API client | `/api/`, `/api/v1/`, retry refresh | Store, Camera, DetectionEvent, Copilot* | Sessao expirada, fallback rota, loading/error | 🟡 INFERIDO |
| Copilot/reports | `apps/copilot`, LLM, frontend | insights, conversations, reports 72h | CopilotConversation, CopilotMessage, ActionOutcome | Timeout LLM, loja sem dados, permissao | 🟡 INFERIDO |
