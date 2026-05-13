# Copilot - Flows

## Fluxo 1 - Contexto de dashboard por loja

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant API as CopilotDashboardContextView
  participant RBAC as require_store_role
  participant Snap as CopilotDashboardContextSnapshot
  participant Svc as services._core
  participant DB as Metrics/Core DB

  FE->>API: GET /api/v1/copilot/stores/{store_id}/context/?force=0
  API->>RBAC: ALLOWED_READ_ROLES
  RBAC-->>API: autorizado
  API->>Snap: get_latest_context_snapshot(max_age=300s)
  alt snapshot recente
    Snap-->>API: snapshot_json
    API-->>FE: 200 snapshot_json
  else sem snapshot ou force
    API->>Svc: materialize_dashboard_context(store_id)
    Svc->>DB: assinatura, câmeras, heartbeat, métricas, profile
    Svc->>Snap: create snapshot
    API-->>FE: 200 snapshot_json
  end
```

Confiança: 🟢 confirmado em `CopilotDashboardContextView` e `services._core`.

## Fluxo 2 - Conversa com LLM e fallback

```mermaid
flowchart TD
  A[POST conversa] --> B[Validar loja e ALLOWED_READ_ROLES]
  B --> C[Validar content/session/context]
  C --> D[Get or create CopilotConversation]
  D --> E[Criar CopilotMessage role=user]
  E --> F{OPENROUTER_API_KEY existe?}
  F -- nao --> G[Gerar resposta deterministica]
  F -- sim --> H[POST OpenRouter chat completions]
  H --> I{Resposta valida?}
  I -- sim --> J[Usar texto LLM]
  I -- nao/falha --> G
  G --> K[Criar CopilotMessage role=assistant]
  J --> K
  K --> L[Retornar 201 com user message e assistant_message]
```

Confiança: 🟢 confirmado em `_build_copilot_assistant_reply` e `CopilotConversationView`.

Lacuna: metadata da resposta indica `mode=deterministic` mesmo quando LLM pode ter sido usado. 🟡

## Fluxo 3 - Materialização de janela operacional

```mermaid
flowchart TD
  A[Job copilot_operational_window_tick ou copilot_tick] --> B[Selecionar loja]
  B --> C[Resolver window_minutes 5 ou 10]
  C --> D[Floor timestamp para bucket]
  D --> E[Consultar traffic_metrics]
  D --> F[Consultar conversion_metrics]
  D --> G[Consultar detection_events]
  D --> H[Consultar vision_atomic_events]
  D --> I[Resolver cobertura edge/câmeras]
  E --> J[Calcular metrics_json]
  F --> J
  G --> J
  H --> J
  I --> K[Calcular confidence_score]
  J --> L[Calcular revenue_risk_estimated]
  K --> L
  L --> M[update_or_create OperationalWindowHourly]
```

Confiança: 🟢 confirmado em `build_operational_window_payload` e comando `copilot_operational_window_tick`.

## Fluxo 4 - Geração de insights operacionais

```mermaid
flowchart TD
  A[materialize_operational_insights] --> B[Buscar Store]
  B --> C[build_insight_candidates]
  C --> D{Edge offline?}
  D -- sim --> I1[Insight health critical]
  C --> E{Câmeras offline?}
  E -- sim --> I2[Insight health warning]
  C --> F{Fila >= 300s?}
  F -- sim --> I3[Insight queue warning]
  C --> G{Conversão < 12%?}
  G -- sim --> I4[Insight conversion warning]
  C --> H{Fluxo caiu >= 30%?}
  H -- sim --> I5[Insight flow info]
  C --> J{Alertas abertos > 0?}
  J -- sim --> I6[Insight anomaly warning]
  I1 --> K[Arquivar insights ativos anteriores]
  I2 --> K
  I3 --> K
  I4 --> K
  I5 --> K
  I6 --> K
  K --> L[Criar novos CopilotOperationalInsight]
```

Confiança: 🟢 confirmado em `services._core`.

## Fluxo 5 - ActionOutcome e Value Ledger

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant API as CopilotActionOutcomeView/Detail
  participant DB as ActionOutcome
  participant Ledger as ValueLedgerDaily

  FE->>API: POST ou PATCH outcome
  API->>API: Validar store e ALLOWED_MANAGE_ROLES
  API->>DB: create/update outcome
  API->>Ledger: _sync_value_ledger_from_outcome(outcome)
  Ledger-->>API: update_or_create ledger diário
  API-->>FE: outcome serializado
```

Confiança: 🟢 confirmado em views de outcome.

## Fluxo 6 - Callback externo de entrega/conclusão

```mermaid
flowchart TD
  A[POST callback outcome] --> B{Token serviço válido?}
  B -- nao --> C[403 FORBIDDEN]
  B -- sim --> D[Validar payload]
  D --> E[Buscar outcome por action_event_id ou id]
  E --> F{Encontrou?}
  F -- nao --> G[404 ACTION_OUTCOME_NOT_FOUND]
  F -- sim --> H[Atualizar provider_message_id/delivery_status/erro]
  H --> I{delivery failed?}
  I -- sim --> J[status=failed e failed_at]
  I -- nao --> K{new_status=completed?}
  K -- sim --> L[status=completed e completed_at]
  K -- nao --> M[Preservar status]
  J --> N[Atualizar outcome_json callback]
  L --> N
  M --> N
  N --> O[Sincronizar Value Ledger]
  O --> P[200 ok]
```

Confiança: 🟢 confirmado em `CopilotActionOutcomeCallbackView`.

Lacuna: rota não encontrada em `urls.py`. 🔴

## Fluxo 7 - Intelligence Feed

```mermaid
flowchart TD
  A[GET dashboard/intelligence-feed] --> B[Resolver org_ids e interno]
  B --> C{Sem org e não interno?}
  C -- sim --> Z[200 feed vazio]
  C -- nao --> D[Validar store_id se específico]
  D --> E[require_store_role leitura]
  E --> F[get_intelligence_feed]
  F --> G[Fetch detection_events]
  F --> H[Fetch copilot_operational_insights]
  F --> I[Fetch action_outcomes]
  F --> J[Fetch notification_logs]
  G --> K[Mapear itens]
  H --> K
  I --> K
  J --> L[Enriquecer]
  K --> L
  L --> M[Aplicar priority score]
  M --> N[Deduplicar]
  N --> O[Filtrar scope/status]
  O --> P[Ordenar e paginar]
  P --> Q[Serializar envelope]
  Q --> R[200]
```

Confiança: 🟢 confirmado em `views_intelligence_feed.py` e `services.intelligence_feed.py`.

## Fluxo 8 - Ação no Intelligence Feed

```mermaid
flowchart TD
  A[POST action feed_item_id] --> B[Validar action_type]
  B --> C[Parse prefixo de_/ci_/ao_]
  C --> D{ID válido?}
  D -- nao --> E[400 INVALID_FEED_ITEM_ID]
  D -- sim --> F[Resolver fonte]
  F --> G{Fonte existe?}
  G -- nao --> H[404 SOURCE_NOT_FOUND]
  G -- sim --> I[require_store_role gestão]
  I --> J{action_type}
  J -- acknowledge/mark/resolve/dismiss/reopen --> K[Atualizar status fonte]
  J -- dispatch_whatsapp/email --> L[Criar ActionOutcome]
  L --> M[Disparar n8n best-effort]
  J -- open_playbook/assign_owner --> N[Audit only]
  K --> O[AuditLog best-effort]
  M --> O
  N --> O
  O --> P[200 ok new_status]
```

Confiança: 🟢 confirmado em `IntelligenceFeedActionView`.

## Fluxo 9 - Value Ledger de rede e GO/NO-GO

```mermaid
flowchart TD
  A[GET network/value-ledger/daily] --> B[Resolver days/thresholds]
  B --> C[Resolver org_ids/interno]
  C --> D{Sem escopo?}
  D -- sim --> E[200 no_data NO-GO]
  D -- nao --> F[Filtrar ValueLedgerDaily]
  F --> G[Calcular stores_total e stores_with_ledger]
  G --> H[Calcular freshness/stale/no_data]
  H --> I[Calcular totais e rates]
  I --> J[Classificar value_status/confidence_tier]
  J --> K{coverage >= min e stale/no_data <= max?}
  K -- sim --> L[decision GO]
  K -- nao --> M[decision NO-GO]
  L --> N[Retornar ledger]
  M --> N
```

Confiança: 🟢 confirmado em `CopilotNetworkValueLedgerDailyView`.

## Fluxo 10 - Frontend abre Copilot

```mermaid
flowchart TD
  A[Header/Sidebar/Dashboard/StoreDetails] --> B[Navigate /app/copilot ou dispatch dv-open-copilot]
  B --> C[Layout escuta dv-open-copilot]
  C --> D[Abrir Copilot UI com prompt opcional]
  D --> E[copilotService]
  E --> F[Contexto, conversa, insights, ledger ou profile]
```

Confiança: 🟢 confirmado por rotas em `App.tsx`, `Layout.tsx`, `Header.tsx`, `StoreDetails.tsx` e `copilotService`.

## Estados Principais

| Entidade | Estados | Confiança |
|---|---|---|
| Insight | `active`, `archived` | 🟢 |
| Report 72h | `pending`, `ready`, `failed` | 🟢 |
| Message role | `system`, `assistant`, `user` | 🟢 |
| ActionOutcome status | `dispatched`, `completed`, `failed`, `canceled` | 🟢 |
| Outcome result | `resolved`, `partial`, `not_resolved` | 🟢 |
| Value status | `official`, `validated`, `estimated` | 🟢 |
| Feed item type | `live_event`, `ai_insight`, `action_status`, `resolved_outcome` | 🟢 |
| Feed status | `new`, `acknowledged`, `dispatched`, `delivered`, `in_progress`, `resolved`, `failed`, `expired`, `dismissed` | 🟢 |

## Códigos de Erro Relevantes

| Código | Quando | Confiança |
|---|---|---|
| `STORE_NOT_FOUND` | Loja ausente em contexto/report/conversa/outcomes/profile | 🟢 |
| `ACTION_OUTCOME_NOT_FOUND` | Outcome ausente em PATCH/callback | 🟢 |
| `FORBIDDEN` | Token de serviço inválido no callback | 🟢 |
| `INVALID_STORE_ID` | `store_id` inválido no Intelligence Feed | 🟢 |
| `INVALID_FEED_ITEM_ID` | ID de feed não parseável | 🟢 |
| `SOURCE_NOT_FOUND` | Fonte do feed não encontrada | 🟢 |
| `ACTION_FAILED` | Exceção ao executar ação do feed | 🟢 |

## Pontos de Controle

1. Preservar rotas `/api/v1/copilot/*` e `/api/v1/dashboard/intelligence-feed/*`. 🟢
2. Preservar RBAC de leitura/gestão por loja. 🟢
3. Preservar fallback determinístico do Copilot. 🟢
4. Preservar sincronização do Value Ledger após outcome. 🟢
5. Corrigir lacunas de rotas ausentes antes de depender de assets/callback em produção. 🔴
