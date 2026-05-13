# Accounts, Fluxos

## Fluxo 1: Login Supabase no Frontend

```mermaid
sequenceDiagram
    participant User as Usuário
    participant Login as Login.tsx
    participant Auth as authService
    participant SB as Supabase
    participant API as Backend API
    participant Router as Router

    User->>Login: email + senha
    Login->>Auth: login({username, password})
    Auth->>SB: signInWithPassword(email, password)
    SB-->>Auth: session + user
    Auth->>Auth: saveSupabaseSession()
    Auth->>API: sync Authorization Bearer
    Auth-->>Login: AuthResponse
    Login->>API: resolvePostLoginDecision()
    API-->>Login: status/setup/stores
    Login->>Router: navigate(admin/dashboard/onboarding)
```

## Fluxo 2: Callback de Email Supabase

```mermaid
flowchart TD
    A[/auth/callback] --> B[Ler code/hash/error da URL]
    B --> C{Tem erro?}
    C -- sim --> D[Mostrar ação necessária]
    C -- no --> E{Tem code?}
    E -- sim --> F[exchangeCodeForSession]
    E -- no --> G[getSession]
    F --> H{Sessão ok?}
    G --> H
    H -- no --> I{Hash tem access/refresh?}
    I -- sim --> J[setSession]
    I -- no --> K[Retry getSession até 6 vezes]
    J --> L[Obter user]
    K --> L
    H -- sim --> L
    L --> M{session + token + user?}
    M -- no --> D
    M -- yes --> N[Salvar authToken/userData]
    N --> O[refreshAuth + sync header]
    O --> P[resolver pós-login]
```

## Fluxo 3: Autenticação Supabase no Backend

```mermaid
flowchart TD
    A[Request Authorization Bearer] --> B[SupabaseJWTAuthentication]
    B --> C{Bearer presente?}
    C -- no --> D[Retorna None para próxima auth class]
    C -- yes --> E[Validar formato token]
    E --> F{Config Supabase existe?}
    F -- no --> G[SUPABASE_MISSING_CONFIG]
    F -- yes --> H[GET Supabase /auth/v1/user]
    H --> I{200?}
    I -- no --> J[AuthenticationFailed Token inválido]
    I -- yes --> K[Provisionar usuário]
    K --> L[upsert user_id_map]
    L --> M{ensure_org=true?}
    M -- yes --> N[ensure_org_membership]
    M -- no --> O[Retornar user]
    N --> O
```

## Fluxo 4: Provisionamento de Organização

```mermaid
flowchart TD
    A[ensure_org_membership] --> B[upsert_user_id_map]
    B --> C{Usuário já tem OrgMember?}
    C -- yes --> D[Garantir no_store progress por org]
    C -- no --> E[Recuperar por stores.owner_email]
    E --> F{Recuperou org?}
    F -- yes --> D
    F -- no --> G[Criar Organization trial 72h]
    G --> H{Coluna trial_ends_at existe?}
    H -- no/DatabaseError --> I[Criar Organization sem trial e marcar fallback]
    H -- yes --> J[Organization com trial_ends_at]
    I --> K[Criar OrgMember role owner]
    J --> K
    K --> L[Garantir OnboardingProgress no_store]
```

## Fluxo 5: Setup State

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant View as SetupStateView
    participant Supa as SupabaseJWTAuthentication
    participant Knox as Knox TokenAuthentication
    participant DB as Database

    FE->>View: GET /api/me/setup-state/ Bearer token
    View->>Supa: authenticate()
    alt Supabase OK
        Supa-->>View: user
    else Supabase None/Falha
        View->>Knox: authenticate()
        Knox-->>View: user ou falha
    end
    alt Sem user
        View-->>FE: 401 not_authenticated
    else User staff
        View->>DB: todas as stores
        View-->>FE: ready/no_store
    else User comum
        View->>DB: user_id_map -> OrgMember -> Stores
        View-->>FE: no_store ou ready
    end
```

## Fluxo 6: Status de Conta e Trial

```mermaid
flowchart TD
    A[GET /api/v1/me/status] --> B{Staff/Superuser/Allowlist?}
    B -- yes --> C[enterprise active internal_admin]
    B -- no --> D[Resolver user_uuid]
    D --> E[Buscar primeira OrgMember]
    E --> F{Membership existe?}
    F -- no --> G[trial false subscription false role null]
    F -- yes --> H[Resolver org_id]
    H --> I[get_org_trial_ends_at]
    I --> J[is_trial_active]
    J --> K[is_subscription_active]
    K --> L[get_org_plan_code]
    L --> M[Retornar status]
```

## Fluxo 7: Private Route

```mermaid
flowchart TD
    A[/app/*] --> B[PrivateRoute]
    B --> C{isLoading ou !authReady?}
    C -- yes --> D[Spinner]
    C -- no --> E{isAuthenticated?}
    E -- no --> F[Navigate /login]
    E -- yes --> G[Render Layout]
```

## Fluxo 8: Logout

```mermaid
flowchart TD
    A[Usuário clica logout] --> B[supabase.auth.signOut]
    B --> C{Falhou?}
    C -- sim --> D[Log warning]
    C -- no --> E[Continua]
    D --> F[storesService.clearCache]
    E --> F
    F --> G[clearAuthStorage]
    G --> H[syncApiAuthHeader]
    H --> I[AuthContext user/token null]
```

## Estados de Setup

| Estado | Condição | Uso no frontend | Confiança |
|---|---|---|---|
| `no_store` | Usuário sem org ou sem loja vinculada | Redirecionar para onboarding. | 🟢 |
| `ready` | Usuário possui loja acessível | Redirecionar para dashboard/continuar setup. | 🟢 |
| `internal_admin` | Staff/superuser/allowlist via `/me/status` | Redirecionar para admin. | 🟢 |

## Códigos e Erros

| Código / Erro | Origem | Significado | Confiança |
|---|---|---|---|
| `SUPABASE_MISSING_CONFIG` | Supabase auth/bootstrap/setup-state | Config provider ausente. | 🟢 |
| `SUPABASE_TOKEN_INVALID` | Bootstrap/setup-state | Token ausente, inválido ou expirado. | 🟢 |
| `SUPABASE_PROVISIONING_ERROR` | Supabase bootstrap/auth | Falha ao criar/atualizar usuário. | 🟢 |
| `DATABASE_ERROR` | SupabaseBootstrapView | Falha de persistência no bootstrap. | 🟢 |
| `PROVISIONING_ERROR` | SetupStateView | Falha de provisionamento. | 🟢 |
| `PERMISSION_DENIED` | Admin summary | Usuário não é staff/superuser. | 🟢 |
| `INVALID_METRIC` | Admin drilldown | Métrica desconhecida. | 🟢 |
| `ORG_SCHEMA_OUTDATED` | SetupStateView | Fallback por schema sem `trial_ends_at`. | 🟢 |

## Pontos de Controle

- 🟢 CONFIRMADO: Login legado não diferencia email inexistente e senha errada.
- 🟢 CONFIRMADO: Bootstrap frontend de conta Supabase é best-effort.
- 🟢 CONFIRMADO: Setup-state retorna JSON 401 com `request_id` quando sem auth.
- 🟢 CONFIRMADO: Staff/superuser têm bypass de trial/status.
- 🟢 CONFIRMADO: Admin control tower bloqueia usuário comum.
- 🔴 LACUNA: Branch de erro de banco em SupabaseBootstrapView pode falhar por ausência de import `settings`.
