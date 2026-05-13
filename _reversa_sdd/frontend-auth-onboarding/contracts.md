# frontend-auth-onboarding — Contratos Externos

> Contratos entre o frontend `auth-onboarding` e serviços externos. Inclui Supabase Auth, Django/Knox backend e chamadas de API internas.

## 1. Supabase Auth — Registro

**Chamada:** `supabase.auth.signUp`
**Origem:** `frontend/src/pages/Register/Register.tsx:63`

```typescript
supabase.auth.signUp({
  email: string,               // e-mail normalizado (trim)
  password: string,            // ≥ 8 caracteres
  options: {
    emailRedirectTo: string,   // getAuthCallbackUrl() → https://app.dalevision.com/auth/callback
    data: {
      full_name: string,       // nome do usuário
      company: string,         // nome da empresa
    }
  }
})
```

**Resposta de sucesso:** `{ data: { user, session }, error: null }` → `setSuccess(true)`

**Erros tratados:**

| Código / status | Comportamento no frontend |
|-----------------|--------------------------|
| `status === 429` | Mensagem "Muitos envios recentes. Aguarde alguns minutos." |
| Qualquer outro erro | `error.message \|\| "Não foi possível criar sua conta."` |

---

## 2. Supabase Auth — Login (signInWithPassword)

**Chamada:** `supabase.auth.signInWithPassword`
**Origem:** `frontend/src/services/auth.ts:55`

> ⚠️ **IMPORTANTE**: O login **NÃO** usa Knox diretamente. Usa `supabase.auth.signInWithPassword` e depois salva a sessão Supabase como token de API. O `AuthContext` chama `authService.login()` que internamente usa Supabase, não Knox.

```typescript
supabase.auth.signInWithPassword({
  email: string,    // credentials.username.trim()
  password: string
})
```

**Resposta de sucesso:** `{ data: { session, user }, error: null }`
- `saveSupabaseSession(data.session, data.user, email)` → persiste em localStorage
- `syncApiAuthHeader()` → sincroniza header `Authorization: Bearer <token>` no axios
- `bootstrapSupabaseAccount()` (best-effort) → POST `/accounts/supabase/` para criar/vincular conta no Django

**Erros tratados:**

| Condição | Comportamento no frontend |
|----------|--------------------------|
| `errCode === "email_not_confirmed"` | Exibe botão "Reenviar e-mail" |
| Mensagem contém "confirm" ou "confirma" | Idem acima |
| Outros erros | `response.data.detail \|\| response.data.non_field_errors[0] \|\| error.message \|\| "Usuário ou senha incorretos"` |

---

## 3. Supabase Auth — Reenvio de confirmação

**Chamada:** `supabase.auth.resend`
**Origem:** `frontend/src/pages/Login/Login.tsx:94`

```typescript
supabase.auth.resend({
  type: "signup",
  email: string,
  options: {
    emailRedirectTo: string    // getAuthCallbackUrl()
  }
})
```

**Resposta:** `{ error }` — se `error`, exibe `error.message || "Não foi possível reenviar o e-mail."`

---

## 4. Django Backend — Bootstrap de conta Supabase

**Endpoint:** `POST /accounts/supabase/`
**Origem:** `frontend/src/services/auth.ts:39`
**Modo:** best-effort (`timeoutCategory: "best-effort"`) — falha silenciosa; não bloqueia login

**Headers:** `Authorization: Bearer <supabase_access_token>`

**Propósito:** criar ou vincular o usuário Supabase no banco Django na primeira vez que loga

---

## 5. Supabase Auth — Bootstrap de sessão (bootstrapSession)

**Fluxo:** `authService.bootstrapSession()`
**Origem:** `frontend/src/services/auth.ts:109`

Lógica de prioridade ao montar `AuthProvider`:

```
1. Se (localUser && localToken) existem:
   a. bootstrapSupabaseSession() → verifica se sessão Supabase ainda é válida
   b. Se falhar → refreshSupabaseSession() → tenta refresh token
   c. Se ambos falharem → clearAuthStorage() → retorna { user: null, token: null }
2. Se (localUser || localToken) ausente:
   a. refreshSupabaseSession() primeiro
   b. fallback → bootstrapSupabaseSession()
   c. Se ambos falharem → { user: null, token: null }
```

**Efeito colateral:** `storesService.clearCache()` em caso de expiração confirmada

---

## 6. Supabase Auth — Logout

**Chamada:** `supabase.auth.signOut`
**Origem:** `frontend/src/services/auth.ts:80`

Fluxo (always runs finally):
1. `supabase.auth.signOut()` — revoga sessão no Supabase
2. `storesService.clearCache()` — limpa cache de lojas
3. `clearAuthStorage()` — remove token e user do localStorage
4. `syncApiAuthHeader()` — remove header Authorization do axios

---

## 7. Backend — Criar Loja

**Endpoint:** `POST /api/stores/` (inferido)
**Chamada:** `storesService.createStore(payload)`
**Origem:** `frontend/src/pages/Onboarding/Onboarding.tsx:196`

**Payload:**
```typescript
{
  name: string,
  city: string,
  state: string,
  business_type?: string,
  business_type_other?: string,
  pos_system?: string,
  pos_other?: string,
  pos_integration_interest?: boolean,
  hours_weekdays?: string,
  hours_saturday?: string,
  hours_sunday_holiday?: string,
  cameras_count?: number,
  avg_ticket?: number,
}
```

**Resposta esperada:** `{ id: string, ... }` — se `!created?.id`, lança erro

**Erros tratados:**
- `status === 400`: extrai `data.message || data.detail || data.non_field_errors` e exibe inline

---

## 8. Backend — Atualizar Perfil da Loja (baseline comercial)

**Endpoint:** `PUT/PATCH /api/copilot/store-profile/<storeId>/` (inferido)
**Chamada:** `copilotService.updateStoreProfile(storeId, payload)`
**Origem:** `frontend/src/pages/Onboarding/Onboarding.tsx:220`

**Payload:**
```typescript
{
  business_model: string,
  has_salao: boolean,
  has_pos_integration: boolean,
  opening_hours: object,
  timezone: string,
  defaults: {
    avg_sales_per_day: number | null,
    ticket_medio_brl: number | null,
    estimated_revenue_day_brl: number | null,
    estimated_revenue_month_brl: number | null,  // estimated_revenue_day * 30
  }
}
```

**Modo:** best-effort — falha logada como `console.warn` sem bloquear onboarding

---

## 9. Backend — Criar Funcionários

**Endpoint:** `POST /api/employees/` (inferido, bulk)
**Chamada:** `employeesService.createEmployees(payload)`
**Origem:** `frontend/src/pages/Onboarding/Onboarding.tsx:331`

**Payload:** array de:
```typescript
{
  full_name: string,
  email?: string,
  whatsapp?: string,
  role?: string,
  store_id: string,
}
```

**Pós-write:** `employeesService.listByStore(storeId)` para verificar persistência; retry automático para faltantes

**Erros tratados:**
- `status === 400` com "unique" ou "store_id" no detail → "Este e-mail já está cadastrado nesta loja."
- Outros 400 → `detailText || "Dados inválidos para funcionários."`

---

**Endpoint:** `POST /api/onboarding/lgpd/` 🟢 CONFIRMADO
**Chamada:** `onboardingService.registerLgpdAcceptance(payload)`
**Origem:** `frontend/src/pages/Onboarding/Onboarding.tsx:430`

**Payload:**
```typescript
{
  storeId: string,
  termVersion: "onboarding_lgpd_v1_2026-04-09",
  legalBasisAck: boolean,       // obrigatório true
  operatorRoleAck: boolean,     // obrigatório true
  permittedUseAck: boolean,     // opcional
  metadata: {
    source: "onboarding_step_4",
    route: "/onboarding",
  }
}
```

**Erro tratado:** qualquer falha → "Não foi possível registrar o aceite. Tente novamente."

---

## 11. Analytics — Journey Event

**Chamada:** `trackJourneyEvent(eventName, payload)`
**Origem:** `frontend/src/pages/Onboarding/Onboarding.tsx:243`

```typescript
trackJourneyEvent("onboarding_store_commercial_baseline", {
  source: "onboarding",
  store_id: string,
  avg_sales_per_day: number | null,
  avg_ticket: number | null,
  estimated_revenue_day: number | null,
  estimated_revenue_month: number | null,
})
```

**Destino:** `services/journey.ts` 🟢 CONFIRMADO (Analytics de Jornada)
