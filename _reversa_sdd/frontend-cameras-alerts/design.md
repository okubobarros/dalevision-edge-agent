# frontend-cameras-alerts — Design Técnico

## Interface

### Rotas

| Rota | Componente | Proteção | URL Params relevantes |
|------|-----------|----------|-----------------------|
| `/app/cameras` | `Cameras` | `PrivateRoute` | `?openEdgeSetup=1`, `?openRoi=1&zone_id=<id>`, `?onboarding=true`, `?action=<str>` |
| `/app/alerts` | `Alerts` | `PrivateRoute` | `?store_id=<id>`, `?event_id=<id>`, `?severity=<s>`, `?status=<s>`, `?from=<date>`, `?to=<date>` |
| `/app/alerts/rules` | `AlertRulesPage` | `PrivateRoute` | `?store_id=<id>` |

### Tipos principais

| Tipo | Campos-chave | Fonte |
|------|-------------|-------|
| `Camera` | `id`, `name`, `ip`, `rtsp_url_masked`, `status`, `zone_id`, `camera_health`, `last_error`, `error_reason` | `services/cameras.ts` |
| `LocalOnboardingBlueprint` | `ok`, `plan_code`, `camera_limit`, `candidates[]`, `selection_guidance` | Cameras.tsx:57 |
| `LocalOnboardingCandidate` | `ip`, `ports`, `confidence`, `status`, `reason_code`, `selectable`, `recommended` | Cameras.tsx:47 |
| `LocalReadinessReport` | `ok`, `status`, `summary`, `checks[]` | Cameras.tsx:75 |
| `CameraDiagnosis` | `cause`, `title`, `recommendedAction`, `reasonCode` | Cameras.tsx:228 |
| `AlertEvent` | `id`, `title`, `description`, `type`, `store_id`, `severity`, `status`, `occurred_at`, `camera_id`, `media[]`, `metadata` | Alerts.tsx:25 |
| `AlertRule` | `id`, `type`, `severity`, `cooldown_minutes`, `active`, `channels`, `threshold`, `store_id` | services/alerts.ts |
| `NotificationLog` | `id`, `rule_id`, `channel`, `status`, `sent_at`, `destination`, `error` | services/alerts.ts |
| `RuleQualitySnapshot` | `score`, `level`, `totalLogs`, `suppressionRate`, `failureRate`, `suggestion` | AlertRules.tsx:25 |

## Fluxo — Câmeras

### Fetch de câmeras (modo individual vs. rede)
```
selectedStore === "all":
  camerasService.getCameras() → se length > 0 → retorna
  else se stores.length > 0 → Promise.all(stores.map(s => getStoreCameras(s.id)))
  else → []

selectedStore !== "all":
  camerasService.getStoreCameras(selectedStore) → retorna câmeras da loja
```

### Diagnóstico de falha
```
diagnoseCameraFailure({ camera, realtimeReason, edgeOnline }):
  status ∈ [online, degraded] → null (saudável)
  rtspMissing || rawError.includes(credential/unauthorized/auth/senha/usuario) → "credencial"
  !edgeOnline || rawReason.includes(no_heartbeat/heartbeat_expired/stale_heartbeat) → "heartbeat"
  rawError.includes(timeout/network/unreachable/refused) → "conectividade"
  else → "stream"
```

### Fluxo de blueprint local (ONVIF)
```
1. GET http://127.0.0.1:8787/onboarding/blueprint → LocalOnboardingBlueprint
2. Usuário seleciona IPs (até selection_guidance.max_selectable)
3. resolveNextCreatePrefill(selectedIps, existingCameras) → CameraCreatePrefill
4. Modal de criação pré-preenchido com IP selecionado
5. Após createCamera bem-sucedido:
   - Remove IP criado de selectedBlueprintIps
   - Resolve próximo IP → se modo onboarding e há próximo → reabre modal com toast "Próxima câmera sugerida"
```

### Cache de ROI em localStorage
```
chave: "dv_roi_published_cameras_v1_<storeId>"
valor: JSON.stringify(string[])  // array de camera IDs

markLocalRoiPublished(cameraId):
  lê set atual → adiciona cameraId → serializa → localStorage.setItem

ao trocar loja:
  lê localStorage[chave nova] → atualiza localPublishedRoiCameraIds
```

### Status de conectividade de câmeras
```
edgeOnline:
  connectivity_status ∈ ["online", "degraded"] → true
  OR edgeStatus.online === true → true
  OR connectivity_age_seconds <= 120 → true
  else → false

cameraSourceSummary (via edgeStatus.camera_source_mode_detected):
  "api_first" → "backend sincronizado" (emerald)
  "local_only_or_unknown" + camera_sync_age_seconds <= 300 → "backend sincronizado (instável)" (amber)
  "local_only_or_unknown" + stale → "contingência local (.env)" (amber)
  else → "aguardando detecção" (gray)
```

## Fluxo — Alertas

### Filtros e query
```
eventsQuery = useAlertsEvents({
  store_id: storeId || undefined,
  status: statusFilter !== "all" ? statusFilter : undefined,
  severity: severityFilter !== "all" ? severityFilter : undefined,
  occurred_from: new Date(`${dateFrom}T00:00:00`).toISOString(),
  occurred_to:   new Date(`${dateTo}T23:59:59`).toISOString(),
})

filtered = events.filter(e =>
  (matchQuery: title, description, type, store_id) &&
  (matchSeverity: "all" || e.severity === severityFilter)
)
```

### Resolução de alerta
```
handleSubmitResolution():
  if (reasonRequired && !reason) → toast.error
  
  "resolvido_localmente":
    resolveMut.mutateAsync(eventId) → toast.success
  
  "delegado":
    delegateToWhatsapp(event, { reason }) → POST delegateEventEmail
    if ok: ignoreMut.mutateAsync(eventId) + toast.success
  
  "incidente_tecnico":
    ignoreMut.mutateAsync(eventId)
    trackJourneyEvent("alert_resolution_escalated")
    handleEscalateTechnical → window.location.assign(/app/edge-help?...)
  
  → trackJourneyEvent("alert_resolution_completed")
  → closeResolutionFlow + eventsQuery.refetch()
```

### SLA Timer dinâmico
```
setInterval(() => setNow(new Date()), 1000)  // atualiza a cada 1s

targetTime = new Date(occurred_at + 30min)
diff = targetTime - now
isOverdue = diff < 0
timeStr = HH:MM:SS (abs(diff))
```

## Fluxo — Regras de Alerta

### Qualidade da regra
```
buildRuleQuality(rule, logs):
  totalLogs = logs.length
  suppressionRate = suppressed / totalLogs  (0 se sem logs)
  failureRate = failed / totalLogs  (0 se sem logs)
  base = totalLogs === 0 ? 60 : 100
  score = clamp(base - suppressionRate×60 - failureRate×40, 0, 100)
  level = score >= 80 → "alto" | score >= 55 → "medio" | else → "baixo"

  suggestion:
    totalLogs >= 6 && suppressionRate >= 0.4 → increase_cooldown (nextCooldown = min(current+5, 120))
    totalLogs >= 6 && failureRate >= 0.2 && (email||whatsapp) → review_channels
    else → null
```

## Dependências

| Componente | Motivo | Como usa |
|-----------|--------|---------|
| `camerasService` | CRUD e limites de câmeras | `getCameras`, `getStoreCameras`, `getStoreLimits`, `createStoreCamera` |
| `storesService` | Edge status | `getStoreEdgeStatus` (polling 20-30s) |
| `onboardingService` | Progresso de onboarding | `getNextStep`, `getProgress` |
| `supportService` | Concessão de suporte | `getMyStoreSupportRequests`, `requestStoreSupport` |
| `alertsService` | CRUD alertas e regras | `listCoreStores`, `delegateEventEmail`, `listRules`, `createRule`, `updateRule`, `listLogs` |
| `useAlertsEvents` / `useAlertLogs` | Queries de alertas | via `queries/alerts.queries.ts` |
| `useResolveEvent` / `useIgnoreEvent` / `useIngestAlert` | Mutações de alertas | via `queries/alerts.queries.ts` |
| `trackJourneyEvent` | Analytics | múltiplos pontos: resolução, escalação, qualidade de regras |
| `CameraRoiEditor` | Editor de ROI de câmera | renderizado via `roiCamera` state |
| `StoreActivationWizard` | Wizard de ativação | aberto por `edgeSetupOpen` |
| `buildCopilotUrl` | Navegação contextual | link "Resolver com Copiloto" nos alertas |
| `AlertsModuleTabs` | Navegação entre tabs do módulo | Alerts + AlertRules compartilham componente |

## Decisões de Design

| Decisão | Evidência | Confiança |
|---------|-----------|-----------|
| ROI publicadas em localStorage (não server-state) | `Cameras.tsx:44,619` | 🟢 |
| Diagnóstico de câmera é função pura determinística no frontend (não backend) | `Cameras.tsx:235-301` | 🟢 |
| Qualidade de regra calculada inteiramente no frontend | `AlertRules.tsx:111-157` | 🟢 |
| SLA hardcoded em 30 minutos | `Alerts.tsx:757` | 🟢 |
| Câmeras em modo "all" usam fallback de merge por loja | `Cameras.tsx:441-460` | 🟢 |
| Blueprint local busca setup API em 127.0.0.1:8787 (não configurável) | `Cameras.tsx:45` | 🟢 |
| Delegação de alerta via e-mail (não WhatsApp direto) | `Alerts.tsx:294` — `delegateEventEmail` | 🟢 |
| `normalizeArray` por 3 formatos de resposta de backend | `Alerts.tsx:67-78` — adaptação defensiva | 🟢 |
| Support grant estende `canManageStore` sem alterar o papel do usuário | `Cameras.tsx:592` | 🟢 |
| `isDev` usado para ocultar botão de simulação em produção | `Alerts.tsx:223` — `import.meta.env.DEV` | 🟢 |

## Estado Interno

### `Cameras`
```
edgeSetupOpen: boolean
cameraModalOpen: boolean          → modal de criar/editar câmera
editingCamera: Camera | null
roiCamera: Camera | null          → câmera com ROI editor aberto
localPublishedRoiCameraIds: Set<string>
testingCameraId: string | null
testCooldownCameraId: string | null
localBlueprint: LocalOnboardingBlueprint | null
selectedBlueprintIps: string[]
localReadiness: LocalReadinessReport | null
localSetupHealth: LocalSetupApiHealth | null
createPrefill: CameraCreatePrefill | null
streamingCamera: Camera | null
showUpgradeCta: boolean
connectionHelpOpen: boolean
```

### `Alerts`
```
query: string                    → busca de texto livre
severityFilter: FilterSeverity   → all|critical|warning|info
statusFilter: FilterStatus       → open|resolved|ignored|all
storeId: string                  → loja selecionada (de ?store_id)
selectedEventId: string | null   → alerta selecionado no drawer
delegatingEventId: string | null → alerta sendo delegado
resolutionTarget: AlertEvent | null
resolutionType: AlertResolutionType
resolutionReason: string
dateFrom: string                 → date input YYYY-MM-DD
dateTo: string                   → date input YYYY-MM-DD
now: Date                        → atualizado a cada 1s (SLA timer)
```

### `AlertRulesPage`
```
storeIdOverride: string | null   → loja selecionada manualmente
type: string                     → evento monitorado
severity: Severity
cooldown: number                 → padrão 15min
active: boolean
channels: { dashboard, email, whatsapp }
showCreate: boolean
createError: RuleCreateErrorInfo | null
applyingRuleId: string | null
```

## Observabilidade

- `trackJourneyEvent("alert_resolution_completed")` — toda resolução 🟢
- `trackJourneyEvent("incident_escalate_clicked")` — toda escalação técnica 🟢
- `trackJourneyEvent("alert_rule_quality_viewed")` — montagem da página de regras 🟢
- `trackJourneyEvent("alert_rule_suggestion_shown")` — sugestão exibida por regra 🟢
- `trackJourneyEvent("alert_rule_suggestion_applied")` — aplicação de sugestão 🟢
- `trackJourneyEvent("store_context_preserved")` — storeId presente em alertas 🟢
- `trackJourneyEvent("store_context_missing_fallback")` — storeId ausente (apenas uma vez) 🟢

## Riscos e Lacunas

- 🔴 **`CameraRoiEditor` não foi lido** — comportamento interno do editor de ROI é lacuna
- 🔴 **`camerasService` não foi lido** — campos exatos de `Camera`, `CreateCameraPayload` e método de teste RTSP não confirmados
- 🔴 **`useAlertsEvents` e hooks de alertas não foram lidos** — formato de `queryKey`, invalidação e refetch não confirmados
- 🟡 **Blueprint local aponta para `127.0.0.1:8787` hardcoded** — sem fallback para outros IPs do setup API
- 🟡 **SLA de 30 minutos hardcoded** — sem configuração por loja ou tipo de alerta
- 🟡 **`delegateEventEmail` retorna `employee.name`** — se funcionário sem e-mail vinculado, erro é mensagem longa sobre "vincule um e-mail"
- 🟡 **`checklistSnapshotRef` e `checklistCompletedEventSentRef`** — lógica de onboarding checklist parcialmente visível mas não totalmente documentada
