# Analytics - Flows

## Fluxo 1 - Evento de onboarding unitário

```mermaid
sequenceDiagram
  participant W as StoreActivationWizard
  participant S as analyticsService
  participant API as OnboardingEventIngestView
  participant Auth as DRF/Auth + require_store_role
  participant DB as onboarding_events

  W->>S: trackOnboardingEvent(payload)
  S->>API: POST /api/v1/analytics/onboarding-event/
  API->>API: normaliza payload como lista de 1 item
  API->>API: valida store_id e event_type
  API->>Auth: require_store_role(user, store_id, ALLOWED_READ_ROLES)
  Auth-->>API: autorizado
  API->>API: normaliza time_spent_ms e user_agent
  API->>DB: bulk_create([OnboardingEvent], batch_size=500)
  DB-->>API: ok
  API-->>S: 201 { ok: true, inserted: 1 }
  S-->>W: resolve Promise
```

Confiança: 🟢 confirmado em `StoreActivationWizard.tsx`, `analytics.ts` e `views.py`.

## Fluxo 2 - Evento de onboarding em lote

```mermaid
flowchart TD
  A[POST onboarding-event com events] --> B{events e lista?}
  B -- nao --> C[Tratar request.data como evento unico]
  B -- sim --> D[Iterar lista]
  C --> D
  D --> E{Lista vazia?}
  E -- sim --> F[400 Nenhum evento recebido]
  E -- nao --> G[Validar cada item]
  G --> H{Item invalido?}
  H -- sim --> I[400 Formato ou campos invalidos]
  H -- nao --> J{Store ja verificada?}
  J -- nao --> K[Buscar Store e checar ALLOWED_READ_ROLES]
  J -- sim --> L[Preparar evento]
  K --> L
  L --> M{Ha mais itens?}
  M -- sim --> G
  M -- nao --> N[bulk_create batch_size 500]
  N --> O[201 ok inserted]
```

Confiança: 🟢 confirmado em `OnboardingEventIngestView.post`.

## Fluxo 3 - Evento de update do agent

```mermaid
sequenceDiagram
  participant D as Dashboard
  participant S as analyticsService
  participant API as AgentEventIngestView
  participant Store as Store
  participant Edge as EdgeDevice
  participant DB as agent_events

  D->>S: trackAgentEvent(agent_update_triggered)
  S->>API: POST /api/v1/analytics/agent-event/
  API->>API: valida store_id/event_type
  API->>Store: filter(id=store_id).first()
  Store-->>API: store ou null
  API->>API: require_store_role(ALLOWED_MANAGE_ROLES)
  API->>Edge: filter(store_id, device_key).first()
  Edge-->>API: device ou null
  API->>DB: create AgentEvent
  DB-->>API: id
  API-->>S: 201 { ok, event_id, event_type }
```

Confiança: 🟢 confirmado em `Dashboard.tsx`, `analytics.ts` e `AgentEventIngestView`.

## Fluxo 4 - Sucesso de update percebido pelo dashboard

```mermaid
flowchart TD
  A[Usuario solicita update] --> B[requestStoreEdgeUpdate]
  B --> C{requested=true?}
  C -- nao already_up_to_date --> D[Toast agent atualizado]
  C -- sim --> E[Salvar pendingUpdateTargetVersion]
  E --> F[Emitir agent_update_triggered]
  F --> G[Invalidar queries de edge/status/update-events]
  G --> H[Polling/refresh atualiza activationStatus]
  H --> I{installed_version == pending target?}
  I -- nao --> H
  I -- sim --> J[Emitir agent_update_succeeded]
  J --> K[Limpar pendingUpdateTargetVersion]
```

Confiança: 🟢 confirmado em `Dashboard.tsx`.

Lacuna: `agent_update_failed` é tipo aceito, mas não foi encontrado fluxo emissor. 🔴

## Fluxo 5 - Funil administrativo de onboarding

```mermaid
sequenceDiagram
  participant Admin as Usuario Staff/Superuser
  participant API as AdminOnboardingFunnelView
  participant DB as onboarding_events

  Admin->>API: GET /api/v1/analytics/admin/onboarding-funnel/?days=N
  API->>API: _assert_internal_admin(user)
  API->>API: parse days, fallback 30, clamp 1..180
  API->>DB: filter(created_at >= start, created_at < end)
  API->>DB: lojas com viewed generate_token
  DB-->>API: baseline_stores
  loop STEP_ORDER
    API->>DB: lojas com completed step
    DB-->>API: count
    API->>API: conversion = round(count / baseline * 100)
  end
  API->>DB: completed time_spent_ms
  API->>DB: dropped steps
  API->>API: avg_time_to_active_min e top_dropoff_step
  API-->>Admin: 200 payload de funil
```

Confiança: 🟢 confirmado em `AdminOnboardingFunnelView`.

## Fluxo 6 - Falha best-effort no frontend

```mermaid
flowchart TD
  A[Wizard/Dashboard chama analyticsService] --> B[api.post com best-effort e noRetry]
  B --> C{Sucesso?}
  C -- sim --> D[Sem impacto no fluxo principal]
  C -- nao --> E[Promise rejeitada]
  E --> F[catch retorna undefined]
  F --> D
```

Confiança: 🟢 confirmado em `analytics.ts`, `StoreActivationWizard.tsx` e `Dashboard.tsx`.

## Matriz de Estados/Eventos

| Origem | Evento | Momento | Persistência | Confiança |
|---|---|---|---|---|
| Wizard | `onboarding_step_viewed` | Entrada/alteração de etapa | `onboarding_events` | 🟢 |
| Wizard | `onboarding_step_completed` | Avanço de etapa | `onboarding_events` | 🟢 |
| Wizard | `onboarding_dropped` | Fechamento/desmontagem sem conclusão | `onboarding_events` | 🟢 |
| Wizard | `onboarding_completed` | Onboarding finalizado | `onboarding_events` | 🟢 |
| Dashboard | `agent_update_triggered` | Update solicitado e aceito | `agent_events` | 🟢 |
| Dashboard | `agent_update_succeeded` | Versão instalada alcança alvo | `agent_events` | 🟢 |
| Não encontrado | `agent_update_failed` | Falha de update | `agent_events` | 🔴 |

## Códigos e Respostas

| Caso | HTTP | Payload | Confiança |
|---|---:|---|---|
| Onboarding inserido | 201 | `{ ok: true, inserted: n }` | 🟢 |
| Agent event inserido | 201 | `{ ok: true, event_id, event_type }` | 🟢 |
| Funil calculado | 200 | objeto com `baseline_stores`, `conversion`, `dropoff_counts` | 🟢 |
| Evento inválido | 400 | `{ detail: "event_type inválido: ..." }` | 🟢 |
| Campos obrigatórios ausentes | 400 | `{ detail: "store_id e event_type são obrigatórios." }` | 🟢 |
| Loja inexistente | 404 | `{ detail: "Loja não encontrada." }` | 🟢 |
| Admin negado | 403 esperado via `PermissionDenied` | mensagem de acesso restrito | 🟡 |

## Pontos de Controle para Reimplementação

1. Manter rotas exatamente sob `/api/v1/analytics/`. 🟢
2. Preservar allowlists de eventos. 🟢
3. Preservar permissões distintas: leitura para onboarding, gestão para agent event. 🟢
4. Preservar tracking frontend best-effort sem retry. 🟢
5. Preservar cálculo de funil por lojas distintas, não por volume bruto de eventos. 🟢
6. Decidir explicitamente se duplicidade de eventos é comportamento aceito. 🔴
