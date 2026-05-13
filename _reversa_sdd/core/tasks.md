# Core - Tasks

## Objetivo

Reimplementar ou manter `apps.core` preservando compatibilidade com schema legado, contratos HTTP, onboarding, relatórios, PDV, calibração e jobs operacionais. 🟢

## Tarefas Funcionais

### T-01 - Mapear modelos unmanaged

Fonte: `C:\workspace\dale-vision\apps\core\models.py`. 🟢

Implementar modelos unmanaged para tabelas existentes, preservando `db_table`, FKs, choices e campos. 🟢

Critério de pronto: consultas ORM funcionam sem o Django tentar criar/remover tabelas unmanaged. 🟢

### T-02 - Criar modelos managed novos

Fonte: migrations `0005` a `0016` e `models.py`. 🟢

Implementar LGPD, suporte, calibração, qualidade, role inference, sales goal, PDV interest e POS transaction com constraints/índices. 🟢

Critério de pronto: migrations aplicam modelos gerenciados sem conflitar com tabelas unmanaged. 🟢

### T-03 - Implementar event receipts

Fonte: `services/event_receipts.py`. 🟢

Critério de pronto: inserir receipt idempotente, marcar processado e marcar falho por `event_id`. 🟢

### T-04 - Implementar journey events

Fonte: `services/journey_events.py`. 🟢

Critério de pronto: eventos críticos sem campos obrigatórios geram rejection receipt; eventos válidos criam `JourneyEvent` e receipt. 🟢

### T-05 - Implementar onboarding progress

Fonte: `views_onboarding.py` e `services/onboarding_progress.py`. 🟢

Critério de pronto: `GET /onboarding/progress/` retorna steps, next_step e ordered_steps compatíveis com frontend. 🟢

### T-06 - Implementar step complete

Fonte: `OnboardingStepCompleteView`. 🟢

Critério de pronto: `POST /onboarding/step/complete/` persiste step, `completed_at` e merge de meta. 🟢

### T-07 - Implementar next step

Fonte: `OnboardingNextStepView`. 🟢

Critério de pronto: retorna stage, CTA, blocking_items e health por loja. 🟢

### T-08 - Implementar setup session

Fonte: `OnboardingSetupSessionView`. 🟢

Critério de pronto: GET retorna sessão atual; POST atualiza stage/payload/setup_session_id/progress. 🟢

### T-09 - Implementar indicator catalog e ROI publish

Fonte: `OnboardingIndicatorCatalogView` e `OnboardingRoiPublishView`. 🟢

Critério de pronto: catálogo respeita câmeras selecionadas; publish valida shape line/polygon e retorna versões. 🟢

### T-10 - Implementar conclusão e LGPD

Fonte: `OnboardingCompleteView` e `OnboardingLgpdAcceptanceView`. 🟢

Critério de pronto: conclusão bloqueia pendências obrigatórias; aceite LGPD persiste termo, acknowledgements, IP e user-agent. 🟢

### T-11 - Implementar report summary

Fonte: `views_report.py`. 🟢

Critério de pronto: `/report/summary/` aceita período/data/store e retorna agregados operacionais. 🟢

### T-12 - Implementar report impact

Fonte: `ReportImpactView`. 🟢

Critério de pronto: impacto usa segmento, custo médio/hora e métricas para estimar perdas/ganhos. 🟢

### T-13 - Implementar productivity coverage

Fonte: `ProductivityCoverageView`. 🟢

Critério de pronto: endpoint tenta payload por `operational_window_hourly` e possui fallback legado quando necessário. 🟢

### T-14 - Implementar journey funnel e export

Fonte: `JourneyFunnelView` e `ReportExportView`. 🟢

Critério de pronto: funil respeita `include_global_leads` apenas para interno; export retorna blob conforme `format`. 🟢

### T-15 - Implementar sales progress

Fonte: `SalesProgressView`. 🟢

Critério de pronto: GET retorna meta/receita/estado/mês; POST salva meta mensal com `days_mode`. 🟢

### T-16 - Implementar PDV interest e ingestão

Fonte: `PdvIntegrationInterestView` e `PdvTransactionIngestView`. 🟢

Critério de pronto: interesse é salvo; transação é idempotente por loja/source/transaction e gera receipt. 🟢

### T-17 - Implementar PDV summary e health

Fonte: `PdvTransactionSummaryView`, `PdvIngestionHealthView`, `services/pdv_health.py`. 🟢

Critério de pronto: summary agrega valores; health retorna total, falhas, taxa de processamento e taxa de erro. 🟢

### T-18 - Implementar data completeness

Fonte: `DataCompletenessView`. 🟢

Critério de pronto: endpoint avalia sinais/tabelas críticas e retorna completude diagnosticável. 🟢

### T-19 - Implementar storage status e signed URL

Fonte: `StorageStatusView`, `SnapshotSignedUrlView`, `services/storage.py`. 🟢

Critério de pronto: status mostra configuração; sign gera URL quando Supabase está configurado e objeto existe. 🟢

### T-20 - Implementar calibração CRUD

Fonte: `views_calibration.py`. 🟢

Critério de pronto: ações, evidências e resultados têm endpoints funcionais com RBAC e audit log best-effort. 🟢

### T-21 - Implementar auto-geração de calibração

Fonte: `CalibrationActionAutoGenerateView`. 🟢

Critério de pronto: dry-run e execução real suportados; evita duplicidade ativa por issue/store/camera. 🟢

### T-22 - Implementar observabilidade admin

Fonte: `AdminIngestionFunnelGapView`, `AdminPipelineObservabilityView`, `AdminReleaseGateView`, `AdminCvQualityBaselineView`, `AdminHvEventHealthView`. 🟢

Critério de pronto: endpoints recusam usuários não internos e retornam payloads de diagnóstico. 🟢

## Jobs

### J-01 - Backfill de first metrics

Fonte: `backfill_first_metrics_received.py`. 🟢

Critério de pronto: detecta lojas com métricas e sem journey event, com opção dry-run. 🟢

### J-02 - Diagnóstico de gap de funil

Fonte: `diagnose_ingestion_funnel_gap.py`. 🟢

Critério de pronto: lista gaps vision metrics vs `first_metrics_received` e opcionalmente repara. 🟢

### J-03 - Export e retenção

Fonte: `export_metrics_drive.py`. 🟢

Critério de pronto: exporta CSV diário de `traffic_metrics`, `conversion_metrics` e `event_receipts`; aplica TTL quando não `--no-cleanup`. 🟢

### J-04 - Health alerts

Fonte: `health_alerts_tick.py`. 🟢

Critério de pronto: emite alertas de saúde edge/câmera em tick único para agendamento externo. 🟢

### J-05 - KPIs diários

Fonte: `materialize_store_kpis_daily.py`. 🟢

Critério de pronto: materializa `store_kpis_daily` por data/range/store. 🟢

### J-06 - Seeds

Fonte: `seed_demo.py` e `seed_demo_data.py`. 🟢

Critério de pronto: seed cria dados demo e pode limpar métricas antigas da loja demo quando solicitado. 🟢

## Tarefas de Teste

### TT-01 - Onboarding

Fonte: `tests_onboarding_*.py`. 🟢

Critério de pronto: progress, next-step, setup-session, LGPD, ROI publish e complete passam. 🟢

### TT-02 - Reports

Fonte: `tests_report_*.py`, `tests_productivity_coverage.py`, `tests_journey_funnel.py`. 🟢

Critério de pronto: summary, impact, coverage e journey funnel retornam contratos esperados. 🟢

### TT-03 - PDV e sales

Fonte: `tests_pdv_*.py`, `tests_sales_progress.py`. 🟢

Critério de pronto: ingestão idempotente, summary, health e meta mensal funcionam. 🟢

### TT-04 - Calibração

Fonte: `tests_calibration_*.py`. 🟢

Critério de pronto: CRUD, auto-generate, evidence/result e impact summary passam. 🟢

### TT-05 - Admin observability

Fonte: `tests_admin_*.py`. 🟢

Critério de pronto: guards internos e payloads de health/release/gap funcionam. 🟢

### TT-06 - Serviços

Fonte: `tests_journey_events.py`, `tests_onboarding_progress_service.py`, `tests_supabase_storage.py`. 🟢

Critério de pronto: journey contract, inferência de progress e storage fallback/signed URL funcionam. 🟢

## Correções/Reforços

### V-01 - Uniformizar RBAC por loja

Fonte: várias views usam helpers distintos. 🟡

Critério de pronto: todas as views por `store_id` passam pelo mesmo serviço de autorização ou documentam exceção. 🟡

### V-02 - Separar domínios do core

Fonte: `core` contém onboarding, reports, PDV, calibration e admin. 🟢

Critério de pronto: plano arquitetural define módulos-alvo ou mantém core como fachada com boundaries explícitos. 🟡

### V-03 - Validar drift de schema unmanaged

Fonte: muitos modelos `managed=False`. 🟢

Critério de pronto: adicionar health check/schema check para campos críticos usados por SQL direto. 🟡

### V-04 - Consolidar DemoLead

Fonte: `DemoLeadViewSet` em core e rota pública via alerts. 🟡

Critério de pronto: remover/arquivar viewset legado ou roteá-lo explicitamente. 🟡

## Ordem Recomendada

1. Modelos e schema compatibility. 🟢
2. Serviços de receipts/journey/storage/onboarding. 🟢
3. Onboarding endpoints. 🟢
4. Reports e productivity. 🟢
5. PDV e sales. 🟢
6. Calibração. 🟢
7. Admin observability. 🟢
8. Jobs. 🟢
9. Reforços V-01 a V-04. 🟡
