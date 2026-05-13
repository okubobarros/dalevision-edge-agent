# frontend-dashboard-operations — Contratos Externos

> Contratos entre o módulo de dashboard/operations e os endpoints de backend, serviços e APIs externas.

## 1. Store Dashboard

**Endpoint:** `GET /api/stores/<storeId>/dashboard/` (inferido)
**Chamada:** `storesService.getStoreDashboard(selectedStore)`
**Query Key:** `["store-dashboard", selectedStore]`
**staleTime:** 30s | **retry:** false
**Habilitado:** `canFetchAuth && !isNetworkMode && !isTrialCeoMode`

**Resposta esperada:** `StoreDashboard` (tipo de `types/dashboard.ts` — não lido)

---

## 2. Store Analytics Summary

**Endpoint:** `GET /api/stores/<storeId>/analytics/summary/` (inferido)
**Chamada:** `storesService.getStoreAnalyticsSummary(storeId, { period, bucket })`
**Query Key:** `["store-metrics-summary-dashboard", selectedStore]`
**staleTime:** 30s

**Params:**
```typescript
{
  period: "1d" | "7d" | "30d",  // networkPeriod === "day" → "1d"
  bucket: "hour"
}
```

**Resposta esperada:** `StoreAnalyticsSummary` — inclui métricas de fluxo, conversão, fila

---

## 3. Network Dashboard

**Endpoint:** `GET /api/stores/network/dashboard/` (inferido)
**Chamada:** `storesService.getNetworkDashboard()`
**Query Key:** `["network-dashboard-home"]` / `["network-dashboard"]`
**staleTime:** 30s

**Resposta esperada:** `NetworkDashboard`:
```typescript
{
  stores: Array<{
    id: string,
    name: string,
    status: string,          // "online" | "offline" | "degraded"
    conversion?: number,     // % de conversão
    alerts?: number,
  }>,
  total_stores: number,
  avg_conversion: number,
  target_conversion: number,
  total_revenue_at_risk: number,
}
```

---

## 4. Store Edge Status (com polling adaptativo)

**Endpoint:** `GET /api/stores/<storeId>/edge/status/` (inferido)
**Chamada:** `storesService.getStoreEdgeStatus(coverageStoreId)`
**Query Key:** `["store-edge-status", coverageStoreId]`
**Polling:** 15s (offline) ou 30s (online, wizard fechado) ou false (aba oculta)
**refetchOnWindowFocus:** "always" | **refetchOnReconnect:** true

**Resposta esperada:** `StoreEdgeStatus`:
```typescript
{
  connectivity_status?: "online" | "degraded" | "offline",
  online?: boolean,             // fallback boolean
  last_comm_at?: string,        // ISO 8601
  last_seen_at?: string,
  last_heartbeat_at?: string,
  last_heartbeat?: string,
  store_status_reason?: string, // "heartbeat_timeout" etc.
}
```

---

## 5. Store Activation Status

**Endpoint:** `GET /api/stores/<storeId>/edge/activation/` (inferido)
**Chamada:** `storesService.getStoreActivationStatus(coverageStoreId)`
**Query Key:** `["store-activation-status-dashboard", coverageStoreId]`
**staleTime:** 15s

**Resposta esperada:** `StoreActivationStatusResponse`:
```typescript
{
  device?: {
    device_key?: string,
    update_channel?: "stable" | "canary",
  },
  installed_version?: string,
}
```

---

## 6. Edge Release Latest

**Endpoint:** `GET /api/edge/release/latest/?channel=<channel>` (inferido)
**Chamada:** `storesService.getEdgeReleaseLatest(activationUpdateChannel)`
**Query Key:** `["edge-release-latest-dashboard", activationUpdateChannel]`
**staleTime:** 60s
**channel:** `"stable"` (padrão) ou `"canary"` (se `device.update_channel === "canary"`)

---

## 7. Request Edge Update

**Endpoint:** `POST /api/stores/<storeId>/edge/update/` (inferido)
**Chamada:** `storesService.requestStoreEdgeUpdate(coverageStoreId, payload)`
**Payload:**
```typescript
{
  device_key?: string,   // activationStatus?.device?.device_key
  force_update: true,
}
```

**Resposta esperada:**
```typescript
{
  requested: boolean,
  reason?: "already_up_to_date" | string,
  target_version?: string,
}
```

**Casos tratados:**
- `requested=false, reason="already_up_to_date"` → toast neutro "Agent já está atualizado"
- `requested=true` → toast success + `trackAgentEvent` + polling de versão instalada

---

## 8. Me Status

**Endpoint:** `GET /api/me/status/` (inferido)
**Chamada:** `meService.getStatus()`
**Query Key:** `["me-status-dashboard"]`
**staleTime:** 60s

**Resposta esperada:** `MeStatus`:
```typescript
{
  has_subscription: boolean,
  trial_active: boolean,
  is_internal_admin?: boolean,
}
```

---

## 9. CEO Dashboard (Trial Mode)

**Endpoint:** `GET /api/stores/<storeId>/ceo-dashboard/?period=<period>` (inferido)
**Chamada:** `storesService.getStoreCeoDashboard(selectedStore, { period: "day" })`
**Query Key:** `["store-ceo-dashboard", selectedStore, "day"]`
**Habilitado:** `canFetchAuth && isTrialCeoMode`
**staleTime:** 30s | **retry:** 1 (único com retry)

---

## 10. Copilot Daily Briefing

**Endpoint:** `GET /api/copilot/daily-briefing/?store_id=<id>` ou sem store_id para rede
**Chamada:** `copilotService.getDailyBriefing({ storeId? })`
**Query Key:** `["copilot-daily-briefing", isNetworkMode ? "network" : selectedStore]`
**staleTime:** 60s

---

## 11. Network Insights (OperationsTower)

**Endpoint:** `GET /api/copilot/network-insights/` (inferido)
**Chamada:** `copilotService.getNetworkInsights()`
**Query Key:** `["network-insights"]`
**staleTime:** 60s

**Resposta esperada:** array de objetos:
```typescript
{
  id: string,
  title: string,
  severity: "critical" | "warning",
  resolved: boolean,
  impact_label?: string,         // "R$ 1.200"
  recommended_action?: string,
  created_at: string,
  store_id: string,
}
```

---

## 12. Revenue Progress e Revenue Goal

**GET:** `salesService.getRevenueProgress(salesGoalMonth)`
**Query Key:** `["revenue-progress", selectedStore, salesGoalMonth]`
**staleTime:** 60s

**POST/PUT:** `salesService.saveRevenueGoal(payload)`
**Mutation:** invalida `["revenue-progress"]` e variações

---

## 13. Alerts Events (Queries + Mutations)

**GET:** `useAlertsEvents({ store_id?, status: "open" })`
**Query Key:** `["alerts-events", ...]`

**PATCH resolve:** `useResolveEvent()` → invalida alertas abertos
**PATCH ignore:** `useIgnoreEvent()` → invalida alertas abertos

---

## 14. Store Limits (Câmeras)

**Endpoint:** `GET /api/cameras/stores/<storeId>/limits/` (inferido)
**Chamada:** `camerasService.getStoreLimits(coverageStoreId)`
**Query Key:** `["store-limits", coverageStoreId]`

---

## 15. Network Vision (Ingestão e Confiança)

**Ingestão:** `storesService.getNetworkVisionIngestionSummary({ event_source, window_hours, event_type? })`
**Query Key:** `["network-vision-ingestion-summary-dashboard", networkIngestionEventType]`

**Confiança:** `storesService.getNetworkVisionConfidenceSummary({ window_hours: 24, limit: 200 })`
**Query Key:** `["network-vision-confidence-summary-dashboard"]`

Ambos habilitados apenas em modo rede (`isNetworkMode`).

---

## 16. Network Edge Rollout e Validation

**Rollout:** `storesService.getNetworkEdgeUpdateRolloutSummary(channel?)`
**Query Key:** `["network-edge-rollout-summary-dashboard", rolloutChannelFilter]`

**Validation:** `storesService.getNetworkEdgeUpdateValidationSummary({ channel?, hours: 72 })`
**Query Key:** `["network-edge-validation-summary-dashboard", rolloutChannelFilter]`

Ambos habilitados apenas em modo rede.

---

## 17. PDV Interest Registration

**Endpoint:** inferred via `storesService.registerPdvInterest()`
**Mutation:** invalida `["stores"]` e `["stores-summary"]`
**Trigger:** botão "Integrar PDV" no dashboard

---

## 18. Analytics Event (Agent Update)

**Chamada:** `analyticsService.trackAgentEvent({ store_id, event_type: "agent_update_triggered", device_key, from_version, to_version })`
**Modo:** fire-and-forget (`.catch(() => undefined)`)
**Origem:** `Dashboard.tsx:772-780`

---

## 19. Pipeline Observability (Admin only)

**Endpoint:** `adminService.getPipelineObservability({ window_hours: 24, store_id?, limit: 120 })`
**Query Key:** `["dashboard-pipeline-observability", ...]`
**Habilitado:** `canFetchAuth && isInternalAdmin`
