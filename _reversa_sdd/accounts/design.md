# Accounts, Design Técnico

## Interface

### Backend HTTP

| Método | Caminho | Auth | Entrada | Saída | Confiança |
|---|---|---|---|---|---|
| `POST` | `/api/accounts/register/` | AllowAny | `username`, `email`, `password`, nomes | `201 {user, token}` Knox | 🟢 |
| `POST` | `/api/accounts/login/` | AllowAny | `username` ou `identifier`, `password` | `200 {user, token}` Knox | 🟢 |
| `POST` | `/api/accounts/logout/` | Knox/Bearer | Token | Logout Knox | 🟢 |
| `POST` | `/api/accounts/logoutall/` | Knox/Bearer | Token | Revoga todos Knox | 🟢 |
| `GET` | `/api/accounts/me/` | IsAuthenticated | Token | `{user, orgs}` | 🟢 |
| `POST` | `/api/accounts/supabase/` | AllowAny | Bearer ou `access_token` | `{user, orgs, request_id}` | 🟢 |
| `GET` | `/api/me/setup-state/` | Supabase ou Knox | Token | `no_store` ou `ready` | 🟢 |
| `GET` | `/api/v1/me/status/` | IsAuthenticated | Token | Trial/subscription/plano/role | 🟢 |
| `GET` | `/api/v1/me/data-maturity/` | IsAuthenticated | `store_id?` | `M0..M3` + signals | 🟢 |
| `GET` | `/api/v1/me/admin/control-tower/summary/` | Staff/Superuser | Token | Summary operacional | 🟢 |
| `GET` | `/api/v1/me/admin/control-tower/drilldown/` | Staff/Superuser | `metric`, `limit` | Rows/columns | 🟢 |

🟢 CONFIRMADO: As rotas de accounts também são expostas em `/api/v1/accounts/` por compatibilidade.

### Frontend

| Componente/Serviço | Papel | Confiança |
|---|---|---|
| `authService.login()` | Autentica via Supabase `signInWithPassword`. | 🟢 |
| `authService.logout()` | Chama Supabase signOut e limpa estado local. | 🟢 |
| `authService.bootstrapSession()` | Revalida sessão Supabase antes de confiar em cache. | 🟢 |
| `saveSupabaseSession()` | Salva `authToken` e `userData`. | 🟢 |
| `AuthProvider` | Mantém `user`, `token`, `isAuthenticated`, `authReady`. | 🟢 |
| `PrivateRoute` | Bloqueia `/app/*` sem token. | 🟢 |
| `api.ts` interceptor | Injeta `Authorization: Bearer <token>`. | 🟢 |
| `resolvePostLoginDecision()` | Decide admin/dashboard/onboarding. | 🟢 |
| `Login` | Form de email/senha + resend confirmação. | 🟢 |
| `Register` | Signup Supabase com full_name/company. | 🟢 |
| `AuthCallback` | Troca code/hash por sessão e redireciona. | 🟢 |
| `ForgotPassword` / `ResetPassword` | Recovery Supabase. | 🟢 |

## Componentes Backend

| Componente | Responsabilidade | Confiança |
|---|---|---|
| `RegisterSerializer` | Validar email único e criar `User`. | 🟢 |
| `LoginSerializer` | Resolver username/email e chamar `authenticate()`. | 🟢 |
| `SupabaseJWTAuthentication` | Autenticar Bearer Supabase em DRF. | 🟢 |
| `_fetch_supabase_user()` | Chamar Supabase `/auth/v1/user` com cache. | 🟢 |
| `provision_user_from_supabase_info()` | Criar/atualizar usuário Django e mapear UUID. | 🟢 |
| `ensure_org_membership()` | Criar/recuperar organização e membership. | 🟢 |
| `_ensure_no_store_onboarding_progress()` | Criar/atualizar onboarding `no_store`. | 🟢 |
| `SetupStateView` | Resolver estado inicial do usuário para onboarding. | 🟢 |
| `MeStatusView` | Resolver trial/subscription/plano/role. | 🟢 |
| `MeDataMaturityView` | Calcular maturidade de dados por lojas acessíveis. | 🟢 |

## Dados e Persistência

| Entidade/Tabela | Uso | Confiança |
|---|---|---|
| `auth_user` | Usuário Django legado/provisionado. | 🟢 |
| `public.user_id_map` | Mapeia `django_user_id` para UUID Supabase/negócio. | 🟢 |
| `organizations` | Organização criada para trial/membership. | 🟢 |
| `org_members` | Vínculo usuário-org com role. | 🟢 |
| `stores` | Resolve lojas acessíveis, edge status e owner_email recovery. | 🟢 |
| `onboarding_progress` | Estado `no_store` e setup session. | 🟢 |
| `subscriptions` | Status de assinatura por org. | 🟢 |
| `knox_authtoken` | Tokens legados emitidos em login/register. | 🟢 |

## Fluxo Principal Supabase

1. 🟢 CONFIRMADO: Usuário entra no frontend por `/login` ou `/activate`.
2. 🟢 CONFIRMADO: Login chama `supabase.auth.signInWithPassword()`.
3. 🟢 CONFIRMADO: Register chama `supabase.auth.signUp()` com `emailRedirectTo`.
4. 🟢 CONFIRMADO: Callback troca `code` por sessão ou recupera token do hash.
5. 🟢 CONFIRMADO: Frontend salva `access_token` em `authToken` e user normalizado em `userData`.
6. 🟢 CONFIRMADO: Interceptor HTTP injeta `Authorization: Bearer`.
7. 🟢 CONFIRMADO: Backend `SupabaseJWTAuthentication` valida token no Supabase.
8. 🟢 CONFIRMADO: Backend cria/atualiza `User`, `user_id_map` e membership.
9. 🟢 CONFIRMADO: Pós-login consulta `/v1/me/status/`, `/me/setup-state/` e stores fallback.
10. 🟢 CONFIRMADO: Usuário é enviado para `/app/admin`, `/app/dashboard` ou `/onboarding`.

## Fluxo Legado Knox

1. 🟢 CONFIRMADO: Cliente chama `/api/accounts/login/` com username/email e senha.
2. 🟢 CONFIRMADO: `LoginSerializer` autentica via Django.
3. 🟢 CONFIRMADO: `LoginView` garante org membership para usuário não staff/superuser.
4. 🟢 CONFIRMADO: `AuthToken.objects.create(user)[1]` gera token Knox.
5. 🟢 CONFIRMADO: Cliente pode usar token nos endpoints DRF porque Knox está nas auth classes.

## Fluxo de Membership

- 🟢 CONFIRMADO: `upsert_user_id_map()` garante UUID para o usuário.
- 🟢 CONFIRMADO: Se já existe OrgMember, apenas garante onboarding `no_store` para cada org.
- 🟢 CONFIRMADO: Se não existe membership, tenta recuperar por `stores.owner_email`.
- 🟢 CONFIRMADO: Se não recupera, cria nova `Organization` com nome derivado do email/username.
- 🟢 CONFIRMADO: Cria `OrgMember` com role `owner`.
- 🟢 CONFIRMADO: Cria/atualiza `OnboardingProgress` step `no_store` quando org não tem loja.

## Fluxo `/me/setup-state`

1. 🟢 CONFIRMADO: Gera `request_id`.
2. 🟢 CONFIRMADO: Tenta autenticar por Supabase JWT.
3. 🟢 CONFIRMADO: Se Supabase não autentica, tenta Knox.
4. 🟢 CONFIRMADO: Se nenhum auth funciona, retorna 401 com `error=not_authenticated`.
5. 🟢 CONFIRMADO: Staff/superuser enxerga todas as lojas.
6. 🟢 CONFIRMADO: Usuário comum resolve UUID e orgs.
7. 🟢 CONFIRMADO: Sem org/loja retorna `state=no_store`.
8. 🟢 CONFIRMADO: Com loja retorna `state=ready`, `has_store=true`, `has_edge` e `primary_store_id`.
9. 🟢 CONFIRMADO: Se fallback de schema foi usado, resposta inclui warning/header `ORG_SCHEMA_OUTDATED`.

## Fluxo `/me/status`

- 🟢 CONFIRMADO: Staff/superuser/allowlist retorna status enterprise ativo.
- 🟢 CONFIRMADO: Usuário comum resolve `user_uuid`, primeira membership e `org_id`.
- 🟢 CONFIRMADO: Sem membership retorna trial/subscription false e role null.
- 🟢 CONFIRMADO: Com membership retorna `trial_active`, `trial_ends_at`, `has_subscription`, `plan_code`, `plan_status`, `role`.

## Observabilidade

- 🟢 CONFIRMADO: Supabase logs usam `request_id` e hash de token.
- 🟢 CONFIRMADO: Setup-state loga razões de not authenticated, provisioning e estado final.
- 🟢 CONFIRMADO: Register/login logam exceções de membership/journey sem bloquear retorno principal.
- 🟢 CONFIRMADO: Admin summary usa `_safe_count()` e registra label quando count falha.
- 🟢 CONFIRMADO: Frontend loga bootstrap/login em desenvolvimento.

## Segurança

- 🟢 CONFIRMADO: Endpoints sensíveis usam `IsAuthenticated`, exceto bootstrap/setup-state que implementam auth manual.
- 🟢 CONFIRMADO: Auth Supabase não loga token bruto.
- 🟢 CONFIRMADO: Login usa mensagem genérica para falhas.
- 🟢 CONFIRMADO: Forgot password usa mensagem anti-enumeração.
- 🟢 CONFIRMADO: Admin Control Tower exige staff/superuser.
- 🟢 DECIDIDO: Rota `/onboarding` deve ser protegida por Guard no AuthContext; usuários sem onboarding concluído ou assinatura ativa devem ser redirecionados forçadamente para o funil.
- 🟢 CONFIRMADO: JWT em `localStorage` terá TTL de 8 horas implementado para mitigar riscos de persistência pós-sessão.

## Diagrama

```mermaid
flowchart TD
    A[Frontend Login/Register] --> B[Supabase Auth]
    B --> C[Session access_token]
    C --> D[authStorage authToken/userData]
    D --> E[Axios Authorization Bearer]
    E --> F[Backend SupabaseJWTAuthentication]
    F --> G[Fetch /auth/v1/user]
    G --> H[Provision Django User]
    H --> I[Upsert user_id_map]
    I --> J[Ensure OrgMember]
    J --> K[me/status + setup-state]
    K --> L{Post-login decision}
    L -- internal admin --> M[/app/admin]
    L -- has store --> N[/app/dashboard]
    L -- no store --> O[/onboarding]
```

## Riscos e Lacunas

- 🟢 RESOLVIDO: `settings` deve ser importado em `views.py` para garantir tratamento elegante de erros de banco (Task Obrigatória).
- 🟢 RESOLVIDO: Rota `/onboarding` protegida no `AuthContext` para evitar bypass do funil de conversão.
- 🟡 RISCO: Dois provedores de token ativos, Supabase e Knox, aumentam matriz de compatibilidade.
- 🟡 RISCO: `localStorage` para JWT depende de CSP/XSS forte no frontend.
- 🟡 RISCO: Criação automática de org por login pode gerar organizações órfãs se signup não vira setup.
