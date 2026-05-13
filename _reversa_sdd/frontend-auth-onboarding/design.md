# frontend-auth-onboarding — Design Técnico

## Interface

### Rotas expostas

| Rota | Componente | Proteção | Descrição |
|------|-----------|----------|-----------|
| `/` | `HomePage` | Pública | Landing page |
| `/login` | `Login` | Pública | Formulário de login Knox |
| `/activate` | `Register` | Pública | Registro via Supabase Auth |
| `/register` | redirect → `/activate` | Pública | Alias legado |
| `/onboarding` | `Onboarding` | Auth req. | Wizard multi-step (loja + equipe + LGPD) |
| `/auth/callback` | `AuthCallback` | Pública | Callback OAuth/Supabase |
| `/auth/reset-password` | `ResetPassword` | Pública | Redefinição de senha |
| `/forgot-password` | `ForgotPassword` | Pública | Solicitação de reset |
| `/app/*` | Layout + filhos | `PrivateRoute` | Área protegida |

### Context API (AuthContext)

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|-----------|
| `AuthProvider` | `({ children: ReactNode })` | `JSX.Element` | Provedor raiz no `main.tsx` |
| `login` | `(credentials: LoginCredentials) => Promise<void>` | `void` | Chama `authService.login`, salva estado |
| `logout` | `() => Promise<void>` | `void` | Chama `authService.logout`, limpa estado |
| `refreshAuth` | `() => void` | `void` | Rehydrate síncrono de localStorage |
| `user` | `User \| null` | — | Usuário atual |
| `token` | `string \| null` | — | Knox token atual |
| `isAuthenticated` | `boolean` | — | `!!token` |
| `isLoading` | `boolean` | — | true durante bootstrap/login/logout |
| `authReady` | `boolean` | — | true após bootstrap concluir |

### Componente `PrivateRoute`

| Símbolo | Assinatura | Retorno | Observação |
|---------|-----------|---------|-----------|
| `PrivateRoute` | `({ children: ReactNode })` | `JSX.Element \| Navigate` | Redireciona para `/login` se não autenticado |

## Fluxo Principal — Login

1. Usuário acessa `/login`; `Login.tsx` renderiza formulário glassmorphism
2. `handleSubmit`: salva e-mail em `dv_last_auth_email` → chama `login({ username, password })` do `AuthContext`
3. `AuthContext.login` → `authService.login(credentials)` → POST Knox `/api/auth/login/` → Knox token retornado
4. `authService.login` persiste token + user em localStorage
5. `AuthContext` atualiza `user`, `token`, `authReady=true`, `isLoading=false`
6. `Login.tsx` chama `resolvePostLoginDecision()` → determina rota pós-login
7. `persistPostLoginExplainer(decision)` → salva flag de exibição do explainer
8. `navigate(decision.route, { replace: true })` — geralmente `/onboarding` ou `/app/dashboard`

## Fluxo Principal — Registro

1. Usuário acessa `/activate`; `Register.tsx` renderiza formulário com `SetupProgress` (step 1)
2. Validação client-side com `useMemo` (errors); botão desabilitado se `!canSubmit`
3. Cooldown 5s set via `setCooldownUntil(Date.now() + 5000)` no submit
4. `supabase.auth.signUp({ email, password, options: { emailRedirectTo, data: { full_name, company } } })`
5. Supabase envia e-mail de confirmação; `setSuccess(true)` exibe feedback
6. Usuário clica no link → `AuthCallback` → Knox bootstrap → `/onboarding`

## Fluxo Principal — Onboarding (3 steps)

### Step 1 — Criar Loja
1. `StoresSetup` coleta: nome, cidade, estado, tipo de negócio, sistema de PDV, horários, qtd câmeras, ticket médio, vendas/dia
2. `handleCreateStore` → `storesService.createStore(payload)` → retorna `{ id }`
3. Baseline comercial calculado: `estimatedRevenueDay = avgTicket × avgSalesPerDay`
4. `copilotService.updateStoreProfile(storeId, { defaults: { avg_sales_per_day, ticket_medio_brl, ... } })`
5. `trackJourneyEvent("onboarding_store_commercial_baseline", ...)` — analytics
6. `setStoreId(created.id)` + `setStep(2)`

### Step 2 — Equipe e Indicadores
1. `EmployeesSetup` coleta: lista de funcionários (nome, cargo, e-mail, WhatsApp) + total de funcionários + custo médio/hora
2. `avgHourlyLaborCost` obrigatório; bloqueia avanço se vazio ou não numérico
3. Deduplicação: `employeeFingerprint = nome|email|whatsapp`; remove duplicatas do payload
4. `employeesService.createEmployees(dedupedPayload)` → verificação pós-write com `listByStore` para detectar faltantes
5. Segunda tentativa automática para registros faltantes (`missingAfterFirstWrite`)
6. `storesService.updateStore(storeId, { employees_count, avg_hourly_labor_cost })`
7. `setStep(3)`

### Step 3 — LGPD
1. `LgpdConsent` coleta: `legalBasisAccepted`, `operatorRoleAccepted` (obrigatórios), `permittedUseAccepted` (opcional)
2. `onboardingService.registerLgpdAcceptance({ storeId, termVersion: "onboarding_lgpd_v1_2026-04-09", ... })`
3. Salva snapshot `demo_onboarding` em localStorage
4. Salva `dv_onboarding_just_completed` em sessionStorage com timestamp
5. Remove `dv_onboarding_state` de sessionStorage
6. `navigate(/app/dashboard?openEdgeSetup=1&store_id=<id>)`

## Fluxos Alternativos

- **Usuário com loja ao entrar em /onboarding sem sessão ativa:** `recoverFromExistingStore()` detecta loja via `storesService.getStoresMinimal()` → redirect para dashboard com `openEdgeSetup=1`
- **Sessão inconsistente (step > 1, storeId null):** `sessionStorage.removeItem(ONBOARDING_STATE_STORAGE_KEY)` + volta para step 1
- **Email não confirmado no login:** detectado via `errCode === "email_not_confirmed"` ou mensagem contendo "confirm" → exibe botão "Reenviar e-mail" que chama `supabase.auth.resend`
- **Throttling Supabase (429) no registro:** `status === 429` → mensagem "Muitos envios recentes. Aguarde alguns minutos."
- **Funcionários duplicados:** fingerprint deduplicação filtra antes do envio; segunda tentativa cobre falhas de persistência parcial
- **Logout em outra aba:** `subscribeAuthChanges` escuta storage event → `authService.rehydrate()` → `setUser(null)`, `setToken(null)`
- **Página carregando (authReady=false):** `PrivateRoute` aguarda `authReady` antes de redirecionar — evita flash de redirect

## Dependências

| Componente | Motivo | Como usa |
|-----------|--------|---------|
| `authService` (`services/auth.ts`) | Comunicação Knox | `login()`, `logout()`, `bootstrapSession()`, `rehydrate()`, `getToken()` |
| `supabase` (`lib/supabase.ts`) | Supabase Auth client | `signUp()`, `auth.resend()`, `auth.exchangeCodeForSession()` (no callback) |
| `storesService` (`services/stores.ts`) | CRUD de lojas | `createStore()`, `updateStore()`, `getStoresMinimal()` |
| `employeesService` (`services/employees.ts`) | CRUD de equipe | `createEmployees()`, `listByStore()` |
| `copilotService` (`services/copilot.ts`) | Perfil comercial | `getStoreProfile()`, `updateStoreProfile()` |
| `onboardingService` (`services/onboarding.ts`) | LGPD | `registerLgpdAcceptance()` |
| `postLoginRoute` (`services/postLoginRoute.ts`) | Roteamento pós-login | `resolvePostLoginDecision()`, `persistPostLoginExplainer()` |
| `journey` (`services/journey.ts`) | Analytics | `trackJourneyEvent()` |
| `react-router-dom` | Roteamento SPA | `Routes`, `Route`, `Navigate`, `PrivateRoute`, `useNavigate` |

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------| 
| Login via Knox (não Supabase Auth session) | `AuthContext.tsx:52` — usa `authService.login` que chama Django/Knox | 🟢 |
| Registro via Supabase Auth (não Knox) | `Register.tsx:63` — `supabase.auth.signUp` | 🟢 |
| Dualidade Knox+Supabase: Knox para sessão, Supabase para identidade | Ausência de `supabase.auth.signIn` no Login | 🟡 |
| Persistência em localStorage (não cookie/httpOnly) | `authService` manipula localStorage diretamente | 🟢 |
| sessionStorage para onboarding state (não Redux/Zustand) | `Onboarding.tsx:88` | 🟢 |
| Lazy loading de todas as páginas | `App.tsx:5-38` com `React.lazy` + `Suspense` | 🟢 |
| `canSubmit` via `useMemo` de erros — sem validação on blur | `Register.tsx:27-36` | 🟢 |
| Restrição `cooldownUntil` no client para rate limit adicional ao Supabase | `Register.tsx:56` | 🟢 |
| Baseline comercial persistido em `StoreProfile.defaults` (não em campo direto) | `Onboarding.tsx:229-235` | 🟢 |

## Estado Interno

### `AuthContext`
```
user: User | null          → objeto de usuário (id, username, email, role...)
token: string | null       → Knox token; isAuthenticated = !!token
isLoading: boolean         → spinner durante bootstrap/login/logout
authReady: boolean         → true após primeiro bootstrap
```

### `Onboarding`
```
step: 1 | 2 | 3            → step atual (persistido em sessionStorage)
storeId: string | null     → ID da loja criada no step 1
store: StoreDraft | null    → dados do formulário de loja (local only)
employees: EmployeeDraft[] → dados do formulário de equipe (local only)
employeesTotal: string     → campo livre (persistido)
avgHourlyLaborCost: string → campo obrigatório (persistido)
lgpdLegalBasisAccepted     → booleano, obrigatório
lgpdOperatorRoleAccepted   → booleano, obrigatório
lgpdPermittedUseAccepted   → booleano, opcional
```

### `Register`
```
loading: boolean           → submissão em andamento
success: boolean           → signUp concluído com sucesso
cooldownUntil: number|null → timestamp de desbloqueio do botão
submitError: string        → erro da última tentativa
```

## Observabilidade

- `console.log` extenso em `AuthContext.tsx` nos eventos de login, logout, bootstrap — 🟡 **deve ser removido ou reduzido em produção**
- `console.warn("[Onboarding] ...")` nos fluxos de erro de equipe e perfil (apenas DEV via `import.meta.env.DEV`) 🟢
- `trackJourneyEvent("onboarding_store_commercial_baseline", ...)` — analytics de funil 🟢 (`Onboarding.tsx:243`)
- Sem métricas de performance ou traces distribuídos no módulo 🟡 DÉBITO TÉCNICO

## Riscos e Lacunas

- 🟢 RESOLVIDO: `resolvePostLoginDecision` e `AuthCallback.tsx` devem ser reforçados com guards no `AuthContext` para garantir redirecionamento ao funil de onboarding/assinatura (Task Crítica).
- 🟢 RESOLVIDO: Todos os `console.log` com PII (AuthContext.tsx:29,61,62,102) devem ser removidos antes da produção (Pré-requisito).
- 🟡 **SetupProgress no Register usa step=1 hardcoded** — componente de progresso não avança com o Register; provavelmente design intencional mas não documentado
