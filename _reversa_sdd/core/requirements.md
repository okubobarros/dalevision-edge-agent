# Core - Requirements

## Escopo

Esta unit cobre `apps.core` no repositório `dale-vision`: modelos centrais, onboarding operacional, relatórios/KPIs, PDV, completude de dados, storage, calibração, auditoria administrativa e serviços auxiliares de eventos. 🟢

O módulo `core` é parcialmente uma camada de compatibilidade sobre tabelas existentes no Postgres/Supabase: muitos modelos herdam `UnmanagedModel` com `managed=False`, enquanto modelos mais novos de suporte, calibração, LGPD, metas e PDV são gerenciados pelo Django. 🟢

## Evidências

| Evidência | Papel | Confiança |
|---|---|---|
| `C:\workspace\dale-vision\apps\core\models.py` | Modelos centrais e choices | 🟢 |
| `C:\workspace\dale-vision\apps\core\urls.py` | Rotas `/api/v1/*` do core | 🟢 |
| `C:\workspace\dale-vision\apps\core\views.py` | Lead legado, storage, sales, PDV, data quality e admin health | 🟢 |
| `C:\workspace\dale-vision\apps\core\views_onboarding.py` | Onboarding progressivo, sessão, ROI, LGPD e conclusão | 🟢 |
| `C:\workspace\dale-vision\apps\core\views_report.py` | Relatórios, impacto, produtividade, export e funil | 🟢 |
| `C:\workspace\dale-vision\apps\core\views_calibration.py` | Ações/evidências/resultados de calibração | 🟢 |
| `C:\workspace\dale-vision\apps\core\services\*.py` | Receipts, journey events, onboarding progress, PDV health e storage | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\onboarding.ts` | Contratos frontend de onboarding | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\me.ts` | Consumo de report/produtividade/funil | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\sales.ts` | Consumo de sales progress | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\admin.ts` | Consumo de calibração/admin | 🟢 |

## Requisitos Funcionais

### RF-01 - Representar entidades centrais

O sistema deve mapear organizações, membros, lojas, zonas, câmeras, saúde de câmeras, funcionários, turnos, ponto, eventos de detecção, mídias, regras de alerta, notificações, leads, onboarding, billing, subscriptions, audit logs e journey events sobre tabelas existentes. 🟢

### RF-02 - Preservar choices de domínio

O sistema deve preservar roles (`owner/admin/manager/viewer`), status de loja, status de câmera, severidade/status de evento, roles de funcionário, status de lead e status de assinatura. 🟢

### RF-03 - Manter modelos gerenciados recentes

O sistema deve gerenciar por migrations os modelos `LgpdAcceptance`, `SupportAccessRequest`, `SupportAccessGrant`, `CalibrationAction`, `CalibrationEvidence`, `CalibrationResult`, `CameraQualityScore`, `TrackRoleInference`, `UserSalesGoal`, `PdvIntegrationInterest` e `PosTransactionEvent`. 🟢

### RF-04 - Registrar jornada de negócio

`log_journey_event` deve criar `JourneyEvent`, validar campos obrigatórios de eventos críticos, registrar rejeições de contrato e inserir espelho em `event_receipts`. 🟢

### RF-05 - Manter recibos idempotentes

O serviço `event_receipts` deve inserir recibos com `ON CONFLICT (event_id) DO NOTHING` e permitir marcar recibos como processados ou falhos. 🟢

### RF-06 - Expor progresso de onboarding

O sistema deve expor `GET /api/v1/onboarding/progress/` retornando steps, próximo step e ordem. 🟢

Steps frontend confirmados: `edge_connected`, `camera_added`, `camera_health_ok`, `roi_published`, `monitoring_started`, `first_insight`. 🟢

### RF-07 - Completar step de onboarding

O sistema deve expor `POST /api/v1/onboarding/step/complete/`, aceitar `step`, `store_id` opcional e `meta`, persistindo progresso com merge de metadados. 🟢

### RF-08 - Recomendar próximo passo de onboarding

O sistema deve expor `GET /api/v1/onboarding/next-step/?store_id=...`, retornando stage, título, descrição, CTA, bloqueios e health. 🟢

Stages frontend confirmados: `no_store`, `add_cameras`, `validate_cameras`, `setup_roi`, `collecting_data`, `active`. 🟢

### RF-09 - Gerenciar setup session de onboarding

O sistema deve expor `GET/POST /api/v1/onboarding/setup-session/`, controlar estágio de setup, payloads por etapa, progress percent e `setup_session_id`. 🟢

Stages de setup confirmados: `install`, `camera_discovery`, `camera_selection`, `indicator_selection`, `roi_mapping`, `validation`, `completed`. 🟢

### RF-10 - Expor catálogo de indicadores

O sistema deve expor `GET /api/v1/onboarding/indicator-catalog/`, retornando indicadores com `key`, `label`, `metric_type`, `roi_shape` e `required`. 🟢

### RF-11 - Publicar ROI no onboarding

O sistema deve expor `POST /api/v1/onboarding/roi/publish/`, aceitando `store_id`, `camera_id`, `indicator_key` e `config_json`, retornando versões de ROI/config. 🟢

### RF-12 - Concluir onboarding

O sistema deve expor `POST /api/v1/onboarding/complete/`, validar checklist de conclusão, marcar onboarding como completo e retornar `redirect_url`. 🟢

### RF-13 - Registrar aceite LGPD

O sistema deve expor `POST /api/v1/onboarding/lgpd-acceptance/`, persistindo versão do termo, três acknowledgements obrigatórios, IP, user-agent e metadata. 🟢

### RF-14 - Expor relatórios operacionais

O sistema deve expor `GET /api/v1/report/summary/`, `GET /api/v1/report/impact/`, `GET /api/v1/productivity/coverage/`, `GET /api/v1/report/journey-funnel/` e `GET /api/v1/report/export/`. 🟢

### RF-15 - Suportar fallback frontend de relatórios

O frontend deve tratar 404/503/timeout em summary, impact e productivity coverage com payloads fallback, preservando UX. 🟢

### RF-16 - Gerenciar meta de vendas do usuário

O sistema deve expor `GET/POST /api/v1/sales/progress/`, ler/criar `UserSalesGoal`, calcular receita atual por PDV quando disponível e retornar estado `connected`, `not_configured` ou `syncing`. 🟢

### RF-17 - Registrar interesse de integração PDV

O sistema deve expor `POST /api/v1/integration/pdv/interest/`, persistindo sistema PDV, email, telefone e status de solicitação. 🟢

### RF-18 - Ingerir eventos de transação PDV

O sistema deve expor `POST /api/v1/integration/pdv/events/`, validar acesso à loja, aplicar idempotência por `(store, source_system, transaction_id)`, criar/atualizar `PosTransactionEvent` e inserir receipt `pdv_transaction_ingest`. 🟢

### RF-19 - Expor resumo e saúde PDV

O sistema deve expor `GET /api/v1/integration/pdv/summary/` e `GET /api/v1/integration/pdv/ingestion-health/`, retornando totais financeiros e saúde de ingestão via `event_receipts`. 🟢

### RF-20 - Expor completude de dados

O sistema deve expor `GET /api/v1/data-quality/completeness/`, avaliando presença de tabelas/sinais operacionais necessários. 🟢

### RF-21 - Expor status e assinatura de storage

O sistema deve expor `GET /api/v1/system/storage-status/` e `GET /api/v1/system/storage/sign/`, usando Supabase Storage quando configurado. 🟢

### RF-22 - Gerenciar ações de calibração

O sistema deve expor endpoints para listar/criar ações, atualizar status/prioridade/notas, anexar evidências, listar evidências com signed URLs, registrar resultados, auto-gerar ações e sumarizar impacto. 🟢

### RF-23 - Auto-gerar ações de calibração

O endpoint de auto-geração deve analisar sinais de qualidade/ingestão/ROI/metrics e criar ações abertas evitando duplicidade ativa por loja/câmera/issue. 🟢

### RF-24 - Expor observabilidade administrativa

O sistema deve expor endpoints internos para ingestion funnel gap, pipeline observability, release gate, CV quality baseline e HV event health, todos restritos a staff/superuser. 🟢

### RF-25 - Oferecer jobs operacionais

O módulo deve fornecer comandos para backfill de `first_metrics_received`, diagnóstico de gap de funil, exportação/retention de métricas, alertas de health, materialização de KPIs diários e seed demo. 🟢

## Requisitos Não Funcionais

### Segurança

Endpoints operacionais usam `IsAuthenticated`, exceto lead público fora do core roteado via `apps.alerts.views.DemoLeadCreateView`. 🟢

Operações por loja validam acesso via helpers/roles ou escopo de org, dependendo da view. 🟢

Endpoints admin exigem staff/superuser. 🟢

LGPD registra consentimento explícito com IP e user-agent. 🟢

### Compatibilidade

Muitos modelos são `managed=False`, preservando compatibilidade com schema Supabase/Postgres existente. 🟢

Há rotas com e sem barra para `productivity/coverage`. 🟢

### Resiliência

Serviços de storage retornam `None` e logam warning/exception quando Supabase não está configurado ou falha. 🟢

Journey events sobrevivem a falhas de receipt, logando exceção sem abortar necessariamente a criação do evento. 🟢

Frontend possui fallbacks para endpoints de relatório e sales progress indisponíveis. 🟢

## Critérios de Aceitação

### CA-01 - Onboarding progress

Dado usuário autenticado e loja acessível, quando consultar progresso, então deve receber steps normalizados e próximo step. 🟢

### CA-02 - Setup session

Dado `store_id` válido, quando enviar stage e payload, então o sistema deve persistir payload por estágio e retornar `progress_percent`. 🟢

### CA-03 - LGPD

Dado usuário autenticado e todos os acknowledgements verdadeiros, quando registrar aceite, então deve persistir `LgpdAcceptance` e retornar `accepted_at`. 🟢

### CA-04 - PDV idempotente

Dado mesmo `store_id`, `source_system` e `transaction_id`, quando evento PDV for reenviado, então a constraint deve impedir duplicidade lógica. 🟢

### CA-05 - Calibration lifecycle

Dado ação aberta, quando usuário autorizado atualizar status, enviar evidência e registrar resultado, então a ação deve refletir status/artefatos/resultados e audit log best-effort. 🟢

### CA-06 - Admin guard

Dado usuário comum, quando chamar endpoints admin de observabilidade, então deve receber negação de acesso. 🟢

### CA-07 - Report fallback

Dado timeout/503 em report summary ou impact, quando frontend consumir `meService`, então deve retornar fallback local em vez de quebrar a tela. 🟢

## MoSCoW

### Must

- Modelos centrais compatíveis com schema legado. 🟢
- Onboarding operacional completo. 🟢
- Relatórios, produtividade e funil. 🟢
- PDV, sales progress e event receipts. 🟢
- Calibração e observabilidade admin. 🟢

### Should

- Signed URLs para evidências/snapshots. 🟢
- Jobs de backfill/materialização/export/health. 🟢
- Journey events com contrato e rejection receipts. 🟢

### Could

- Consolidar `DemoLeadViewSet` não roteado no core com `DemoLeadCreateView` em alerts. 🟡
- Reduzir duplicidade entre relatórios core e copilot/value ledger. 🟡

### Won't

- Gerenciar todo schema legado via migrations Django; parte permanece unmanaged por compatibilidade. 🟢

## Lacunas

| Lacuna | Impacto | Confiança |
|---|---|---|
| `DemoLeadViewSet` existe em `core.views`, mas a rota pública usa `apps.alerts.views.DemoLeadCreateView`. | Possível código legado não utilizado. | 🟡 |
| Autorização por loja não é uniforme entre todas as views; algumas usam helper local, outras org/admin. | Risco de divergência de RBAC. | 🟡 |
| `core` concentra muitas responsabilidades distintas. | Alto acoplamento e difícil manutenção. | 🟢 |
| Vários relatórios usam SQL direto em tabelas públicas. | Mudanças de schema quebram runtime sem proteção de ORM. | 🟢 |
