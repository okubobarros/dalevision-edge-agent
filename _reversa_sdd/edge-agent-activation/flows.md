# Edge Agent Activation, Fluxos

## Fluxo 1, Emissão de Token

```mermaid
flowchart TD
    A[Usuário autenticado solicita token da loja] --> B{Permissão válida?}
    B -- não --> C[403 forbidden]
    B -- sim --> D[Calcular TTL]
    D --> E[issue_activation_token store_id]
    E --> F[Retornar token, expires_at, single_use]
```

## Fluxo 2, Bootstrap Local

```mermaid
flowchart TD
    A[bootstrap_activation] --> B[Carregar config]
    B --> C{device_key e edge_device_id existem?}
    C -- sim --> D[Estado active, sem chamada backend]
    C -- não --> E{activation_token existe?}
    E -- não --> F[Estado unprovisioned]
    E -- sim --> G[Estado activating]
    G --> H[Gerar/reutilizar device_key]
    H --> I{cloud_base_url existe?}
    I -- não --> J[Estado error]
    I -- sim --> K[POST activate]
    K --> L{Resultado}
    L -- 2xx --> M[Persistir credenciais e limpar token]
    L -- network --> N[Estado activating retry]
    L -- 401/403/409 --> O[Estado error]
    L -- outro erro --> P[Estado activating retryable]
```

## Fluxo 3, Hidratação de Env

```mermaid
flowchart TD
    A[Config com cloud/store/edge_token] --> B{Campos mínimos presentes?}
    B -- não --> C[Log warning e retorna false]
    B -- sim --> D[Set os.environ]
    D --> E{env_path resolvido?}
    E -- não --> F[Retorna true]
    E -- sim --> G[Ler linhas existentes]
    G --> H[Atualizar/append CLOUD_BASE_URL STORE_ID EDGE_TOKEN AGENT_ID]
    H --> I[Escrever .env]
    I --> J[Log edge_token_len]
```

## Fluxo 4, Uso Posterior do Edge Token

```mermaid
sequenceDiagram
    participant Agent as Edge Agent
    participant API as Backend Edge Auth
    participant DB as EdgeToken/Store

    Agent->>API: X-EDGE-TOKEN + payload edge
    API->>DB: sha256(token), active=True
    DB-->>API: EdgeToken + store
    API->>API: validar store match e blocked_reason
    API-->>Agent: 200 ou 401/403
```

## Lacunas

- 🔴 Detalhar todos os códigos de erro retornados por `activate_edge_device`.
