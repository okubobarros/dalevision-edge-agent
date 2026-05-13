# frontend-auth-onboarding — Casos de Borda

> Casos extremos identificados no código e comportamentos defensivos implementados no módulo de autenticação e onboarding.

## CE-01 — Bootstrap com token stale no localStorage

**Contexto:** Usuário volta após vários dias com token expirado no localStorage

**Fluxo real:**
1. `bootstrapSession()` detecta `localUser && localToken` existem
2. Chama `bootstrapSupabaseSession()` → Supabase retorna sessão inválida
3. Chama `refreshSupabaseSession()` → refresh token também expirado
4. Executa `clearAuthStorage()` + `storesService.clearCache()`
5. Retorna `{ user: null, token: null }` → `PrivateRoute` redireciona para `/login`

**Comportamento:** correto — evita acesso não autorizado com token stale 🟢
**Risco:** Se `bootstrapSupabaseSession` tiver timeout longo, loading screen fica por muito tempo 🟡

---

## CE-02 — Registro com e-mail já existente no Supabase

**Contexto:** Usuário tenta criar conta com e-mail duplicado

**Comportamento atual:** Supabase não necessariamente retorna erro explícito de duplicata — pode retornar sucesso silencioso (comportamento padrão do Supabase quando "Confirm email" está ativo). Usuário recebe e-mail mas não consegue fazer signup de novo.

**Risco:** 🟢 RESOLVIDO (Prioridade) — Implementar Toast amigável ("Conta já existe - enviamos um novo link de login") para evitar confusão do usuário e perda de lead.

---

## CE-03 — Usuário confirma e-mail em outra aba enquanto formulário de login está aberto

**Contexto:** Usuário abre `/auth/callback` em nova aba, Supabase session criada, voltar para aba de login

**Comportamento:** `subscribeAuthChanges` captura storage event → `authService.rehydrate()` → `AuthContext` atualizado automaticamente

**Resultado:** AuthContext sincroniza sem reload 🟢

---

## CE-04 — Onboarding: reload no meio do step 2 após criar loja

**Contexto:** Usuário cria loja (step 1), avança para step 2, recarrega a página

**Comportamento:**
1. `useEffect` lê `dv_onboarding_state` de sessionStorage
2. `persistedStep === 2 && persistedStoreId` válido → restaura `storeId` e `step=2`
3. Usuário retoma no step 2 sem perder o `storeId`

**Resultado:** correto 🟢

---

## CE-05 — Onboarding: sessionStorage com step=3 mas storeId=null

**Contexto:** Sessão corrompida (ex.: storage modificado manualmente ou bug anterior)

**Comportamento:**
```
(persistedStep === 2 || persistedStep === 3) && !persistedStoreId
→ sessionStorage.removeItem(ONBOARDING_STATE_STORAGE_KEY)
→ setStep(1), setStoreId(null)
```

**Resultado:** resiliência contra estado inconsistente 🟢

---

## CE-06 — Custo médio/hora com vírgula decimal (input brasileiro)

**Contexto:** Usuário digita "12,50" no campo `avgHourlyLaborCost` (formato pt-BR)

**Comportamento:**
```
Number("12,50".replace(",", ".")) === 12.5  // ✓
Number("12,50") === NaN  // sem o replace → bloquearia
```

**Resultado:** normalização com `.replace(",", ".")` antes do `Number()` 🟢

---

## CE-07 — Funcionários duplicados no formulário (mesmo e-mail)

**Contexto:** Usuário adiciona o mesmo funcionário duas vezes por engano

**Comportamento:**
1. `buildEmployeesPayload` cria fingerprint `nome|email|whatsapp` para cada entrada
2. Entradas com fingerprint idêntico são removidas antes do POST
3. Payload deduplicado enviado ao backend

**Resultado:** evita erro 400 de unique constraint 🟢

---

## CE-08 — Funcionários: falha de persistência parcial no backend

**Contexto:** Backend persiste 3 de 5 funcionários (timeout ou erro parcial)

**Comportamento:**
1. Após `createEmployees(dedupedPayload)`, chama `listByStore(storeId)` para verificar
2. Detecta `missingAfterFirstWrite` — funcionários no payload mas não retornados pelo `list`
3. Chama `createEmployees(missingAfterFirstWrite)` uma segunda vez
4. Nova verificação com `listByStore`; se ainda faltantes → `setEmployeesError("Não foi possível confirmar...")`

**Resultado:** retry automático de segunda tentativa 🟢; sem loop infinito (apenas 1 retry)

---

## CE-09 — Login com "verified=1" na query string (pós-confirmação de e-mail)

**Contexto:** `AuthCallback` redireciona para `/login?verified=1` após confirmar e-mail

**Comportamento:** `useEffect` detecta `params.get("verified") === "1"` → `setError("E-mail verificado. Agora faça login.")` (mensagem de sucesso exibida no campo de erro — comportamento discutível)

**Risco:** 🟡 Mensagem de sucesso exibida em componente visual de `error` (fundo vermelho) — pode confundir usuário

---

## CE-10 — Logout com Supabase indisponível

**Contexto:** `supabase.auth.signOut()` lança exceção (rede offline)

**Comportamento:**
```typescript
try {
  await supabase.auth.signOut()
} catch (error) {
  console.warn(...)
} finally {
  // SEMPRE executa:
  storesService.clearCache()
  clearAuthStorage()
  syncApiAuthHeader()
}
```

**Resultado:** logout local sempre ocorre independente de falha no Supabase 🟢

---

## CE-11 — Baseline comercial: `avgTicket` ou `avgSalesPerDay` vazios

**Contexto:** Usuário não preenche ticket médio ou vendas/dia (campos opcionais)

**Comportamento:**
```typescript
const avgTicketNumber = avgTicketRaw ? Number(avgTicketRaw) : NaN
// Se NaN → estimatedRevenueDay = null
// avg_ticket enviado ao backend apenas se !isNaN(avgTicketNumber)
```

**Resultado:** campos opcionais não enviados ao backend se vazios; `estimatedRevenueDay=null` 🟢

---

## CE-12 — Usuário autenticado acessa `/onboarding` sem sessão ativa de onboarding e tem loja

**Contexto:** Usuário já passou pelo onboarding, limpa sessionStorage, acessa `/onboarding` novamente

**Comportamento:**
1. `recoverFromExistingStore()` chama `storesService.getStoresMinimal()`
2. Detecta `stores.length > 0` + `hasActiveOnboardingSession === false`
3. `navigate(/app/dashboard?openEdgeSetup=1&store_id=<stores[0].id>)`

**Resultado:** usuário não fica preso repetindo onboarding 🟢

---

## CE-13 — Dois `useEffect` conflitantes no step 1 do Onboarding

**Contexto:** `checkPostLoginRoute` e `recoverFromExistingStore` rodam simultaneamente no step 1

**Comportamento:**
- Ambos têm guarda `if (isLoading || !isAuthenticated || storeId || step !== 1) return`
- Ambos têm flag `active` para cancelar `setState` em caso de unmount
- Primeiro que encontrar condição de redirect navega; o segundo ignora (componente desmontado)

**Risco:** 🟡 Race condition teórica se ambos completam quase simultaneamente — React.StrictMode pode causar dupla execução

---

## CE-14 — Throttling do botão de registro: `cooldownUntil` com `useEffect` de cleanup

**Contexto:** Componente desmonta antes do timeout de 5s expirar

**Comportamento:**
```typescript
useEffect(() => {
  if (!cooldownUntil) return
  const remaining = cooldownUntil - Date.now()
  const timeoutId = window.setTimeout(() => setCooldownUntil(null), remaining)
  return () => window.clearTimeout(timeoutId)  // cleanup correto
}, [cooldownUntil])
```

**Resultado:** sem memory leak ou setState em componente desmontado 🟢

---

## CE-15 — LGPD: `termVersion` hardcoded com data

**Contexto:** Termos LGPD são atualizados (novo versionamento necessário)

**Comportamento atual:** `const LGPD_TERM_VERSION = "onboarding_lgpd_v1_2026-04-09"` — hardcoded no componente

**Risco:** 🔴 Mudanças nos termos exigem deploy de frontend; sem mecanismo de versão dinâmica; usuários que aceitaram versão antiga podem precisar re-aceitar sem notificação automática

---

## CE-16 — `demo_onboarding` em localStorage contém dados de funcionários (PII)

**Contexto:** Ao concluir o onboarding, `localStorage.setItem("demo_onboarding", JSON.stringify({ store, storeId, employees, avgHourlyLaborCost }))` persiste dados incluindo lista de funcionários

**Risco:** 🟢 RESOLVIDO (Pré-requisito Lançamento) — Remover todos os `console.log` de produção; implementar TTL de 8 horas no `localStorage` para proteção de PII de funcionários.
