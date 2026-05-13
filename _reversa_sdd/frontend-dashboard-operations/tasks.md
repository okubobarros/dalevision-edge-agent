# frontend-dashboard-operations — Tarefas de Implementação

## Pré-requisitos
- [ ] `AuthContext` implementado e `authReady`, `isAuthenticated` disponíveis
- [ ] `StoreContext` implementado com `selectedStoreId`, `stores`, `isLoading`, `hasError`
- [ ] `@tanstack/react-query` configurado com `QueryClientProvider`
- [ ] `react-hot-toast` configurado com `Toaster`
- [ ] `recharts` instalado
- [ ] Todos os services (`storesService`, `copilotService`, `meService`, `salesService`, `analyticsService`, `adminService`, `camerasService`) implementados

## Tarefas

### Core — getDashboardExperience

- [ ] T-01 — Implementar `deriveAccountState(meStatus, stores)` com prioridade meStatus > stores.status
  - Origem no legado: `frontend/src/pages/Dashboard/dashboardExperience.ts:38-57`
  - Critério de pronto: retorna `plan_active` se `has_subscription`; `trial_active` se `trial_active=true`; `trial_expired` se trial=false sem assinatura ou loja com blocked+trial_expired
  - Confiança: 🟢

- [ ] T-02 — Implementar `deriveStoreState({ selectedStore, edgeStatus, onboarding, hasOperationalData, camerasOnline })`
  - Origem no legado: `frontend/src/pages/Dashboard/dashboardExperience.ts:59-88`
  - Critério de pronto: `technical_incident` se heartbeat/timeout no store_status_reason; cascata: not_connected → connected_no_capture → collecting → operational
  - Confiança: 🟢

- [ ] T-03 — Implementar `getDashboardExperience()` compondo os dois derivadores acima
  - Origem no legado: `frontend/src/pages/Dashboard/dashboardExperience.ts:90-148`
  - Critério de pronto: retorna `{ dashboardType, accountState, networkState, storeState, reasons }` corretamente para todos os cenários
  - Confiança: 🟢

### Core — Dashboard

- [ ] T-04 — Implementar utilitários de formatação e conectividade
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:53-210`
  - Critério de pronto: `isRecentTimestamp`, `getConnectivityStatus`, `getLastSeenAt`, `formatRelativeTime`, `formatTimestampShort`, `formatLastSeenDisplay`, `formatCurrencyBRL`, `formatMetricNumber`, `formatRatioPercent`, `normalizePlanCode`, `parseMaybeNumber` implementados com cobertura de casos pt-BR
  - Confiança: 🟢

- [ ] T-05 — Implementar `estimateRevenueGapFromOperations({ avgQueueSeconds, avgVisitorsPerHour, avgTicketBRL })`
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:169-188`
  - Critério de pronto: `queueAbandonRate = max(0, min(35%, (queue-180)/1200))`; `lostCustomers = round(visitors × abandonRate × 8h)`; `revenueGap = lostCustomers × ticket`
  - Confiança: 🟢

- [ ] T-06 — Implementar `readEdgeSetupHandoff()` e `persistEdgeSetupHandoff(storeId)` com TTL de 45s
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:113-143`
  - Critério de pronto: handoff lido de sessionStorage; expirado após 45s é removido e retorna null; gravado com `created_at: Date.now()`
  - Confiança: 🟢

- [ ] T-07 — Implementar `PLAN_CAMERA_LIMITS` e `normalizePlanCode`
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:200-221`
  - Critério de pronto: `trial/free/start/basic/paid → 3`; `pro → 12`; `growth/enterprise → null`
  - Confiança: 🟢

- [ ] T-08 — Implementar React Query stack do Dashboard (todas as queries)
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:400-730`
  - Critério de pronto: todas as queries com `enabled: canFetchAuth`, `staleTime`, `retry: false`; modo rede ativa/desativa corretamente as queries de network vs. individual
  - Confiança: 🟢

- [ ] T-09 — Implementar lógica de redirect para onboarding com grace period
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:453-464`
  - Critério de pronto: `stores.length === 0 && !hasKnownStore && !suppressOnboardingRedirect` → `navigate("/onboarding")`; grace period 45s via sessionStorage
  - Confiança: 🟢

- [ ] T-10 — Implementar detecção de URL params `?openEdgeSetup=1` e `?activation_success=true`
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:352-395`
  - Critério de pronto: wizard abre automaticamente; toast de sucesso disparado; queries de edge status invalidadas
  - Confiança: 🟢

- [ ] T-11 — Implementar polling adaptativo de `edgeStatus`
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:634-657`
  - Critério de pronto: 15s quando offline; 30s quando online e wizard fechado; 15s quando wizard aberto; pausa quando aba oculta
  - Confiança: 🟢

- [ ] T-12 — Implementar mutação `requestEdgeUpdate` com monitoring de versão instalada
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:759-810`
  - Critério de pronto: mutação chama `requestStoreEdgeUpdate`; polling detecta `installed_version === target_version`; toast de conclusão + `trackAgentEvent`
  - Confiança: 🟢

- [ ] T-13 — Implementar mutação `saveRevenueGoal` e `savePdvInterest`
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:408-440`
  - Critério de pronto: toast de sucesso; invalidação de queries relacionadas; toast de erro com mensagem do backend
  - Confiança: 🟢

- [ ] T-14 — Implementar seletor de loja com modo rede (ALL_STORES_VALUE)
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:223,442-715`
  - Critério de pronto: troca de loja recarrega todos os widgets; modo "all" habilita queries de rede; `coverageStoreId` calculado corretamente
  - Confiança: 🟢

### Views do Dashboard

- [ ] T-15 — Implementar `PaidExecutiveDashboardView` com KPIs primários, secundários e gráfico de fluxo
  - Origem no legado: `frontend/src/pages/Dashboard/views/PaidExecutiveDashboardView.tsx`
  - Critério de pronto: 4 KPIs primários com TrustBadge; 3 KPIs secundários; BarChart Recharts com `flowSeries`; IntelligenceFeedPanel na sidebar
  - Confiança: 🟢

- [ ] T-16 — Implementar `TrialDashboardView`
  - Origem no legado: `frontend/src/pages/Dashboard/views/TrialDashboardView.tsx` (🟡 não lido)
  - Critério de pronto: exibe conteúdo adequado para usuário em trial ativo ou expirado
  - Confiança: 🟡

- [ ] T-17 — Implementar `PaidSetupDashboardView`
  - Origem no legado: `frontend/src/pages/Dashboard/views/PaidSetupDashboardView.tsx` (🟡 não lido)
  - Critério de pronto: guia de configuração para plano pago sem edge conectado
  - Confiança: 🟡

- [ ] T-18 — Implementar `DashboardKpiStrip`, `InfrastructureSection`, `AlertsSection`
  - Origem no legado: `frontend/src/pages/Dashboard/views/` (🟡 não lidos)
  - Critério de pronto: strips e seções renderizados com dados das queries
  - Confiança: 🟡

- [ ] T-19 — Implementar `GovernanceBadge` e `TrustBadge` com estilos por status
  - Origem no legado: `frontend/src/pages/Dashboard/Dashboard.tsx:237-311`
  - Critério de pronto: `official` (emerald), `proxy` (amber), `estimated` (slate); `auditable` (indigo) no PaidExecutiveDashboardView
  - Confiança: 🟢

### OperationsTower

- [ ] T-20 — Implementar `OperationsTower` com KPIs globais e fila de intervenção
  - Origem no legado: `frontend/src/pages/Operations/OperationsTower.tsx:55-418`
  - Critério de pronto: 4 GlobalKpis; fila com severidade crítica primeiro; mensagem de vazio "Fluxo Operacional Saudável"
  - Confiança: 🟢

- [ ] T-21 — Implementar Pulso das Lojas (ranking) e Staff Gap
  - Origem no legado: `frontend/src/pages/Operations/OperationsTower.tsx:103-366`
  - Critério de pronto: `best` (conversão ≥ meta), `worsening` (< meta), navegação para detalhes de loja; Staff Gap com avatares e gap visual
  - Confiança: 🟢

- [ ] T-22 — Implementar Copilot Panel na OperationsTower com link contextual
  - Origem no legado: `frontend/src/pages/Operations/OperationsTower.tsx:367-390`
  - Critério de pronto: botão navega para copilot com prompt "Gerar plano de ação para subcobertura na rede hoje."
  - Confiança: 🟡 (texto hardcoded — a integrar com API real futuramente)

## Tarefas de Teste

- [ ] TT-01 — Teste de `getDashboardExperience`: todos os cenários de accountState × storeState
- [ ] TT-02 — Teste de `estimateRevenueGapFromOperations`: queue=0 (sem risco), queue=600s (alto risco), valores negativos
- [ ] TT-03 — Teste de redirect para onboarding: stores=[], suppressOnboardingRedirect=false → navigate chamado
- [ ] TT-04 — Teste de grace period: sessionStorage com completed_at recente → suppressOnboardingRedirect=true → sem redirect
- [ ] TT-05 — Teste de `readEdgeSetupHandoff`: TTL expirado → null; TTL válido → { storeId, createdAt }
- [ ] TT-06 — Teste de polling adaptativo: aba oculta → `refetchInterval` retorna false
- [ ] TT-07 — Teste de URL params: `?openEdgeSetup=1` → `edgeSetupOpen=true`; `?activation_success=true` → toast disparado
- [ ] TT-08 — Teste de `normalizePlanCode`: trial/free → "trial"; enterprise/entreprise → "enterprise"
- [ ] TT-09 — Teste de OperationsTower interventions: filtragem por severity, ordenação críticas primeiro
- [ ] TT-10 — Teste de storeRanking: lojas acima e abaixo da meta de conversão

## Ordem Sugerida
1. T-01 a T-07 (utilitários e lógica pura) — sem dependências externas, fáceis de testar
2. T-08 (React Query stack) — depende de todos os services implementados
3. T-09, T-10 (comportamentos de redirect e URL params) — dependem de T-08
4. T-11, T-12, T-13, T-14 (polling, mutações, seletor) — dependem de T-08
5. T-15 a T-19 (views) — dependem de T-08, T-14
6. T-20 a T-22 (OperationsTower) — independente, pode ser paralelo a T-15+

## Lacunas Pendentes (🔴)
- `StoreContext` precisa ser lido antes de T-08 (gerenciamento de selectedStoreId, stores, cache)
- `TrialDashboardView` e `PaidSetupDashboardView` precisam ser lidos antes de T-16 e T-17
- `InfrastructureSection`, `AlertsSection`, `EdgeActivationChecklist`, `DashboardHeroSection`, `OperationalDiagnosisSection` precisam ser lidos antes de T-18
- `buildCopilotUrl` precisa ser analisado antes de T-22 (T-14, T-20)
- Copilot panel da OperationsTower usa texto hardcoded — decisão de produto necessária sobre quando usar API dinâmica
- Staff Gap usa dados simulados (`scheduled = 4`, cálculo por `store.alerts`) — requer spec de escala real
