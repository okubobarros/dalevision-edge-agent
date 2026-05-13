# frontend-cameras-alerts — Contratos Externos

## 1. Store Cameras

**Endpoint:** `GET /api/cameras/stores/<storeId>/cameras/` (inferido)
**Chamada:** `camerasService.getStoreCameras(selectedStore)`
**Query Key:** `["store-cameras", selectedStore, stores.length]`
**staleTime:** 15s
**Retry:** 1 vez; apenas ECONNABORTED, timeout, 502/503/504

**Resposta esperada:** `Camera[]`

**Fallback em modo rede:** se `selectedStore === "all"`:
1. `camerasService.getCameras()` → endpoint global
2. Se vazio: `Promise.all(stores.map(s => getStoreCameras(s.id).catch(() => [])))`

---

## 2. Create Camera

**Endpoint:** `POST /api/cameras/stores/<storeId>/cameras/` (inferido)
**Chamada:** `camerasService.createStoreCamera(selectedStore, payload, { onboardingAssisted })`

**Payload:** `CreateCameraPayload` (campos de `camerasService` — não lido diretamente)

**Erros tratados:**

| status | code | Comportamento |
|--------|------|---------------|
| 400/402/409 | `PAYWALL_TRIAL_LIMIT` ou `LIMIT_CAMERAS_REACHED` | Toast customizado com botão "Ir para billing" |
| 400 | outros | Toast.error + fieldMap com FIELD_LABELS (nome, ip, username, password, rtsp_url, brand, model, external_id) |

---

## 3. Store Camera Limits

**Endpoint:** `GET /api/cameras/stores/<storeId>/limits/` (inferido)
**Chamada:** `camerasService.getStoreLimits(selectedStore)`
**Query Key:** `["store-limits", selectedStore]`
**staleTime:** 30s

---

## 4. Store Edge Status (Polling)

**Chamada:** `storesService.getStoreEdgeStatus(selectedStore)`
**Query Key:** `["store-edge-status", selectedStore]`
**Polling:** 20s (online) ou 30s (offline); pausa quando aba oculta
**refetchOnWindowFocus:** false

**Campos usados:**
```typescript
{
  connectivity_status?: "online" | "degraded" | "offline",
  online?: boolean,
  connectivity_age_seconds?: number,   // <= 120 → online
  camera_source_mode_detected?: "api_first" | "local_only_or_unknown",
  camera_sync_age_seconds?: number,    // <= 300 → sync recente
  cameras?: Array<{ camera_id: string, ... }>,  // edgeCameraMap
}
```

---

## 5. Onboarding Progress e Next Step

**Next Step:** `onboardingService.getNextStep(storeId)`
**Query Key:** `["onboarding-next-step", "cameras", selectedStore]`
**staleTime:** 30s

**Progress:** `onboardingService.getProgress(storeId)`
**Query Key:** `["onboarding-progress", "cameras", selectedStore]`
**staleTime:** 30s

---

## 6. Support Requests

**GET:** `supportService.getMyStoreSupportRequests(storeId)`
**Query Key:** `["store-support-requests", selectedStore]`
**staleTime:** 30s

**POST:** `supportService.requestStoreSupport(storeId, message)`
**Mensagem padrão:** `"Solicitação via página Câmeras: usuário em modo leitura precisa apoio para cadastro/ROI."`
**On success:** invalida `["store-support-requests", selectedStore]`

---

## 7. Local Setup API — Blueprint ONVIF

**Base URL:** `http://127.0.0.1:8787` (hardcoded, `EDGE_SETUP_LOCAL_BASE_URL`)
**Endpoint:** `GET /onboarding/blueprint`

**Resposta esperada:** `LocalOnboardingBlueprint`:
```typescript
{
  ok: boolean,
  plan_code: string,
  camera_limit: number,
  candidates: Array<{
    ip: string,
    ports: number[],
    confidence: string,
    status: "ok" | "warning" | "fail",
    reason_code: string,
    selectable: boolean,
    recommended: boolean,
  }>,
  selection_guidance: {
    max_selectable: number,
    recommended_camera_ips: string[],
  }
}
```

---

## 8. Local Setup API — Readiness

**Endpoint:** `GET http://127.0.0.1:8787/onboarding/readiness`

**Resposta esperada:** `LocalReadinessReport`:
```typescript
{
  ok: boolean,
  status: "ready" | "needs_attention" | "blocked",
  summary?: {
    checks_total?: number,
    checks_ok?: number,
    checks_warning?: number,
    checks_fail?: number,
    missing_required_env?: string[],
  },
  checks?: Array<{
    key: string,
    status: "ok" | "warning" | "fail",
    reason_code?: string,
    message?: string,
  }>
}
```

**Download:** `buildReadinessMarkdown(report)` → arquivo `.md` via `downloadTextFile`

---

## 9. Local Setup API — Health Check

**Endpoint:** `GET http://127.0.0.1:8787/health` ou `/` (inferido)

**Resposta esperada:** `LocalSetupApiHealth`:
```typescript
{
  ok?: boolean,
  service?: string,
  status?: string,
  capabilities?: {
    onboarding_blueprint?: boolean,
    onboarding_readiness?: boolean,
    onboarding_installation_check?: boolean,
  }
}
```

---

## 10. Alerts Events (Query)

**Chamada:** `useAlertsEvents({ store_id?, status?, severity?, occurred_from?, occurred_to? })`
**Resposta:** array / `{data:[]}` / `{results:[]}` — normalizado via `normalizeArray`

---

## 11. Alert Delegate Email

**Endpoint:** `POST /api/alerts/events/<eventId>/delegate/` (inferido)
**Chamada:** `alertsService.delegateEventEmail(eventId, { note })`

**Payload:**
```typescript
{
  note: string  // buildDelegationMessage(event, storeName, evidenceUrl)
}
```

**Resposta esperada:**
```typescript
{
  ok: boolean,
  message?: string,
  employee?: { name?: string },
}
```

**Erros tratados:**
- `employee_phone`: string → exibe como mensagem de erro
- `employee_id`: string → exibe como mensagem de erro
- `detail`: string → exibe como mensagem de erro
- Outros → "Delegação indisponível: vincule um e-mail ou telefone ao colaborador..."

---

## 12. Alert Resolve / Ignore

**Resolve:** `resolveMut.mutateAsync(eventId)` via `useResolveEvent()`
**Ignore:** `ignoreMut.mutateAsync(eventId)` via `useIgnoreEvent()`
**On success:** `eventsQuery.refetch()`

---

## 13. Alert Ingest (Dev only)

**Chamada:** `ingestMut.mutate(payload)` via `useIngestAlert()`

**Payload:** `AlertIngestPayload`:
```typescript
{
  store_id: string,
  event_type: "queue_long",
  severity: "warning",
  title: string,
  description: string,
  occurred_at: string,
  metadata: { source: "ui_simulator", ts: number },
  receipt_id: string,  // "ui-dev-<Date.now()>"
}
```

---

## 14. Alert Rules CRUD

**List Rules:** `alertsService.listRules(storeId)` → `AlertRule[]`
**Query Key:** `["alerts", "rules", storeId]`

**Create Rule:** `alertsService.createRule(payload)`
```typescript
{
  store_id: string,
  type: string,            // "queue_long" | "staff_missing" | "suspicious_cancel"
  severity: Severity,
  cooldown_minutes: number,
  active: boolean,
  channels: { dashboard: boolean, email: boolean, whatsapp: boolean },
  threshold: {},
}
```

**Update Rule:** `alertsService.updateRule(ruleId, payload)`
**Usado por:** `handleApplySuggestion` → `{ cooldown_minutes: number }`

---

## 15. Notification Logs

**Chamada:** `alertsService.listLogs({ store_id })`
**Query Key:** `["alerts", "rules", "logs", storeId]`

**Resposta:** `NotificationLog[]`:
```typescript
{
  id: string | number,
  rule_id?: string | number,
  channel?: string,
  status?: "sent" | "suppressed" | "failed",
  sent_at?: string,
  destination?: string,
  error?: string,
}
```

---

## 16. Core Stores (para seletor de alertas)

**Chamada:** `alertsService.listCoreStores`
**Query Key:** `["alerts", "coreStores"]`
**Resposta:** `StoreOption[]` com `id` e `name`

> ⚠️ Este endpoint é diferente de `storesService.getStoresMinimal()` — usa `alertsService` separado.

---

## 17. Analytics (Journey Events)

Todos via `trackJourneyEvent(eventName, payload)`:

| Evento | Trigger | Payload-chave |
|--------|---------|--------------|
| `alert_resolution_completed` | Toda resolução | `alert_id`, `store_id`, `camera_id`, `resolution_type`, `reason` |
| `alert_resolution_escalated` | Tipo "incidente_tecnico" | idem + `reason` |
| `incident_escalate_clicked` | handleEscalateTechnical | `source: "alerts"`, `store_id`, `camera_id`, `event_id`, `reason` |
| `alert_rule_quality_viewed` | Mount de AlertRules | `store_id`, `rules_count`, `low_quality_rules` |
| `alert_rule_suggestion_shown` | useEffect por regra | `rule_id`, `suggestion_type`, `quality_level`, `quality_score` |
| `alert_rule_suggestion_applied` | handleApplySuggestion | `old_cooldown_minutes`, `new_cooldown_minutes` |
| `store_context_preserved` | storeId presente em Alerts | `store_id`, `from_route`, `to_route` |
| `store_context_missing_fallback` | storeId ausente | `from_route`, `store_id_present: false` |
