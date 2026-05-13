# Core - Flows

## Fluxo 1 - Onboarding setup session

```mermaid
sequenceDiagram
  participant FE as Frontend onboardingService
  participant API as OnboardingSetupSessionView
  participant DB as onboarding_progress
  participant Store as stores

  FE->>API: GET /api/v1/onboarding/setup-session/?store_id=S
  API->>Store: validar store e acesso
  API->>DB: buscar sessão/progresso
  API-->>FE: ok, setup_session_id, stage, stages, progress_percent, payload
  FE->>API: POST stage + payload
  API->>DB: upsert progress/meta por stage
  API-->>FE: estado atualizado
```

Confiança: 🟢 confirmado em `views_onboarding.py` e `frontend/src/services/onboarding.ts`.

## Fluxo 2 - Próximo passo de onboarding

```mermaid
flowchart TD
  A[GET onboarding/next-step store_id] --> B[Validar store_id]
  B --> C[Checar acesso]
  C --> D[Consultar câmeras ativas]
  D --> E[Checar health de câmeras]
  E --> F[Checar ROI ausente]
  F --> G[Checar métricas recentes]
  G --> H{Há bloqueio?}
  H -- sim --> I[Retornar stage e blocking_items]
  H -- nao --> J[Retornar active/collecting_data]
```

Confiança: 🟢 confirmado pelos helpers `_has_unvalidated_cameras`, `_has_missing_roi`, `_has_recent_metrics` e `_build_completion_blocker`.

## Fluxo 3 - Publicação ROI no onboarding

```mermaid
flowchart TD
  A[POST onboarding/roi/publish] --> B[Validar store_id/camera_id/indicator_key]
  B --> C[Validar config_json]
  C --> D{ROI line/polygon válido?}
  D -- nao --> E[400 validação]
  D -- sim --> F[Persistir versão ROI/config]
  F --> G[Atualizar onboarding_progress]
  G --> H[Retornar roi_version/config_version]
```

Confiança: 🟢 confirmado em `OnboardingRoiPublishView` e helpers de shape.

## Fluxo 4 - Conclusão do onboarding

```mermaid
flowchart TD
  A[POST onboarding/complete] --> B[Validar loja e acesso]
  B --> C[Montar checklist]
  C --> D{Há blockers obrigatórios?}
  D -- sim --> E[Retornar erro de conclusão]
  D -- nao --> F[Marcar onboarding completed]
  F --> G[Registrar journey/progress quando aplicável]
  G --> H[Retornar redirect_url]
```

Confiança: 🟢 confirmado em `OnboardingCompleteView`.

## Fluxo 5 - Journey event com receipt

```mermaid
flowchart TD
  A[log_journey_event] --> B[Validar campos obrigatórios por event_name]
  B --> C{Faltando campo crítico?}
  C -- sim --> D[Log warning]
  D --> E[Inserir receipt de rejeição]
  E --> F[Retornar None]
  C -- nao --> G[Criar JourneyEvent]
  G --> H[Inserir event_receipt ON CONFLICT DO NOTHING]
  H --> I[Retornar JourneyEvent]
```

Confiança: 🟢 confirmado em `services/journey_events.py`.

## Fluxo 6 - Ingestão PDV

```mermaid
sequenceDiagram
  participant Client as Frontend/PDV
  participant API as PdvTransactionIngestView
  participant DB as PosTransactionEvent
  participant Receipts as event_receipts

  Client->>API: POST /api/v1/integration/pdv/events/
  API->>API: validar store, source_system, transaction_id, valores e occurred_at
  API->>API: checar acesso à loja
  API->>DB: create/update por store+source+transaction
  API->>Receipts: insert pdv_transaction_ingest idempotente
  API-->>Client: resposta de ingestão
```

Confiança: 🟢 confirmado em `views.py`, `models.py` e `services/event_receipts.py`.

## Fluxo 7 - Report summary/impact/produtividade

```mermaid
flowchart TD
  A[Frontend meService] --> B[GET report/summary ou impact ou productivity]
  B --> C[Parse período/data/store]
  C --> D[Resolver org/timezone]
  D --> E[Consultar métricas SQL]
  E --> F[Montar payload agregado]
  F --> G{Erro 404/503/timeout no frontend?}
  G -- sim --> H[Fallback local]
  G -- nao --> I[Renderizar payload real]
```

Confiança: 🟢 confirmado em `views_report.py` e `frontend/src/services/me.ts`.

## Fluxo 8 - Calibração

```mermaid
flowchart TD
  A[List/Create CalibrationAction] --> B[Validar escopo org/store/camera]
  B --> C[Criar ou listar ações]
  C --> D[PATCH status/prioridade/notas]
  D --> E[POST evidence]
  E --> F[GET evidences com signed URLs]
  F --> G[POST result]
  G --> H[Impact summary]
```

Confiança: 🟢 confirmado em `views_calibration.py` e `adminService`.

## Fluxo 9 - Auto-geração de calibração

```mermaid
flowchart TD
  A[POST calibration/actions/auto-generate] --> B[Resolver store_id/dry_run/max_actions]
  B --> C[Consultar sinais de qualidade/ingestão/ROI]
  C --> D[Gerar candidatos issue_code]
  D --> E{Ação ativa já existe?}
  E -- sim --> F[Ignorar duplicada]
  E -- nao --> G{dry_run?}
  G -- sim --> H[Retornar candidatos]
  G -- nao --> I[Criar CalibrationAction]
```

Confiança: 🟢 confirmado em `CalibrationActionAutoGenerateView` e helper `_has_active_action`.

## Fluxo 10 - Storage signed URL

```mermaid
flowchart TD
  A[GET system/storage/sign] --> B[Validar usuário]
  B --> C[Resolver bucket/path/expires]
  C --> D{Supabase configurado?}
  D -- nao --> E[Retornar indisponível/None]
  D -- sim --> F[create_signed_url]
  F --> G{Sucesso?}
  G -- sim --> H[Retornar signed_url]
  G -- nao --> I[Log exception e erro controlado]
```

Confiança: 🟢 confirmado em `services/storage.py` e `SnapshotSignedUrlView`.

## Fluxo 11 - Admin observability

```mermaid
flowchart TD
  A[GET admin endpoint] --> B{staff ou superuser?}
  B -- nao --> C[PermissionDenied]
  B -- sim --> D[Resolver janela/limite/store]
  D --> E[Executar SQL diagnóstico]
  E --> F[Serializar rows e summary]
  F --> G[Retornar 200]
```

Confiança: 🟢 confirmado em views admin de `views.py`.

## Fluxo 12 - Jobs core

```mermaid
flowchart TD
  A[Scheduler/CLI] --> B{Comando}
  B --> C[backfill_first_metrics_received]
  B --> D[diagnose_ingestion_funnel_gap]
  B --> E[export_metrics_drive]
  B --> F[health_alerts_tick]
  B --> G[materialize_store_kpis_daily]
  B --> H[seed_demo/seed_demo_data]
  C --> I[event_receipts/journey_events/métricas]
  D --> I
  E --> I
  F --> I
  G --> I
```

Confiança: 🟢 confirmado em `management/commands`.

## Estados Principais

| Domínio | Estados | Confiança |
|---|---|---|
| Store | `active`, `inactive`, `trial`, `blocked` | 🟢 |
| Camera | `online`, `degraded`, `offline`, `unknown`, `error` | 🟢 |
| DetectionEvent | `open`, `resolved`, `ignored` | 🟢 |
| Onboarding frontend | `no_store`, `add_cameras`, `validate_cameras`, `setup_roi`, `collecting_data`, `active` | 🟢 |
| CalibrationAction | `open`, `in_progress`, `waiting_validation`, `validated`, `rejected`, `closed` | 🟢 |
| SupportAccessRequest | `pending`, `granted`, `closed`, `rejected` | 🟢 |
| Subscription | `trialing`, `active`, `past_due`, `canceled`, `incomplete`, `blocked` | 🟢 |

## Pontos de Controle

1. Preservar `managed=False` onde o schema é externo. 🟢
2. Preservar rotas `/api/v1/*` consumidas pelo frontend. 🟢
3. Preservar fallbacks frontend para relatórios/sales. 🟢
4. Preservar idempotência de receipts e PDV. 🟢
5. Auditar drift de SQL direto contra schema real. 🟡
