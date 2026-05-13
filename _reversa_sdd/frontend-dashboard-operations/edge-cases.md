# frontend-dashboard-operations — Casos de Borda

## CE-01 — Grace period de onboarding evita redirect imediato

**Contexto:** Usuário conclui onboarding, é redirecionado para `/app/dashboard?openEdgeSetup=1&store_id=X`, mas o backend ainda não retornou as lojas

**Comportamento:**
```
suppressOnboardingRedirect:
  sessionStorage["dv_onboarding_just_completed"].at + 45000 > Date.now() → true
  → stores.length === 0 NÃO dispara redirect para /onboarding
```

**Resultado:** usuário não é jogado de volta ao onboarding nos primeiros 45s 🟢

**Risco:** 🟡 Se o backend demorar mais que 45s para criar a loja no backend, o redirect dispara mesmo assim

---

## CE-02 — Edge Setup Handoff com TTL expirado

**Contexto:** Usuário abre o dashboard 50s após o handoff ter sido gravado no sessionStorage

**Comportamento:**
```
readEdgeSetupHandoff():
  Date.now() - createdAt > 45000ms → remove sessionStorage + return null
  → initialOpenEdgeSetup = false
  → edgeSetupOpen começa como false
```

**Resultado:** wizard NÃO abre automaticamente se handoff estiver expirado 🟢

---

## CE-03 — `activation_success=true` na URL sem loja selecionada

**Contexto:** URL `?activation_success=true` chega sem `store_id` no handoff

**Comportamento:**
- Toast é exibido independentemente
- `queryClient.invalidateQueries({ queryKey: ["store-edge-status"] })` invalida todas as variações da key
- `edgeSetupHandoffStoreId` permanece null; wizard abre sem store pré-selecionada

**Risco:** 🟡 Wizard pode abrir sem contexto de loja se o handoff expirou

---

## CE-04 — Modo rede com uma única loja

**Contexto:** Usuário tem apenas uma loja; seleciona "Todas as Lojas"

**Comportamento:**
```
coverageStoreId = useMemo(() => {
  if (selectedStore !== ALL_STORES_VALUE) return selectedStore
  const items = stores ?? []
  if (items.length === 1) return items[0].id  // ← coverage para loja única
  return null
}, [selectedStore, stores])
```

**Resultado:** queries de edge status e activation continuam sendo feitas para a única loja mesmo em modo rede 🟢

---

## CE-05 — `connectivityStatus` com valor inesperado do backend

**Contexto:** Backend retorna `connectivity_status: "unknown"` ou string não mapeada

**Comportamento:**
```
getConnectivityStatus():
  value = "unknown" → não é "online", "degraded", "offline"
  typeof status?.online → se boolean, usa isso como fallback
  else → retorna "offline"
```

**Resultado:** fallback para "offline" em caso de valor inesperado 🟢

---

## CE-06 — Revenue gap com queue < 180s (fila dentro do SLA)

**Contexto:** `avgQueueSeconds = 90s` — abaixo do threshold de 180s

**Comportamento:**
```
queueAbandonRate = max(0, min(0.35, (90 - 180) / 1200))
                 = max(0, min(0.35, -0.075))
                 = max(0, -0.075)
                 = 0
lostCustomers = 0
revenueGap = 0
```

**Resultado:** sem risco calculado quando fila está dentro do SLA 🟢

---

## CE-07 — Update do edge agent: já está na versão mais recente

**Contexto:** Usuário clica em "Atualizar Agent" mas agent já está na versão alvo

**Comportamento:**
```
requestEdgeUpdate:
  response: { requested: false, reason: "already_up_to_date" }
  → toast("Agent já está atualizado para a versão alvo.")
  → setPendingUpdateTargetVersion não chamado (null permanece)
```

**Resultado:** sem toast de error; mensagem neutra informativa 🟢

---

## CE-08 — Update do edge agent: polling detecta conclusão

**Contexto:** Update iniciado; `pendingUpdateTargetVersion = "v1.3.5"`; polling de activationStatus em andamento

**Comportamento:**
```
useEffect:
  if (!coverageStoreId || !pendingUpdateTargetVersion) return
  installed = activationStatus?.installed_version → "v1.3.5"
  target = pendingUpdateTargetVersion → "v1.3.5"
  installed === target → setPendingUpdateTargetVersion(null) + toast success
```

**Risco:** 🟡 Se installed_version format difere (ex: "1.3.5" vs "v1.3.5"), comparação falha — polling nunca conclui

---

## CE-09 — `isTrialCeoMode` vs. modo rede

**Contexto:** Usuário seleciona "Todas as Lojas" quando alguma loja está em trial

**Comportamento:**
```
isTrialCeoMode = selectedStore !== ALL_STORES_VALUE && selectedStoreStatus === "trial"
             = false (porque selectedStore === ALL_STORES_VALUE)
→ ceoDashboard query disabled
→ storeDashboard query: enabled = canFetchAuth && !isNetworkMode && !isTrialCeoMode
                        = false (isNetworkMode = true)
```

**Resultado:** em modo rede, nenhum dashboard de loja individual é buscado 🟢

---

## CE-10 — `storesOnlineCount` / `storesOfflineCount` com dados conflitantes

**Contexto:** `networkDashboard.stores` tem status operacional diferente do `stores` lista (dados de fontes distintas)

**Comportamento:**
```
storesOnlineCount:
  networkRows = networkDashboard?.stores ?? []
  fromOperationalStatus = filtro por status "online"|"degraded"
  if (fromOperationalStatus > 0) return fromOperationalStatus  // prioridade networkDashboard
  else fallback para stores list com status "active"|"trial"
```

**Resultado:** `networkDashboard` tem prioridade quando tem dados; fallback para lista de lojas 🟢

---

## CE-11 — Intervenção sem `impact_label` na fila da OperationsTower

**Contexto:** Insight do copilot sem campo `impact_label`

**Comportamento:**
```
impact: insight.impact_label || "R$ 0"
```

**Resultado:** exibe "R$ 0" como placeholder; não quebra o componente 🟢

---

## CE-12 — OperationsTower: `total_stores = 0`

**Contexto:** `networkDashboard` retorna `total_stores = 0` (edge case de conta vazia)

**Comportamento:**
```
const totalStoresCount = networkDashboard?.total_stores || 1  // fallback para 1
networkHealthPercent = round(onlineStores / 1 × 100)
```

**Resultado:** divisão por zero evitada via `|| 1` 🟢

---

## CE-13 — `canManageStore` para usuário viewer/support

**Contexto:** Usuário com `role = "viewer"` tenta acessar ações de gestão

**Comportamento:**
```
selectedStoreRole = selectedStoreItem?.role ?? null
canManageStore = selectedStoreRole
  ? ["owner", "admin", "manager"].includes(selectedStoreRole)
  : true  // ← padrão permissivo quando role é null
```

**Risco:** 🔴 Quando `selectedStoreRole` é `null` (loja não encontrada ou `role` ausente), `canManageStore = true` — acesso permissivo inesperado

---

## CE-14 — Múltiplos `useEffect` na montagem do Dashboard (race)

**Contexto:** Quatro useEffects rodam em paralelo na montagem: grace period, handoff, store-load redirect, activation_success

**Comportamento:**
- Todos têm guards específicos (`if (!canFetchAuth || ...)`)
- `initialRouteHandledRef` existe mas seu uso completo não foi lido (linha 360)
- React 18 StrictMode pode causar execução dupla dos effects

**Risco:** 🟡 Race entre `navigate("/onboarding")` e abertura do wizard se ambas as condições existirem simultaneamente — `initialRouteHandledRef` pode mitigar mas não foi confirmado

---

## CE-15 — `filterDashboardByStoreStatus` com loja não encontrada

**Contexto:** Filtro por status "active" mas todas as lojas estão "blocked"

**Comportamento:**
```
filterDashboardByStoreStatus("active"):
  firstMatch = stores.find(s => s.status === "active" || s.status === "trial")
  firstMatch = undefined
  setSelectedStoreId(undefined ?? ALL_STORES_VALUE)
  → selectedStore volta para modo rede
```

**Resultado:** fallback para modo rede quando filtro não encontra match 🟢

---

## CE-16 — Gráfico de fluxo com `flowSeries` vazio

**Contexto:** Nenhum dado de fluxo disponível (edge não conectado ou período sem dados)

**Comportamento:**
```
{flowSeries.length > 0 && (
  <section>  // BarChart
    ...
  </section>
)}
```

**Resultado:** seção do gráfico não é renderizada quando `flowSeries` está vazio — sem erro de runtime 🟢

---

## CE-17 — Plano com string não mapeada em `normalizePlanCode`

**Contexto:** Backend retorna `plan = "premium"` (valor não mapeado)

**Comportamento:**
```
normalizePlanCode("premium"):
  não é "trial"/"free" → não é "basic"/"start" → não é "pro" → não é "growth" → não é "enterprise"
  → return "premium"  (valor original)

PLAN_CAMERA_LIMITS["premium"] → undefined
```

**Risco:** 🟡 Limite de câmeras retorna `undefined` para planos não mapeados — comportamento depende de como o consumidor trata `undefined`
