# Analytics - Tasks

## Objetivo

Reimplementar ou manter a unit `analytics` preservando os contratos de ingestão de telemetria, autorização por loja e funil administrativo. 🟢

## Tarefas Funcionais

### T-01 - Criar modelos analíticos

Fonte: `C:\workspace\dale-vision\apps\analytics\models.py`. 🟢

Implementar `StoreDailyMetrics`, `OnboardingEvent` e `AgentEvent` com campos, choices, FKs, índices e `db_table` conforme o legado. 🟢

Critério de pronto: migrations geram `onboarding_events` e `agent_events` com índices equivalentes; `StoreDailyMetrics` mantém unicidade por `store + period_date`. 🟢

### T-02 - Criar rota de ingestão de onboarding

Fonte: `C:\workspace\dale-vision\apps\analytics\views.py`. 🟢

Implementar `POST /api/v1/analytics/onboarding-event/` autenticado. 🟢

Critério de pronto: payload unitário e payload `{ events: [...] }` são aceitos. 🟢

### T-03 - Validar eventos de onboarding

Fonte: `ONBOARDING_ALLOWED_EVENTS` em `views.py`. 🟢

Validar tipo do item, presença de `store_id` e `event_type`, existência da loja e allowlist de evento. 🟢

Critério de pronto: erros retornam HTTP 400/404 nos mesmos casos do legado. 🟢

### T-04 - Aplicar autorização de leitura por loja

Fonte: chamada `require_store_role(request.user, store_id, ALLOWED_READ_ROLES)`. 🟢

Critério de pronto: usuário sem papel permitido não consegue registrar evento de onboarding para loja alheia. 🟢

### T-05 - Persistir onboarding em lote

Fonte: `OnboardingEvent.objects.bulk_create(rows, batch_size=500)`. 🟢

Critério de pronto: múltiplos eventos válidos são gravados em lote e a resposta informa `inserted`. 🟢

### T-06 - Criar rota de agent event

Fonte: `AgentEventIngestView`. 🟢

Implementar `POST /api/v1/analytics/agent-event/` autenticado com allowlist `agent_update_triggered`, `agent_update_succeeded`, `agent_update_failed`. 🟢

Critério de pronto: evento válido retorna HTTP 201 com `ok`, `event_id` e `event_type`. 🟢

### T-07 - Aplicar autorização de gestão por loja

Fonte: chamada `require_store_role(request.user, store_id, ALLOWED_MANAGE_ROLES)`. 🟢

Critério de pronto: apenas usuários com papel de gestão registram eventos de update do agent. 🟢

### T-08 - Resolver dispositivo do agent

Fonte: busca `EdgeDevice.objects.filter(store_id=store_id, device_key=device_key).first()`. 🟢

Critério de pronto: quando `device_key` existe e corresponde à loja, `device_id` é persistido; quando não corresponde, evento continua válido com `device_id=null`. 🟢

### T-09 - Criar funil administrativo

Fonte: `AdminOnboardingFunnelView`. 🟢

Implementar `GET /api/v1/analytics/admin/onboarding-funnel/?days=N`. 🟢

Critério de pronto: staff/superuser recebe payload com período, baseline, contagens, conversões, tempo médio e drop-offs. 🟢

### T-10 - Aplicar clamp de período

Fonte: conversão e clamp de `days` em `views.py`. 🟢

Critério de pronto: `days` inválido vira 30; valores menores que 1 viram 1; valores maiores que 180 viram 180. 🟢

### T-11 - Integrar frontend analytics service

Fonte: `C:\workspace\dale-vision\frontend\src\services\analytics.ts`. 🟢

Implementar cliente com métodos `trackOnboardingEvent`, `trackAgentEvent` e `getAdminOnboardingFunnel`. 🟢

Critério de pronto: chamadas usam `timeoutCategory: "best-effort"` e `noRetry: true`. 🟢

### T-12 - Emitir eventos no wizard

Fonte: `StoreActivationWizard.tsx`. 🟢

Emitir `onboarding_step_viewed`, `onboarding_step_completed`, `onboarding_dropped` e `onboarding_completed` nos mesmos pontos comportamentais. 🟢

Critério de pronto: falha de analytics é capturada e não interrompe onboarding. 🟢

### T-13 - Emitir eventos no dashboard

Fonte: `Dashboard.tsx`. 🟢

Emitir `agent_update_triggered` ao solicitar update e `agent_update_succeeded` quando versão instalada alcançar versão alvo pendente. 🟢

Critério de pronto: falha de analytics é capturada e não interrompe o update. 🟢

## Tarefas de Teste

### TT-01 - Testar evento de onboarding inválido

Fonte: `OnboardingEventIngestViewTests.test_returns_400_for_invalid_event_type`. 🟢

Critério de pronto: `event_type=invalid` retorna 400. 🟢

### TT-02 - Testar inserção de onboarding

Fonte: `OnboardingEventIngestViewTests.test_inserts_event_success`. 🟢

Critério de pronto: evento válido retorna 201, `ok=true`, `inserted=1` e chama `bulk_create`. 🟢

### TT-03 - Testar criação de agent event

Fonte: `AgentEventIngestViewTests.test_creates_agent_event`. 🟢

Critério de pronto: evento válido com device retorna 201 e chama `AgentEvent.objects.create`. 🟢

### TT-04 - Testar funil administrativo

Fonte: `AdminOnboardingFunnelViewTests.test_returns_funnel_payload`. 🟢

Critério de pronto: baseline, conversão e top drop-off são calculados conforme eventos fake. 🟢

### TT-05 - Adicionar teste de usuário comum no funil

Fonte: comportamento `_assert_internal_admin`. 🟢

Critério de pronto: usuário não staff/superuser recebe 403. 🟡

### TT-06 - Adicionar teste de lote misto de onboarding

Fonte: suporte a `{ events: [...] }`. 🟢

Critério de pronto: lote com duas lojas distintas chama verificação de permissão uma vez por loja e insere todos os eventos. 🟡

### TT-07 - Adicionar teste de normalização de `time_spent_ms`

Fonte: conversão `max(0, int(time_spent_ms))`. 🟢

Critério de pronto: valor negativo vira 0; valor inválido vira `None`. 🟡

## Tarefas de Correção/Reforço

## Tarefas Estratégicas (0 a 10 Users)

- [ ] TA-01 — Implementar Deduplicação de Eventos no Backend
  - Origem no legado: Risco de métricas inconsistentes.
  - Critério de pronto: Cache Redis (TTL 1h) verifica `event_id` (UUID); descartar duplicatas silenciosamente.
  - Confiança: 🟢

- [ ] TA-02 — Emitir evento `agent_update_failed` no Agente
  - Origem no legado: Lacuna de monitoramento de update.
  - Critério de pronto: Try/except no processo de update do agente dispara evento em caso de falha de rollback ou verificação.
  - Confiança: 🟢

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Estratégia de integridade de dados e monitoramento proativo consolidada.

### V-05 - Adicionar logs estruturados

Fonte: endpoints não possuem logging explícito. 🟡

Critério de pronto: falhas inesperadas e rejeições relevantes geram logs sem PII/segredos, com `store_id`, evento e status. 🟡

## Ordem Recomendada

1. Modelos e migrations. 🟢
2. Endpoints DRF e URLs. 🟢
3. Permissões por loja. 🟢
4. Cliente frontend best-effort. 🟢
5. Emissão no wizard e dashboard. 🟢
6. Funil administrativo. 🟢
7. Testes de contrato. 🟢
8. Correções V-01 a V-05. 🟡
