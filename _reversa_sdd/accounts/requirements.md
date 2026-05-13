# Accounts

## Visão Geral

🟢 CONFIRMADO: Esta unit define autenticação, criação/provisionamento de usuário, sessão frontend, bootstrap Supabase, tokens Knox legados, estado pós-login, vínculo usuário-organização e endpoints `/me/*` do DaleVision.

🟢 CONFIRMADO: O backend fica em `C:\workspace\dale-vision\apps\accounts`, enquanto o frontend consome Supabase e armazena sessão em `frontend/src/services/auth*.ts`, `AuthContext.tsx`, `PrivateRoute.tsx`, `Login`, `Register`, `AuthCallback`, `ForgotPassword` e `ResetPassword`.

🟢 CONFIRMADO: Existem dois caminhos de autenticação compatíveis: Supabase JWT via `Authorization: Bearer <token>` e Knox token legado retornado por `/api/accounts/login/` e `/api/accounts/register/`.

## Responsabilidades

- 🟢 CONFIRMADO: Registrar usuário Django legado por username/email/password.
- 🟢 CONFIRMADO: Autenticar usuário legado por username ou email e emitir token Knox.
- 🟢 CONFIRMADO: Validar token Supabase chamando `/auth/v1/user`.
- 🟢 CONFIRMADO: Provisionar ou atualizar usuário Django a partir da identidade Supabase.
- 🟢 CONFIRMADO: Manter mapeamento `django_user_id` -> `user_uuid` em `public.user_id_map`.
- 🟢 CONFIRMADO: Garantir membership em organização para usuários não internos.
- 🟢 CONFIRMADO: Criar organização trial de 72 horas quando usuário não possui membership.
- 🟢 CONFIRMADO: Recuperar membership por `stores.owner_email` quando usuário foi recriado.
- 🟢 CONFIRMADO: Expor dados do usuário atual e organizações vinculadas.
- 🟢 CONFIRMADO: Expor status de trial/subscription/plano para pós-login e paywall.
- 🟢 CONFIRMADO: Expor setup-state para decidir onboarding versus dashboard.
- 🟢 CONFIRMADO: Expor data maturity `M0..M3` por lojas acessíveis.
- 🟢 CONFIRMADO: Proteger rotas `/app/*` no frontend por presença de token.
- 🟢 CONFIRMADO: Redirecionar pós-login para admin, dashboard ou onboarding conforme estado.
- 🟢 CONFIRMADO: Fornecer painel admin interno de summary/drilldown para staff/superuser.

## Regras de Negócio

- 🟢 CONFIRMADO: `RegisterSerializer` exige senha com mínimo de 6 caracteres no endpoint legado.
- 🟢 CONFIRMADO: `RegisterSerializer` rejeita email já existente com mensagem "Este email já está em uso."
- 🟢 CONFIRMADO: `LoginSerializer` aceita `username` legado ou `identifier` novo.
- 🟢 CONFIRMADO: Login por email só é permitido quando existe exatamente um usuário com aquele email case-insensitive.
- 🟢 CONFIRMADO: Falha de login por email inexistente, senha errada, email duplicado ou usuário inativo retorna a mesma mensagem "Credenciais inválidas."
- 🟢 CONFIRMADO: Login/registro legado retornam `user` e `token` Knox.
- 🟢 CONFIRMADO: Supabase auth requer `SUPABASE_URL` e `SUPABASE_ANON_KEY` ou `SUPABASE_KEY`.
- 🟢 CONFIRMADO: Supabase auth usa cache por hash do token com TTL padrão de 20 segundos, configurável por `SUPABASE_AUTH_CACHE_SECONDS`.
- 🟢 CONFIRMADO: Timeout de Supabase auth tem padrão 4 segundos e limites entre 1 e 15 segundos.
- 🟢 CONFIRMADO: Token Supabase inválido retorna erro de autenticação sem expor o token bruto; logs usam hash `sha256:<12 chars>`.
- 🟢 CONFIRMADO: Provisionamento Supabase cria usuário com username=email, email=email e senha aleatória quando usuário não existe.
- 🟢 CONFIRMADO: Provisionamento Supabase atualiza username, email, `is_active`, `first_name` e `last_name` quando necessário.
- 🟢 CONFIRMADO: Usuário sem org recebe nova `Organization` com `trial_ends_at = now + 72h`, quando coluna existe.
- 🟢 CONFIRMADO: Se `organizations.trial_ends_at` não existe, criação de org faz fallback sem trial e marca warning `ORG_SCHEMA_OUTDATED`.
- 🟢 CONFIRMADO: Staff/superuser e allowlist interna ignoram bloqueio de trial no `/api/v1/me/status/`.
- 🟢 CONFIRMADO: `SetupStateView` aceita Supabase JWT ou Knox token e retorna `no_store` ou `ready`.
- 🟢 CONFIRMADO: Admin Control Tower exige `is_staff` ou `is_superuser`; usuário comum recebe `PERMISSION_DENIED`.
- 🟢 CONFIRMADO: Frontend atual usa Supabase `signInWithPassword`, `signUp`, `exchangeCodeForSession`, `resetPasswordForEmail` e `updateUser`.
- 🟢 CONFIRMADO: Frontend salva `authToken` e `userData` no `localStorage`.
- 🟢 CONFIRMADO: Logout frontend sempre limpa stores cache, auth storage e header Authorization, mesmo se `supabase.auth.signOut()` falhar.
- 🟡 INFERIDO: Endpoints Knox continuam por compatibilidade com integrações legadas, mas o fluxo principal de UI é Supabase.
- 🔴 LACUNA: `SupabaseBootstrapView` referencia `settings.DEBUG`, mas `apps/accounts/views.py` não importa `django.conf.settings`.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟢 O backend deve expor `/api/accounts/register/` e `/api/v1/accounts/register/`. | Should | `backend/urls.py` inclui `apps.accounts.urls` nos dois prefixes. |
| RF-02 | 🟢 O backend deve expor `/api/accounts/login/` e `/api/v1/accounts/login/`. | Should | `LoginView` autentica e retorna token Knox. |
| RF-03 | 🟢 O backend deve aceitar login legado por username ou email. | Should | `LoginSerializer.validate()` normaliza `identifier`/`username`. |
| RF-04 | 🟢 O backend deve expor logout Knox via `/logout/` e `/logoutall/`. | Should | `apps/accounts/urls.py` usa `knox_views.LogoutView` e `LogoutAllView`. |
| RF-05 | 🟢 O backend deve expor `/api/accounts/supabase/` para bootstrap Supabase. | Must | `SupabaseBootstrapView` valida bearer ou `access_token` no body. |
| RF-06 | 🟢 A autenticação padrão DRF deve aceitar Supabase JWT e Knox token. | Must | `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` contém `SupabaseJWTAuthentication` e `knox.auth.TokenAuthentication`. |
| RF-07 | 🟢 O backend deve provisionar usuário Django a partir de Supabase. | Must | `provision_user_from_supabase_info()` cria/atualiza `User` e `user_id_map`. |
| RF-08 | 🟢 O backend deve garantir org membership para usuários não internos. | Must | `ensure_org_membership()` cria/reaproveita membership. |
| RF-09 | 🟢 O backend deve expor `/api/accounts/me/` com user e orgs. | Must | `MeView.get()` consulta `user_id_map` e `OrgMember`. |
| RF-10 | 🟢 O backend deve expor `/api/v1/me/status/` com trial/subscription/plano/role. | Must | `MeStatusView.get()` retorna flags usadas pelo pós-login/paywall. |
| RF-11 | 🟢 O backend deve expor `/api/me/setup-state/` e `/api/v1/me/setup-state/`. | Must | `SetupStateView` decide `no_store` ou `ready`. |
| RF-12 | 🟢 O frontend deve proteger `/app/*` por autenticação. | Must | `PrivateRoute` redireciona para `/login` se `isAuthenticated=false`. |
| RF-13 | 🟢 O frontend deve renovar/bootstrap Supabase session antes de confiar no token em cache. | Must | `authService.bootstrapSession()` tenta `getSession()` e `refreshSession()`. |
| RF-14 | 🟢 O frontend deve definir header `Authorization: Bearer <token>` em todas as requests autenticadas. | Must | `api.ts` request interceptor chama `setAuthHeader()`. |
| RF-15 | 🟢 O pós-login deve direcionar admin interno para `/app/admin`, usuário com loja para dashboard e usuário sem loja para onboarding. | Must | `resolvePostLoginDecision()` usa user local, `/v1/me/status/`, `/me/setup-state/` e stores fallback. |
| RF-16 | 🟢 O frontend deve suportar confirmação de email e recovery Supabase. | Should | `AuthCallback`, `ForgotPassword`, `ResetPassword`. |
| RF-17 | 🟢 Admin interno deve acessar summary/drilldown; usuário comum deve ser bloqueado. | Should | `AdminControlTowerSummaryView` e `AdminControlTowerDrilldownView` validam staff/superuser. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Segurança | Token Supabase bruto não deve aparecer em logs. | `_mask_token()` registra hash curto. | 🟢 |
| Segurança | Erros de login não devem permitir enumeração de usuário. | Login inválido usa sempre "Credenciais inválidas." | 🟢 |
| Compatibilidade | APIs Knox devem continuar disponíveis em `/api/accounts` e `/api/v1/accounts`. | URLs duplicadas e serializers legados. | 🟢 |
| Disponibilidade | Bootstrap Supabase no frontend não deve bloquear login em timeout. | `bootstrapSupabaseAccount()` é best-effort e ignora falha. | 🟢 |
| Performance | Validação Supabase deve usar cache curto. | `SUPABASE_AUTH_CACHE_SECONDS` padrão 20s. | 🟢 |
| Operabilidade | Respostas críticas devem incluir `request_id`. | `SupabaseBootstrapView` e `SetupStateView`. | 🟢 |
| Resiliência | Setup state deve tentar Supabase e depois Knox. | `SetupStateView.get()` faz fallback de auth. | 🟢 |
| Privacidade | Forgot password não deve revelar se email existe. | Mensagem sempre "Se este e-mail estiver cadastrado..." | 🟢 |

## Critérios de Aceitação

```gherkin
Dado um usuário Django ativo com senha válida
Quando chamar POST /api/accounts/login/ com username e password corretos
Então a API deve retornar 200
E deve incluir user e token Knox
```

```gherkin
Dado um email inexistente
Quando chamar POST /api/accounts/login/
Então a API deve retornar erro 400
E a mensagem deve ser igual à mensagem de senha incorreta
```

```gherkin
Dado um token Supabase válido
Quando o backend autenticar a request
Então deve buscar o usuário em Supabase
E deve criar ou atualizar o User Django
E deve garantir user_id_map
E deve garantir OrgMember quando ensure_org=true
```

```gherkin
Dado um usuário sem organização
Quando ensure_org_membership executar
Então deve criar Organization
E deve criar OrgMember com role owner
E deve criar onboarding progress no_store quando não houver loja
```

```gherkin
Dado um usuário autenticado sem loja
Quando chamar /api/me/setup-state/
Então deve retornar ok=true
E state=no_store
E has_store=false
```

```gherkin
Dado um usuário autenticado com loja vinculada
Quando chamar /api/me/setup-state/
Então deve retornar ok=true
E state=ready
E primary_store_id preenchido
```

```gherkin
Dado um usuário staff
Quando chamar /api/v1/me/status/
Então deve retornar is_internal_admin=true
E plan_code=enterprise
E has_subscription=true
```

```gherkin
Dado uma sessão Supabase válida no frontend
Quando o AuthProvider iniciar
Então deve bootstrapar ou renovar sessão
E deve sincronizar Authorization Bearer no cliente HTTP
```

```gherkin
Dado uma rota /app/dashboard
Quando não houver token em storage
Então PrivateRoute deve redirecionar para /login
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Supabase JWT auth e provisionamento | Must | Fluxo atual do frontend depende disso. |
| `user_id_map` e `OrgMember` | Must | Controla acesso multi-org e onboarding. |
| `/me/setup-state` e `/me/status` | Must | Determinam pós-login, trial e dashboard/onboarding. |
| Header Authorization no frontend | Must | Todas as APIs autenticadas dependem dele. |
| Knox login/register | Should | Compatibilidade legada, mas UI atual usa Supabase. |
| Admin Control Tower | Should | Relevante para operação interna, não para login básico. |
| Forgot/reset password | Should | Necessário para UX, implementado no Supabase. |
| Journey event `signup_completed` | Could | Métrica de funil; falha não bloqueia registro. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `C:\workspace\dale-vision\apps\accounts\serializers.py` | `RegisterSerializer`, `LoginSerializer`, `UserSerializer` | 🟢 |
| `C:\workspace\dale-vision\apps\accounts\views.py` | `RegisterView`, `LoginView`, `SupabaseBootstrapView`, `MeView`, `MeStatusView`, `MeDataMaturityView`, `SetupStateView`, admin views | 🟢 |
| `C:\workspace\dale-vision\apps\accounts\auth_supabase.py` | `SupabaseJWTAuthentication`, `provision_user_from_supabase_info`, `ensure_org_membership` | 🟢 |
| `C:\workspace\dale-vision\apps\accounts\urls.py` | Rotas accounts | 🟢 |
| `C:\workspace\dale-vision\backend\settings.py` | Auth classes DRF | 🟢 |
| `C:\workspace\dale-vision\backend\urls.py` | Prefixes `/api/accounts`, `/api/v1/accounts`, `/api/me/setup-state` | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\auth.ts` | Login/logout/bootstrap frontend | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\authSession.ts` | Supabase session build/refresh/bootstrap | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\authStorage.ts` | `authToken`, `userData`, auth events | 🟢 |
| `C:\workspace\dale-vision\frontend\src\contexts\AuthContext.tsx` | AuthProvider state | 🟢 |
| `C:\workspace\dale-vision\frontend\src\components\PrivateRoute.tsx` | Proteção `/app/*` | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\postLoginRoute.ts` | Decisão pós-login | 🟢 |
| `C:\workspace\dale-vision\apps\accounts\tests.py` | Testes de login, Supabase, setup-state, me-status e admin | 🟢 |

## Lacunas de Validação

- 🟢 RESOLVIDO: Import de `settings` em `apps/accounts/views.py` é Task Obrigatória para evitar Erro 500 em falhas de banco.
- 🟢 CONFIRMADO: Endpoints Knox são o padrão oficial para gestão de sessão ativa.
- 🟢 RESOLVIDO: Risco de XSS mitigado pela implementação de TTL de 8 horas no `localStorage`.
- 🟡 Padronizar resposta de erro entre `/api/accounts/supabase/`, `SupabaseJWTAuthentication` e `/api/me/setup-state/`.
- 🟡 Confirmar lifecycle de limpeza de usuários/orgs trial criados por cadastros incompletos.
