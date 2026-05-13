# Copilot - Tasks

## Objetivo

Reimplementar ou manter o Copilot como camada operacional equivalente ao legado: contexto, insights, conversa, feed, ações, outcomes, ledger e policies. 🟢

## Tarefas Funcionais

### T-01 - Criar modelos do Copilot

Fonte: `C:\workspace\dale-vision\apps\copilot\models.py`. 🟢

Implementar todos os modelos com campos, choices, índices e constraints: context snapshot, insight, report, conversation, message, profile, operational window, outcome, ledger e policy. 🟢

Critério de pronto: migrations preservam nomes de tabelas e constraints únicas. 🟢

### T-02 - Implementar contexto de dashboard

Fonte: `services\_core.py` e `CopilotDashboardContextView`. 🟢

Critério de pronto: endpoint por loja retorna snapshot recente ou materializa novo com `force`. 🟢

### T-03 - Implementar materialização de operational window

Fonte: `build_operational_window_payload` e `materialize_operational_window`. 🟢

Critério de pronto: bucket 5/10 min calcula métricas, statuses, flags, confiança e risco estimado, fazendo upsert por chave lógica. 🟢

### T-04 - Implementar geração de insights

Fonte: `build_insight_candidates` e `materialize_operational_insights`. 🟢

Critério de pronto: condições edge offline, câmera offline, fila alta, conversão baixa, queda de fluxo e alertas abertos geram insights com evidência e ações. 🟢

### T-05 - Implementar listagem de insights

Fonte: `CopilotInsightsView` e `CopilotNetworkInsightsView`. 🟢

Critério de pronto: loja exige leitura; rede filtra por orgs do usuário; ambos excluem expirados/arquivados. 🟢

### T-06 - Implementar relatório 72h

Fonte: `CopilotReport72hView` e `materialize_report_72h`. 🟢

Critério de pronto: retorna readiness, status_detail e next refresh. 🟢

### T-07 - Implementar conversa

Fonte: `CopilotConversationView`, serializers e `_build_copilot_assistant_reply`. 🟢

Critério de pronto: GET lista mensagens; POST cria user+assistant; OpenRouter é opcional com fallback determinístico. 🟢

### T-08 - Implementar ação de staff plan

Fonte: `CopilotStaffPlanActionView`. 🟢

Critério de pronto: POST com gestão atualiza `employees_count` e registra trilha conversacional. 🟢

### T-09 - Implementar ActionOutcome por loja

Fonte: `CopilotActionOutcomeView` e `CopilotActionOutcomeDetailView`. 🟢

Critério de pronto: GET agrega resumo; POST cria outcome; PATCH atualiza outcome e sincroniza ledger. 🟢

### T-10 - Implementar callback de ActionOutcome

Fonte: `CopilotActionOutcomeCallbackView` e testes. 🟢

Critério de pronto: token inválido retorna 403, outcome ausente retorna 404, entrega/falha/conclusão atualiza outcome e ledger. 🟢

Ação corretiva obrigatória: adicionar rota ausente ao `urls.py` se confirmada em runtime. 🔴

### T-11 - Implementar Value Ledger por loja e rede

Fonte: `CopilotValueLedgerDailyView` e `CopilotNetworkValueLedgerDailyView`. 🟢

Critério de pronto: dias clampados, totais calculados, pipeline health, status de valor, confidence tier e sprint2 acceptance disponíveis. 🟢

### T-12 - Implementar ranking de eficiência

Fonte: `CopilotNetworkEfficiencyRankingView`. 🟢

Critério de pronto: ranking combina eventos, outcomes e ledger; suporta anonimização; retorna summary e contribution factors. 🟢

### T-13 - Implementar StoreProfile

Fonte: `CopilotStoreProfileView` e `StoreProfileSerializer`. 🟢

Critério de pronto: GET retorna defaults se ausente; PATCH/PUT cria ou atualiza perfil com RBAC de gestão. 🟢

### T-14 - Implementar NetworkOperationalPolicy

Fonte: `CopilotNetworkOperationalPolicyView`. 🟢

Critério de pronto: GET cria default quando ausente; POST cria/atualiza policy por org e loja/rede. 🟢

Tarefa de reforço: aplicar RBAC por loja quando `store_id` específico for usado. 🟡

### T-15 - Implementar Intelligence Feed

Fonte: `views_intelligence_feed.py`, serializers e `services\intelligence_feed.py`. 🟢

Critério de pronto: GET consolida fontes, aplica filtros, scoring, dedupe, paginação e payload resiliente. 🟢

### T-16 - Implementar ações do Intelligence Feed

Fonte: `IntelligenceFeedActionView`. 🟢

Critério de pronto: ações atualizam status conforme fonte, criam outcome para dispatch, registram audit log best-effort e disparam n8n best-effort. 🟢

### T-17 - Implementar webhook WhatsApp Meta

Fonte: `views_whatsapp.py` e `whatsapp_dispatcher.py`. 🟢

Critério de pronto: GET verifica webhook; POST processa eventos e botão de resolução de outcome. 🟢

### T-18 - Integrar frontend copilotService

Fonte: `frontend\src\services\copilot.ts`. 🟢

Critério de pronto: métodos TS chamam todos os endpoints existentes, com fallback onde legado possui fallback. 🟢

Tarefa corretiva: alinhar ou implementar `conversation-assets`, chamado pelo frontend mas sem rota lida. 🔴

## Tarefas de Jobs

### J-01 - `copilot_tick`

Fonte: `management\commands\copilot_tick.py`. 🟢

Critério de pronto: processa uma loja ou lote, com flags para pular janela operacional, contexto, insights e relatório. 🟢

### J-02 - `copilot_operational_window_tick`

Fonte: `copilot_operational_window_tick.py`. 🟢

Critério de pronto: materializa janelas por loja com `--window-minutes`. 🟢

### J-03 - `copilot_operational_window_cleanup`

Fonte: `copilot_operational_window_cleanup.py`. 🟢

Critério de pronto: aplica retenção por cutoff e suporta dry-run/limites conforme argumentos do comando. 🟢

### J-04 - `rebuild_value_ledger_daily`

Fonte: `rebuild_value_ledger_daily.py`. 🟢

Critério de pronto: reconstrói ledger por data/range/store/org e opcionalmente remove órfãos. 🟢

### J-05 - Relatórios de aceite e health

Fonte: `copilot_value_ledger_acceptance_report.py`, `copilot_value_ledger_health_snapshot.py`, `copilot_sprint2_evidence_pack.py`, `copilot_daily_log_entry.py`. 🟢

Critério de pronto: comandos produzem saídas GO/NO-GO, health snapshot, evidence pack e daily log. 🟢

### J-06 - Motores MVP legado

Fonte: `mvp_tactical_engine.py`, `mvp_roi_engine.py`, `sync_operational_insights.py`. 🟢

Critério de pronto: se mantidos, devem ser compatibilizados com modelos atuais e marcados como MVP/legado. 🟡

## Tarefas de Teste

### TT-01 - Conversa

Fonte: `tests_conversation_view.py`. 🟢

Critério de pronto: POST de conversa retorna 201 e cria mensagens. 🟢

### TT-02 - Daily briefing

Fonte: `tests_daily_briefing_view.py`. 🟢

Critério de pronto: sem escopo retorna calm; rede com dados retorna headline esperado. 🟢

### TT-03 - Staff plan action

Fonte: `tests_staff_plan_action.py`. 🟢

Critério de pronto: atualização de staff retorna 200 e payload de método. 🟢

### TT-04 - ActionOutcome list/detail/callback

Fonte: `tests_action_outcome_list_view.py`, `tests_action_outcome_detail.py`, `tests_action_outcome_callback.py`. 🟢

Critério de pronto: resumo, patch concluído, callback autorizado/negado e 404 funcionam. 🟢

### TT-05 - Ledger e network outcomes

Fonte: `tests_value_ledger_store_view.py`, `tests_network_outcomes.py`, `tests_network_outcomes_ledger.py`. 🟢

Critério de pronto: totais, rates, pipeline health, acceptance e breakdowns são retornados. 🟢

### TT-06 - Store profile

Fonte: `tests_store_profile.py`. 🟢

Critério de pronto: GET defaults e PATCH/PUT upsert funcionam. 🟢

### TT-07 - Intelligence feed mappers/scoring/dedupe/resilience

Fonte: `tests/test_intelligence_feed_*.py`. 🟢

Critério de pronto: mapeadores, prioridade, dedupe e feed vazio resiliente passam. 🟢

## Tarefas de Correção

## Tarefas Estratégicas (0 a 10 Users)

- [ ] TC-01 — Registrar Rota de Callback ActionOutcome
  - Origem no legado: View existe, rota ausente no urls.py.
  - Critério de pronto: Endpoint `/api/v1/copilot/actions/outcomes/callback/` funcional; aceita webhooks externos (n8n/WhatsApp).
  - Confiança: 🟢

- [ ] TC-02 — Remover chamadas de Assets no Frontend (Cleanup)
  - Origem no legado: Decisão de MVP focado em texto.
  - Critério de pronto: Eliminar fetchs para áudio/anexos; console livre de erros 404 de assets.
  - Confiança: 🟢

- [ ] TC-03 — Corrigir imports no comando `sync_operational_insights`
  - Origem no legado: Inconsistência de path de modelos.
  - Critério de pronto: Comando importa `StoreProfile` de `apps.copilot.models`.
  - Confiança: 🟢

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Todas as inconsistências de rotas e assets foram resolvidas.

### V-04 - Reforçar RBAC em NetworkOperationalPolicy

Fonte: endpoint usa org scope, não role por loja específica. 🟡

Critério de pronto: quando `store_id` específico for enviado, exigir `ALLOWED_MANAGE_ROLES` naquela loja. 🟡

### V-05 - Corrigir metadata do modo de resposta

Fonte: `CopilotConversationView` grava `mode=deterministic` sempre. 🟡

Critério de pronto: metadata distingue `llm_openrouter` de `deterministic_fallback`. 🟡

## Ordem Recomendada

1. Modelos e migrations. 🟢
2. Serviços `_core` de contexto/janela/insights/report. 🟢
3. Endpoints por loja com RBAC. 🟢
4. Outcomes e ledger. 🟢
5. Intelligence Feed e ações. 🟢
6. Integrações externas com fallback. 🟢
7. Frontend `copilotService` e páginas. 🟢
8. Jobs e relatórios de aceite. 🟢
9. Correções V-01 a V-05. 🟡
