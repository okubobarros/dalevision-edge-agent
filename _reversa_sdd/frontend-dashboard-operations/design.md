# frontend-dashboard-operations — Design Técnico

## Interface

### Rotas

| Rota | Componente | Proteção | Descrição |
|------|-----------|----------|-----------|
| `/app/dashboard` | `Dashboard` | `PrivateRoute` | Hub principal; redireciona para /onboarding se sem lojas |
| `/app/operations` | `OperationsTower` | `PrivateRoute` | Torre de controle da rede (visão multi-loja) |
| `/app/operations/stores` | `Stores` | `PrivateRoute` | Listagem de lojas (outro módulo) |
| `/app/operations/stores/:storeId` | `StoreDetails` | `PrivateRoute` | Detalhes de loja (outro módulo) |

### URL Params do Dashboard

| Param | Valor | Efeito |
|-------|-------|--------|
| `?openEdgeSetup=1` | string | Abre `StoreActivationWizard` automaticamente |
| `?activation_success=true` | string | Dispara toast e invalida cache de edge status |
| `?store_id=<id>` | string | Pré-seleciona loja no handoff do onboarding |

### Tipos principais

| Tipo | Campos-chave | Fonte |
|------|-------------|-------|
| `DashboardExperience` | `dashboardType`, `accountState`, `networkState`, `storeState`, `reasons` | `dashboardExperience.ts` |
| `AccountState` | `trial_active`, `trial_expired`, `plan_active`, `unknown` | `dashboardExperience.ts` |
| `StoreOperationalState` | `not_connected`, `connected_no_capture`, `collecting`, `operational`, `technical_incident` | `dashboardExperience.ts` |
| `StoreEdgeStatus` | `connectivity_status`, `online`, `last_comm_at`, `last_heartbeat_at`, `store_status_reason` | `services/stores.ts` |
| `StoreSummary` | `id`, `name`, `status`, `role`, `last_seen_at`, `blocked_reason`, `trial_ends_at`, `conversion` | `services/stores.ts` |
| `NetworkDashboard` | `stores[]`, `total_stores`, `avg_conversion`, `target_conversion`, `total_revenue_at_risk` | `services/stores.ts` |

## Fluxo Principal — Dashboard

1. `Dashboard` monta; lê `authReady && isAuthenticated` do `AuthContext`
2. `StoreContext` fornece `selectedStore`, `stores`, `storesLoading`
3. `canFetchAuth = authReady && isAuthenticated` habilita todas as queries React Query
4. Paralelo: busca `storeDashboard`, `metricsSummary`, `networkDashboard`, `meStatus`, `events`, `edgeStatus`, `activationStatus`, `dailyBriefing`, `revenueProgress`, `storeValueLedger`
5. Verifica URL params (`openEdgeSetup`, `activation_success`) no mount via `useEffect`
6. Verifica `dv_edge_setup_handoff_v1` em sessionStorage para handoff de onboarding
7. `getDashboardExperience()` determina `dashboardType` com base em todos os dados
8. Renderiza o componente de view adequado (Trial / PaidSetup / PaidExecutive)
9. Polling de `edgeStatus` com intervalo adaptativo (15s/30s baseado em estado e visibilidade)

## Fluxo — getDashboardExperience()

```
Input:
  meStatus, stores, selectedStore, edgeStatus, onboarding, hasOperationalData, camerasOnline

deriveAccountState():
  meStatus.has_subscription     → plan_active
  meStatus.trial_active = true  → trial_active
  meStatus.trial_active = false && !has_subscription → trial_expired
  stores com blocked + trial_expired → trial_expired
  stores com status = "trial" → trial_active
  else → unknown

deriveStoreState():
  heartbeat/timeout no store_status_reason → technical_incident
  !isConnected → not_connected
  camerasOnline <= 0 → connected_no_capture
  !hasOperationalData || onboarding.stage = "collecting_data" → collecting
  else → operational

dashboardType:
  trial_active → "trial"
  plan_active + storeState = "operational" → "paid_executive"
  plan_active + outros → "paid_setup"
  trial_expired → "trial"
  storeState = "operational" (fallback) → "paid_executive"
  else → "paid_setup"
```

## Fluxo — Redirect para Onboarding

```
useEffect:
  if (!canFetchAuth || storesLoading || storesHasError || !stores) return
  if (stores.length === 0 && !hasKnownStore && !suppressOnboardingRedirect):
    navigate("/onboarding", { replace: true })

suppressOnboardingRedirect:
  sessionStorage["dv_onboarding_just_completed"] existe?
    payload.at + 45000 > Date.now() → true (suprime)
    else → false
```

## Fluxo — Edge Setup Handoff

```
readEdgeSetupHandoff():
  sessionStorage["dv_edge_setup_handoff_v1"] existe?
    TTL: Date.now() - created_at <= 45000ms → retorna { storeId, createdAt }
    else → remove e retorna null

persistEdgeSetupHandoff(storeId):
  sessionStorage["dv_edge_setup_handoff_v1"] = { store_id, created_at: Date.now() }
```

## Fluxo — Polling adaptativo do Edge Status

```
refetchInterval: (query) =>
  document.visibilityState === "hidden" → false (pause)
  query.state.status !== "success" → 15000ms
  !data?.online → 15000ms
  edgeSetupOpen → 15000ms
  else → 30000ms
```

## Fluxo — OperationsTower

1. Busca `networkDashboard` via `getNetworkDashboard()` (staleTime 30s)
2. Busca `insights` via `copilotService.getNetworkInsights()` (staleTime 60s)
3. Deriva `interventions`: filtra `severity in [critical, warning]` + `!resolved`, mapeia para `Intervention`, ordena críticas primeiro
4. Deriva `storeRanking`: `best` = conversão ≥ meta (top 3); `worsening` = conversão < meta (bottom 3); `offline` = status = "offline"
5. Calcula `networkHealthPercent = round(onlineStores / totalStores × 100)`
6. Renderiza: Header → KPIs Globais → Fila de Intervenção (col-span-2) + Pulso das Lojas + Staff Gap + Copilot Panel

## Fluxos Alternativos

- **Trial expirado (trialBlockedStore):** `StoreActivationWizard` pode exibir callout de upgrade; `isTrialBlocked = true`
- **Modo rede (ALL_STORES_VALUE):** desativa `storeDashboard`, `metricsSummary`; ativa `networkIngestionSummary`, `networkVisionConfidenceSummary`, `networkCoverageSummary`, `networkRolloutSummary`, `networkValidationSummary`
- **Admin interno (isInternalAdmin):** ativa query de `pipelineObservability` para debug de pipeline de visão
- **Update do edge agent:** `requestEdgeUpdate` mutação → polling de `activationStatus.installed_version` até igualar `pendingUpdateTargetVersion`; toast de conclusão + analytics
- **Modo TrialCeo (isTrialCeoMode):** `selectedStore !== ALL_STORES_VALUE && selectedStoreStatus === "trial"` → busca `ceoDashboard` em vez de `dashboard`

## Dependências

| Componente | Motivo | Como usa |
|-----------|--------|---------|
| `@tanstack/react-query` | Fetching e cache | `useQuery`, `useQueries`, `useMutation`, `useQueryClient` |
| `StoreContext` | Estado global da loja selecionada | `selectedStoreId`, `setSelectedStoreId`, `stores` |
| `AuthContext` | Proteção de queries | `canFetchAuth = authReady && isAuthenticated` |
| `storesService` | Dados de loja/rede | 12+ endpoints (dashboard, edge status, analytics, rollout, etc.) |
| `camerasService` | Limites de câmeras | `getStoreLimits(storeId)` |
| `alertsService` / `useAlertsEvents` | Alertas abertos | `useAlertsEvents`, `useResolveEvent`, `useIgnoreEvent` |
| `copilotService` | Briefing e network insights | `getDailyBriefing`, `getNetworkInsights`, `getValueLedgerDaily` |
| `meService` | Status do usuário e relatórios | `getStatus`, `getReportSummary`, `getProductivityCoverage` |
| `salesService` | Progresso de receita e metas | `getRevenueProgress`, `saveRevenueGoal` |
| `adminService` | Pipeline observability (admin only) | `getPipelineObservability` |
| `analyticsService` | Tracking de eventos | `trackAgentEvent` (update do agent) |
| `StoreActivationWizard` | Modal de ativação do edge agent | Renderizado condicionalmente por `edgeSetupOpen` |
| `IntelligenceFeedPanel` | Feed de inteligência em tempo real | Sidebar do PaidExecutiveDashboardView |
| `react-hot-toast` | Feedback de ações | `toast.success`, `toast.error`, `toast` |
| `recharts` | Gráfico de fluxo | `BarChart`, `Bar`, `Cell`, `Tooltip`, `ResponsiveContainer` |
| `buildCopilotUrl` | URL do copilot com prompt | Navegação contextual para o copilot |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------| 
| Três experiências de dashboard mutuamente exclusivas determinadas por função pura | `dashboardExperience.ts:90` — `getDashboardExperience` é função pura sem side-effects | 🟢 |
| Estado da conta prioriza `meStatus` sobre status de lojas (meStatus tem precedência) | `dashboardExperience.ts:42-51` | 🟢 |
| Grace period de onboarding (45s) para evitar redirect imediato após conclusão | `Dashboard.tsx:54-379` | 🟢 |
| Polling adaptativo de edge status (não WebSocket) | `Dashboard.tsx:641-656` — sem uso de `socket.io` ou `EventSource` | 🟢 |
| `retry: false` em todas as queries — falha silenciosa preferida a loading infinito | `Dashboard.tsx:405,479,491` | 🟢 |
| `coverageStoreId`: loja selecionada, ou única loja da rede, ou null em modo multi-loja com várias lojas | `Dashboard.tsx:446-451` | 🟢 |
| Revenue e risk calculados no frontend por algoritmo próprio (não via API) | `Dashboard.tsx:169-188` — `estimateRevenueGapFromOperations` | 🟢 |
| Copilot panel com texto hardcoded (insight de escalas) na OperationsTower | `OperationsTower.tsx:378-381` — string fixa, não dinâmica | 🟡 |
| PDV integration via WhatsApp em vez de integração nativa direta | `PaidExecutiveDashboardView.tsx:426` | 🟢 |

## Estado Interno

### `Dashboard`
```
edgeSetupOpen: boolean              → controla StoreActivationWizard
edgeSetupHandoffStoreId: string|null → storeId do handoff de onboarding
networkPeriod: "day"|"7d"|"30d"    → período para queries de network
networkIngestionEventType: string  → filtro de tipo de evento de ingestão
rolloutChannelFilter: "all"|"stable"|"canary" → filtro de canal de rollout
salesGoalMonth: string             → mês YYYY-MM para meta de receita
pendingUpdateTargetVersion: string|null → versão alvo do update em progresso
showValueOnboarding: boolean       → mostra OperationalOnboardingChecklist
resolvingEventId: string|null      → alerta sendo resolvido
ignoringEventId: string|null       → alerta sendo ignorado
delegatingEventId: string|null     → alerta sendo delegado
rolloutActionStoreId: string|null  → loja com rollout em andamento
```

### `OperationsTower`
```
mounted: boolean  → controla animação de entrada (opacity + translate-y)
```

## Observabilidade

- `toast.success("Agente Local Conectado com Sucesso!")` após `activation_success=true` 🟢
- `toast.success("Update iniciado. O agent deve reiniciar em ~2 minutos.")` 🟢
- `toast.success("Meta mensal salva com sucesso.")` 🟢
- `toast.error(message)` em todos os erros de mutação 🟢
- `analyticsService.trackAgentEvent("agent_update_triggered", {...})` quando update solicitado 🟢
- Sem métricas de performance ou traces de rendering distribuídos 🔴

## Riscos e Lacunas

- 🔴 **`StoreContext` não foi lido** — gerenciamento de `selectedStoreId`, `stores`, `isLoading`, `hasError` é crítico mas não documentado diretamente
- 🔴 **`TrialDashboardView` e `PaidSetupDashboardView` não foram lidos** — comportamento dessas views é lacuna significativa
- 🔴 **`InfrastructureSection` e `AlertsSection` não foram lidos** — componentes de infra e alertas do dashboard não documentados
- 🟡 **Copilot panel na OperationsTower tem texto hardcoded** — insight de "Anomalia nas Escalas de Tarde" é string fixa, não dados reais da API
- 🟡 **Staff Gap na OperationsTower usa dados simulados** — `scheduled = 4` e cálculo de `present` baseado em `store.alerts` é heurística, não dado real de escala
- 🟡 **Revenue estimado por algoritmo frontend** — `estimateRevenueGapFromOperations` usa constantes (8h/dia, ramp linear) que podem não refletir realidade do negócio
- 🔴 **`buildCopilotUrl` não foi analisado** — formato da URL e parâmetros do copilot são lacuna
- 🟡 **`isInternalAdmin` baseado em `meStatus.is_internal_admin`** — campo não documentado no tipo; pode ter comportamento diferente em prod
