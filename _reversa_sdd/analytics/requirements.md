# Analytics - Requirements

## Escopo

Esta unit especifica o módulo `apps.analytics` do repositório `dale-vision`, responsável por registrar telemetria operacional de onboarding, eventos de atualização do Edge Agent e expor o funil administrativo de ativação. 🟢

O módulo não é o pipeline principal de métricas de visão (`vision.metrics.v1`, `traffic_metrics`, `conversion_metrics`); ele complementa o produto com eventos de jornada e governança de implantação. 🟢

## Evidências

| Evidência | Papel | Confiança |
|---|---|---|
| `C:\workspace\dale-vision\apps\analytics\models.py` | Modelos `StoreDailyMetrics`, `OnboardingEvent`, `AgentEvent` | 🟢 |
| `C:\workspace\dale-vision\apps\analytics\views.py` | Endpoints de ingestão e funil | 🟢 |
| `C:\workspace\dale-vision\apps\analytics\urls.py` | Rotas `/api/v1/analytics/*` | 🟢 |
| `C:\workspace\dale-vision\apps\analytics\tests.py` | Cobertura comportamental mínima | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\analytics.ts` | Cliente frontend para analytics | 🟢 |
| `C:\workspace\dale-vision\frontend\src\components\StoreActivationWizard.tsx` | Emissão de eventos de onboarding | 🟢 |
| `C:\workspace\dale-vision\frontend\src\pages\Dashboard\Dashboard.tsx` | Emissão de eventos de update do agent | 🟢 |
| `C:\workspace\dale-vision\backend\urls.py` | Inclusão da rota `api/v1/analytics/` | 🟢 |

## Requisitos Funcionais

### RF-01 - Registrar evento único de onboarding

O sistema deve aceitar `POST /api/v1/analytics/onboarding-event/` com um objeto contendo `store_id`, `event_type` e campos opcionais `step`, `technical_status`, `time_spent_ms`, `session_id` e `metadata`. 🟢

Eventos aceitos: `onboarding_step_viewed`, `onboarding_step_completed`, `onboarding_completed`, `onboarding_dropped`. 🟢

### RF-02 - Registrar lote de eventos de onboarding

O endpoint de onboarding deve aceitar payload no formato `{ "events": [...] }` e persistir todos os eventos válidos em `bulk_create` com `batch_size=500`. 🟢

### RF-03 - Validar payload de onboarding

O sistema deve rejeitar payload vazio, item não-objeto, ausência de `store_id`, ausência de `event_type` e `event_type` fora da allowlist com HTTP 400. 🟢

### RF-04 - Validar loja antes de registrar onboarding

Para cada `store_id` distinto no lote, o sistema deve procurar a loja e retornar HTTP 404 quando ela não existir. 🟢

### RF-05 - Exigir permissão de leitura para onboarding

Antes de inserir eventos de onboarding, o sistema deve chamar `require_store_role(request.user, store_id, ALLOWED_READ_ROLES)`. 🟢

### RF-06 - Normalizar tempo gasto

Quando `time_spent_ms` vier preenchido, o sistema deve converter para inteiro não-negativo. Se a conversão falhar, deve armazenar `null`. 🟢

### RF-07 - Capturar user-agent

O sistema deve copiar `HTTP_USER_AGENT` da requisição para todos os eventos de onboarding do lote. 🟢

### RF-08 - Registrar evento de atualização do agent

O sistema deve aceitar `POST /api/v1/analytics/agent-event/` com `store_id`, `event_type`, `device_key`, `from_version`, `to_version` e `metadata`. 🟢

Eventos aceitos: `agent_update_triggered`, `agent_update_succeeded`, `agent_update_failed`. 🟢

### RF-09 - Exigir permissão de gestão para eventos de agent

Antes de inserir eventos de agent, o sistema deve chamar `require_store_role(request.user, store_id, ALLOWED_MANAGE_ROLES)`. 🟢

### RF-10 - Vincular evento de agent ao dispositivo quando possível

Quando `device_key` for enviado, o sistema deve buscar `EdgeDevice` por `store_id` e `device_key`. Se encontrado, deve persistir `device_id`; se não encontrado, o evento deve ser criado com `device_id=null`. 🟢

### RF-11 - Expor funil administrativo de onboarding

O sistema deve expor `GET /api/v1/analytics/admin/onboarding-funnel/?days=N` para staff/superuser, retornando período, baseline, contagens por etapa, conversão por etapa, tempo médio até ativação, principal etapa de abandono e contagem de abandonos. 🟢

### RF-12 - Restringir funil ao time interno

O funil administrativo deve permitir apenas `is_staff` ou `is_superuser`; usuários comuns devem receber `PermissionDenied`. 🟢

### RF-13 - Limitar janela do funil

O parâmetro `days` deve ser convertido para inteiro e limitado entre 1 e 180; valores inválidos devem cair para 30. 🟢

### RF-14 - Calcular baseline pelo primeiro passo

O baseline do funil deve ser o número de lojas distintas com `onboarding_step_viewed` na etapa `generate_token` dentro da janela. 🟢

### RF-15 - Calcular conversão por etapa

Para cada etapa em `STEP_ORDER`, o sistema deve contar lojas distintas com `onboarding_step_completed` e calcular percentual sobre o baseline arredondado. 🟢

Ordem das etapas: `generate_token`, `install_agent`, `agent_online`, `connect_camera`, `configure_roi`, `store_active`. 🟢

### RF-16 - Calcular tempo médio até ativação

O tempo médio deve considerar eventos `onboarding_completed` com `time_spent_ms` inteiro e positivo, convertendo para minutos e arredondando para duas casas. 🟢

### RF-17 - Calcular principal drop-off

O principal drop-off deve ser a etapa mais frequente em eventos `onboarding_dropped` dentro da janela. 🟢

### RF-18 - Cliente frontend best-effort

O frontend deve chamar os endpoints via `analyticsService` com `timeoutCategory: "best-effort"` e `noRetry: true`, evitando bloquear o fluxo principal quando a telemetria falhar. 🟢

### RF-19 - Eventos emitidos pelo wizard de ativação

O wizard deve emitir `onboarding_step_viewed` ao trocar de etapa, `onboarding_step_completed` ao avançar, `onboarding_dropped` ao desmontar sem conclusão e `onboarding_completed` ao finalizar onboarding. 🟢

### RF-20 - Eventos emitidos pelo dashboard

O dashboard deve emitir `agent_update_triggered` quando um update é solicitado e `agent_update_succeeded` quando a versão instalada passa a coincidir com a versão alvo pendente. 🟢

Não há evidência de emissão frontend de `agent_update_failed`, embora o backend aceite esse evento. 🔴

## Requisitos Não Funcionais

### Segurança

Todos os endpoints usam `IsAuthenticated`. 🟢

Os endpoints de ingestão ainda fazem autorização por loja usando roles específicas (`ALLOWED_READ_ROLES` ou `ALLOWED_MANAGE_ROLES`). 🟢

O funil administrativo exige staff/superuser. 🟢

### Performance

A ingestão em lote de onboarding usa `bulk_create(rows, batch_size=500)`. 🟢

Os modelos possuem índices por `created_at`, por `store + created_at` e por combinações usadas no funil. 🟢

O frontend marca as chamadas como best-effort e sem retry. 🟢

### Observabilidade

Os eventos persistem `metadata`, `session_id`, `technical_status`, versões do agent e `user_agent`, permitindo análise posterior. 🟢

Não há logging explícito nos endpoints de analytics para falhas de validação ou inserção. 🟡

### Compatibilidade

As rotas públicas do módulo estão sob `/api/v1/analytics/`. 🟢

`StoreDailyMetrics` existe no app, mas não há endpoints ativos lidos nesta unit que o exponham ou materializem diretamente. 🟢

## Critérios de Aceitação

### CA-01 - Onboarding válido

Dado um usuário autenticado com papel permitido na loja, quando enviar `store_id`, `event_type=onboarding_step_viewed` e `step=install_agent`, então o sistema deve criar um `OnboardingEvent` e retornar HTTP 201 com `{ ok: true, inserted: 1 }`. 🟢

### CA-02 - Onboarding inválido

Dado um usuário autenticado, quando enviar `event_type=invalid`, então o sistema deve retornar HTTP 400 com mensagem de `event_type inválido`. 🟢

### CA-03 - Lote de onboarding

Dado um payload `{ events: [...] }` com múltiplos eventos válidos, quando a requisição for processada, então o sistema deve inserir todos os eventos via `bulk_create` e retornar a quantidade inserida. 🟢

### CA-04 - Loja inexistente

Dado um `store_id` inexistente, quando qualquer endpoint de ingestão for chamado, então o sistema deve retornar HTTP 404 com `Loja não encontrada.`. 🟢

### CA-05 - Agent event válido

Dado um usuário autenticado com papel de gestão na loja, quando enviar `agent_update_triggered` com `device_key`, então o sistema deve criar `AgentEvent` e retornar HTTP 201 com `event_id` e `event_type`. 🟢

### CA-06 - Funil staff

Dado um usuário staff, quando consultar `/api/v1/analytics/admin/onboarding-funnel/?days=30`, então o sistema deve retornar `baseline_stores`, `funnel_counts`, `conversion`, `avg_time_to_active_min`, `top_dropoff_step` e `dropoff_counts`. 🟢

### CA-07 - Funil usuário comum

Dado um usuário comum, quando consultar o funil administrativo, então o sistema deve negar acesso. 🟢

### CA-08 - Telemetria best-effort

Dado uma falha no endpoint de analytics durante o wizard ou dashboard, quando o frontend chamar `analyticsService`, então o fluxo principal não deve ser interrompido porque os chamadores capturam erro com `.catch(() => undefined)`. 🟢

## MoSCoW

### Must

- Registrar eventos de onboarding válidos. 🟢
- Registrar eventos de atualização do agent válidos. 🟢
- Aplicar autenticação e autorização por loja. 🟢
- Expor funil administrativo para staff/superuser. 🟢

### Should

- Manter chamadas frontend como best-effort. 🟢
- Persistir `metadata`, `session_id`, `technical_status` e versões para investigação. 🟢
- Usar índices para consultas temporais e por loja. 🟢

### Could

- Emitir `agent_update_failed` a partir do frontend ou backend de update. 🔴
- Expor endpoints para `StoreDailyMetrics`. 🔴
- Adicionar logs estruturados no app analytics. 🟡

### Won't

- Reimplementar nesta unit a ingestão de visão `vision.metrics.v1`. 🟢
- Substituir `journey_events` do app `core`; analytics e journey coexistem. 🟢

## Lacunas

| Lacuna | Impacto | Confiança |
|---|---|---|
| `agent_update_failed` é aceito mas não foi encontrado emissor frontend/backend no recorte lido. | Funil de update pode superestimar sucesso ou não medir falhas. | 🔴 |
| `StoreDailyMetrics` parece modelo legado/planejado sem endpoint ativo nesta unit. | Pode haver dívida de produto ou tabela órfã. | 🟡 |
| Não há deduplicação de eventos de onboarding por `session_id + step + event_type`. | Reenvios ou re-renderizações podem inflar métricas. | 🟡 |
| `metadata` aceita qualquer objeto sem validação de tamanho/esquema. | Risco de payload excessivo ou cardinalidade ruim. | 🟡 |
