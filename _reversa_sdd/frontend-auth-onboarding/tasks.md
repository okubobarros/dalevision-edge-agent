# frontend-auth-onboarding — Tarefas de Implementação

## Pré-requisitos
- [ ] Backend Django/Knox disponível com endpoint `/api/auth/login/` funcional
- [ ] Supabase projeto configurado com `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY`
- [ ] `storesService`, `employeesService`, `copilotService`, `onboardingService` implementados e testados
- [ ] React Router v6 configurado como provedor raiz
- [ ] `AuthContext` disponível como provedor raiz no `main.tsx`

## Tarefas

### Autenticação (AuthContext + authService)

- [ ] T-01 — Implementar `authService.login(credentials)` com POST Knox
  - Origem no legado: `frontend/src/contexts/AuthContext.tsx:52`, `frontend/src/services/auth.ts` (não lido — 🟡)
  - Critério de pronto: POST para `/api/auth/login/` retorna token; token e user persistidos em localStorage; `AuthContext.user` populado
  - Confiança: 🟡

- [ ] T-02 — Implementar `authService.bootstrapSession()` para rehydrate assíncrono no mount
  - Origem no legado: `frontend/src/contexts/AuthContext.tsx:23`
  - Critério de pronto: usuário com token válido no localStorage não é redirecionado para login ao recarregar
  - Confiança: 🟡

- [ ] T-03 — Implementar `subscribeAuthChanges` para sincronização entre abas
  - Origem no legado: `frontend/src/contexts/AuthContext.tsx:110`, `frontend/src/services/authStorage.ts`
  - Critério de pronto: logout em aba A reflete em aba B em ≤ 1s via storage event
  - Confiança: 🟢

- [ ] T-04 — Implementar `AuthProvider` com estados `user`, `token`, `isLoading`, `authReady`
  - Origem no legado: `frontend/src/contexts/AuthContext.tsx:14-125`
  - Critério de pronto: `useAuth()` retorna todos os campos do `AuthContextType`; bootstrap ocorre no mount
  - Confiança: 🟢

- [ ] T-05 — Implementar `PrivateRoute` com aguardo de `authReady`
  - Origem no legado: `frontend/src/components/PrivateRoute.tsx`
  - Critério de pronto: `/app/*` inacessível sem token; sem flash de redirect antes de `authReady=true`
  - Confiança: 🟢

### Login

- [ ] T-06 — Implementar página `Login` com formulário glassmorphism
  - Origem no legado: `frontend/src/pages/Login/Login.tsx:114-330`
  - Critério de pronto: campos username + password; toggle show/hide senha; submit chama `login()`; feedback de erro do backend exibido
  - Confiança: 🟢

- [ ] T-07 — Implementar lógica de `resolvePostLoginDecision` + navegação pós-login
  - Origem no legado: `frontend/src/pages/Login/Login.tsx:52-54`, `frontend/src/services/postLoginRoute.ts` (🟡 não lido)
  - Critério de pronto: após login bem-sucedido, usuário sem loja vai para `/onboarding`; com loja vai para `/app/dashboard`
  - Confiança: 🟡

- [ ] T-08 — Implementar detecção de e-mail não confirmado e botão de reenvio
  - Origem no legado: `frontend/src/pages/Login/Login.tsx:63-112`
  - Critério de pronto: erro com "email_not_confirmed" ou "confirm" exibe botão "Reenviar e-mail"; `supabase.auth.resend` chamado com feedback
  - Confiança: 🟢

- [ ] T-09 — Detectar params `?verified=1` e `?reset=1` na URL do login
  - Origem no legado: `frontend/src/pages/Login/Login.tsx:30-40`
  - Critério de pronto: mensagens contextuais exibidas após verificação/reset de senha
  - Confiança: 🟢

### Registro

- [ ] T-10 — Implementar página `Register` com validação inline via `useMemo`
  - Origem no legado: `frontend/src/pages/Register/Register.tsx:27-36`
  - Critério de pronto: campos nome, e-mail, empresa, senha ≥ 8 chars; botão desabilitado se qualquer campo inválido
  - Confiança: 🟢

- [ ] T-11 — Implementar `supabase.auth.signUp` com metadados `full_name` e `company`
  - Origem no legado: `frontend/src/pages/Register/Register.tsx:63-73`
  - Critério de pronto: conta criada no Supabase; e-mail de confirmação enviado com `emailRedirectTo` correto; `success=true` exibido
  - Confiança: 🟢

- [ ] T-12 — Implementar cooldown de 5s e tratamento de 429 Supabase
  - Origem no legado: `frontend/src/pages/Register/Register.tsx:56,77-82`
  - Critério de pronto: botão desabilitado 5s após click; status 429 exibe mensagem amigável sem stack trace
  - Confiança: 🟢

### Onboarding

- [ ] T-13 — Implementar `Onboarding` com estado persistido em `sessionStorage`
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:51-89`
  - Critério de pronto: reload no onboarding retoma step correto; sessão inconsistente (step>1 sem storeId) volta ao step 1
  - Confiança: 🟢

- [ ] T-14 — Implementar `handleCreateStore` com cálculo de baseline comercial
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:165-277`
  - Critério de pronto: loja criada; `estimatedRevenueDay = avgTicket × avgSalesPerDay`; `copilotService.updateStoreProfile` chamado com defaults; `trackJourneyEvent` disparado
  - Confiança: 🟢

- [ ] T-15 — Implementar `handleEmployeesNext` com deduplicação por fingerprint e retry
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:279-415`
  - Critério de pronto: fingerprint `nome|email|whatsapp` deduplica lista; segunda tentativa para `missingAfterFirstWrite`; `avg_hourly_labor_cost` obrigatório
  - Confiança: 🟢

- [ ] T-16 — Implementar `handleLgpdNext` com dois aceites obrigatórios
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:417-464`
  - Critério de pronto: `legalBasisAccepted` e `operatorRoleAccepted` obrigatórios; `onboardingService.registerLgpdAcceptance` chamado com `termVersion`; navega para dashboard após aceite
  - Confiança: 🟢

- [ ] T-17 — Implementar redirecionamento se usuário já tem loja ao entrar em `/onboarding`
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:122-157`
  - Critério de pronto: `storesService.getStoresMinimal()` chamado no mount; se lista não-vazia e sem sessão ativa → redirect para `/app/dashboard?openEdgeSetup=1&store_id=<id>`
  - Confiança: 🟢

- [ ] T-18 — Implementar limpeza de sessionStorage ao concluir onboarding
  - Origem no legado: `frontend/src/pages/Onboarding/Onboarding.tsx:441-458`
  - Critério de pronto: `dv_onboarding_state` removido; `dv_onboarding_just_completed` salvo com timestamp; `demo_onboarding` salvo em localStorage
  - Confiança: 🟢

### Roteamento e Lazy Loading

- [ ] T-19 — Configurar `App.tsx` com lazy loading de todas as páginas via `React.lazy` + `Suspense`
  - Origem no legado: `frontend/src/App.tsx:1-134`
  - Critério de pronto: todas as páginas carregam sob demanda; fallback `RouteFallback` exibido durante carregamento
  - Confiança: 🟢

- [ ] T-20 — Implementar `LegacyStoreRedirect` para compatibilidade de rotas antigas
  - Origem no legado: `frontend/src/App.tsx:46-49`
  - Critério de pronto: `/stores/:id` redireciona para `/app/operations/stores/:id`
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01 — Teste de login happy path: credenciais válidas → token salvo → navegação para rota correta
- [ ] TT-02 — Teste de login falha: credenciais inválidas → mensagem de erro do backend exibida
- [ ] TT-03 — Teste de registro: campos inválidos bloqueiam botão; signUp Supabase chamado com payload correto
- [ ] TT-04 — Teste de onboarding step 1: `createStore` chamado com payload completo; storeId salvo; step avança
- [ ] TT-05 — Teste de onboarding step 2: `avgHourlyLaborCost` vazio bloqueia avanço; deduplicação remove duplicatas
- [ ] TT-06 — Teste de LGPD: campos obrigatórios não marcados bloqueiam avanço; aceite registrado; redirect correto
- [ ] TT-07 — Teste de `PrivateRoute`: rota protegida redireciona para `/login` sem token; não redireciona com token
- [ ] TT-08 — Teste de persistência de sessão: token em localStorage → bootstrap → `isAuthenticated=true` sem login novo
- [ ] TT-09 — Teste de sessão inconsistente: sessionStorage com step=2 e storeId=null → volta ao step 1
- [ ] TT-10 — Teste de usuário com loja ao entrar em onboarding → redirect para dashboard

## Ordem Sugerida
1. T-01 a T-05 (AuthContext + serviços de auth) — fundação; sem eles nada funciona
2. T-06 a T-09 (Login) — segundo; permite acesso à área protegida
3. T-10 a T-12 (Register) — paralelo ao login após T-01 concluído
4. T-19, T-20 (roteamento) — pode ser paralelo com Register
5. T-13 a T-18 (Onboarding) — depende de T-01, T-04, T-05 e dos serviços backend
6. TT-* — testes ao fim de cada grupo de tarefas

## Tarefas Estratégicas (0 a 10 Users)

- [ ] TS-01 — Implementar Toast amigável de "E-mail já cadastrado" no Registro
  - Origem no legado: Validação estratégica de UX.
  - Critério de pronto: Se Supabase retorna que conta existe, exibir toast sugerindo login em vez de sucesso silencioso.
  - Confiança: 🟢

- [ ] TS-02 — Implementar Auth Guards para `/onboarding` e Dashboard
  - Origem no legado: Decisão crítica de proteção de funil.
  - Critério de pronto: Usuário sem loja ou sem assinatura é redirecionado para o onboarding; impossível acessar `/app/*` via URL direta sem cumprir requisitos.
  - Confiança: 🟢

- [ ] TS-03 — Limpeza de PII e Segurança de Storage
  - Origem no legado: Pré-requisito de conformidade/privacidade.
  - Critério de pronto: Todos os `console.log` de Auth removidos; TTL de 8 horas implementado na persistência do JWT no `localStorage`.
  - Confiança: 🟢

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Todas as decisões estratégicas e técnicas foram validadas.
