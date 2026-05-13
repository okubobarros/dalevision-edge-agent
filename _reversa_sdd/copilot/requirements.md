# Copilot - Requirements

## Escopo

Esta unit especifica o módulo `apps.copilot` do repositório `dale-vision`, responsável por contexto operacional, insights, conversa assistida, intelligence feed, ações/outcomes, value ledger, políticas operacionais, perfis de loja e integrações WhatsApp/n8n. 🟢

O Edge Agent não contém lógica de Copilot; ele alimenta métricas/eventos que o backend consome indiretamente via `traffic_metrics`, `conversion_metrics`, `vision_atomic_events`, `detection_events` e `event_receipts`. 🟢

## Evidências

| Evidência | Papel | Confiança |
|---|---|---|
| `C:\workspace\dale-vision\apps\copilot\models.py` | Modelos persistidos do Copilot | 🟢 |
| `C:\workspace\dale-vision\apps\copilot\views.py` | Endpoints principais do Copilot | 🟢 |
| `C:\workspace\dale-vision\apps\copilot\views_intelligence_feed.py` | Feed consolidado e ações do feed | 🟢 |
| `C:\workspace\dale-vision\apps\copilot\views_whatsapp.py` | Webhook Meta WhatsApp | 🟢 |
| `C:\workspace\dale-vision\apps\copilot\services\_core.py` | Materialização de contexto, janelas, insights e report 72h | 🟢 |
| `C:\workspace\dale-vision\apps\copilot\services\intelligence_feed.py` | Consolidação, scoring, dedupe e paginação do feed | 🟢 |
| `C:\workspace\dale-vision\frontend\src\services\copilot.ts` | Cliente frontend do Copilot | 🟢 |
| `C:\workspace\dale-vision\frontend\src\types\copilot.ts` | Contratos TypeScript do Copilot | 🟢 |
| `C:\workspace\dale-vision\backend\urls.py` | Inclusão de `apps.copilot.urls` em `/api/v1/` | 🟢 |
| `C:\workspace\dale-vision\backend\settings.py` | App instalado e configuração OpenRouter | 🟢 |

## Requisitos Funcionais

### RF-01 - Expor briefing diário

O sistema deve expor `GET /api/v1/copilot/daily-briefing/`, com `store_id` opcional, retornando estado, headline, mensagem, métricas, CTA e momento de orgulho. 🟢

Quando `store_id` for informado, deve validar a loja e exigir papel de leitura. 🟢

Quando o usuário não possuir organizações e não for interno, deve retornar briefing calmo vazio em HTTP 200. 🟢

### RF-02 - Expor contexto de dashboard por loja

O sistema deve expor `GET /api/v1/copilot/stores/<store_id>/context/`, exigir leitura da loja, reutilizar snapshot recente salvo por até 300 segundos e materializar novo snapshot quando necessário ou quando `force=1|true|yes`. 🟢

### RF-03 - Resolver estado operacional

O contexto deve incluir `account_state`, `operational_state`, trial, cobertura de câmeras/edge, perfil de loja e métricas das últimas 24h. 🟢

Estados operacionais confirmados: `not_started`, `setup_in_progress`, `collecting_data`, `report_ready`, `operating`, `incident`. 🟢

### RF-04 - Materializar janela operacional

O serviço deve materializar `OperationalWindowHourly` por loja e bucket de 5 ou 10 minutos, derivando métricas de fluxo, fila, staff, alertas críticos, eventos de visão, risco estimado e confiança. 🟢

A chave lógica deve ser `(store_id, ts_bucket, window_minutes)`. 🟢

### RF-05 - Gerar insights operacionais

O sistema deve gerar candidatos de insight a partir de cobertura edge/câmeras, fila média, conversão, queda de fluxo e alertas abertos. 🟢

Ao materializar insights, deve arquivar insights ativos anteriores da loja e criar novos registros ativos. 🟢

### RF-06 - Listar insights por loja e rede

O sistema deve expor `GET /api/v1/copilot/stores/<store_id>/insights/` e `GET /api/v1/copilot/network/insights/`, retornando insights ativos e não expirados. 🟢

O endpoint por loja deve aceitar `refresh=1|true|yes` para recalcular insights. 🟢

### RF-07 - Gerar relatório 72h

O sistema deve expor `GET /api/v1/copilot/stores/<store_id>/report-72h/`, retornar relatório existente ou materializar novo, anexar readiness e sugerir próximo refresh em segundos. 🟢

Quando não houver relatório materializado, deve retornar payload `pending` com `next_refresh_suggested_seconds=300`. 🟢

### RF-08 - Suportar conversa com o Copilot

O sistema deve expor `GET/POST /api/v1/copilot/stores/<store_id>/conversations/`, listar mensagens recentes e criar mensagem do usuário mais resposta do assistente. 🟢

`content` deve ter limite de 4000 caracteres e `session_id` limite de 128 caracteres. 🟢

### RF-09 - Usar LLM externo com fallback determinístico

Ao responder conversa, o sistema deve chamar OpenRouter se `OPENROUTER_API_KEY` estiver configurada; caso contrário, ou em falha, deve retornar resposta determinística baseada no contexto operacional. 🟢

O prompt de sistema deve exigir português do Brasil, tom executivo, uso exclusivo de dados informados, aviso de baixa confiança e restrição LGPD contra identificação de pessoas/rostos. 🟢

### RF-10 - Atualizar plano de staff

O sistema deve expor `POST /api/v1/copilot/stores/<store_id>/actions/staff-plan/`, exigir papel de gestão, atualizar `Store.employees_count` e registrar mensagens de conversa/auditoria operacional. 🟢

### RF-11 - Criar e listar ActionOutcome por loja

O sistema deve expor `GET/POST /api/v1/copilot/stores/<store_id>/actions/outcomes/`, exigir leitura para GET e gestão para POST, listar com resumo agregado e criar outcomes com baseline/outcome/impacto/confiança. 🟢

### RF-12 - Atualizar ActionOutcome por loja

O sistema deve expor `PATCH /api/v1/copilot/stores/<store_id>/actions/outcomes/<outcome_id>/`, exigir gestão, atualizar status, resultado, comentário, impacto realizado, confiança e campos de entrega. 🟢

Quando `status=completed` e `completed_at` não for informado, deve preencher `completed_at` com `now`. 🟢

### RF-13 - Sincronizar Value Ledger ao alterar outcome

Criação, atualização e callback de `ActionOutcome` devem chamar `_sync_value_ledger_from_outcome`. 🟢

### RF-14 - Callback externo de ActionOutcome

O sistema deve expor endpoint AllowAny de callback de outcome, validar token de serviço n8n/integração, localizar outcome por `action_event_id` ou `id`, atualizar entrega, falha, conclusão e metadados de callback. 🟢

Se token for inválido, deve retornar `403 FORBIDDEN`; se outcome não existir, `404 ACTION_OUTCOME_NOT_FOUND`. 🟢

Lacuna: a rota de callback não aparece em `apps/copilot/urls.py` lido, embora existam view e testes para `/api/v1/copilot/actions/outcomes/callback/`. 🔴

### RF-15 - Expor Value Ledger por loja

O sistema deve expor `GET /api/v1/copilot/stores/<store_id>/value-ledger/daily/?days=N`, exigir leitura, limitar `days` entre 1 e 730, calcular totais, taxas, status de valor, tier de confiança e saúde do pipeline. 🟢

### RF-16 - Expor outcomes e ledger em nível rede

O sistema deve expor endpoints de rede para outcomes, value ledger diário e ranking de eficiência, filtrando por organizações do usuário ou permitindo interno staff/superuser. 🟢

Usuário sem escopo de org e não interno deve receber payload vazio HTTP 200. 🟢

### RF-17 - Calcular aceite Sprint 2 do ledger

O ledger de rede deve calcular `sprint2_acceptance` com decisão `GO`/`NO-GO` com base em cobertura mínima, taxa máxima stale e taxa máxima no_data. 🟢

### RF-18 - Calcular ranking de eficiência

O ranking de rede deve combinar alertas críticos/avisos abertos, taxa de conclusão, taxa de recuperação e confiança média para produzir `efficiency_score`, banda `leader|stable|at_risk`, fatores de contribuição e rank. 🟢

O parâmetro `anonymized` deve controlar nomes exibidos ou usar `StoreProfile.defaults_json.ranking_anonymized` como fallback. 🟢

### RF-19 - Expor StoreProfile

O sistema deve expor `GET/PATCH/PUT /api/v1/copilot/stores/<store_id>/profile/`, retornando defaults quando perfil não existir e permitindo upsert com papel de gestão. 🟢

### RF-20 - Expor política operacional de rede/loja

O sistema deve expor `GET/POST /api/v1/copilot/network/policies/`, resolver `org_id` do usuário, permitir política de rede (`store_id=null`) ou específica por loja, criar default quando ausente e atualizar via serializer. 🟢

Lacuna: não há chamada explícita a `require_store_role` nesse endpoint para `store_id` específico; a autorização parece baseada apenas em pertencer à primeira organização do usuário. 🟡

### RF-21 - Expor Intelligence Feed

O sistema deve expor `GET /api/v1/dashboard/intelligence-feed/`, consolidando `detection_events`, `copilot_operational_insights`, `action_outcome` e `notification_logs`, com scope, status, evidência, resolvidos, limite e cursor. 🟢

O endpoint deve retornar payload vazio em HTTP 200 para usuário sem org e não interno, ou em falha interna de montagem. 🟢

### RF-22 - Executar ações no Intelligence Feed

O sistema deve expor `POST /api/v1/dashboard/intelligence-feed/<feed_item_id>/actions/`, aceitar ações `acknowledge`, `dispatch_whatsapp`, `dispatch_email`, `open_playbook`, `mark_in_progress`, `resolve`, `dismiss`, `reopen`, `assign_owner`, exigir gestão da loja e registrar audit log best-effort. 🟢

Para dispatch, deve criar `ActionOutcome` e disparar n8n best-effort via `send_event_to_n8n`. 🟢

### RF-23 - Webhook WhatsApp Meta

O sistema deve expor webhook Meta WhatsApp para verificação GET e eventos POST, com tratamento de cliques de resolução sobre outcomes. 🟢

### RF-24 - Jobs operacionais

O sistema deve oferecer comandos para materializar contexto/insights/relatórios, janelas operacionais, limpar retenção, reconstruir ledger, gerar relatórios de aceite/health/evidence pack e motores MVP tático/ROI. 🟢

## Requisitos Não Funcionais

### Segurança

Endpoints de usuário usam `IsAuthenticated`, exceto webhook/callbacks externos com token próprio ou verificação Meta. 🟢

A maioria dos endpoints por loja usa `require_store_role` com `ALLOWED_READ_ROLES` ou `ALLOWED_MANAGE_ROLES`. 🟢

Prompt LLM inclui restrição LGPD para não identificar pessoas nem inferir identidade por rosto. 🟢

### Performance

Contexto de dashboard reutiliza snapshot por até 300 segundos. 🟢

Intelligence Feed limita itens brutos por fonte a 200, limita `limit` de resposta a 100 e usa cursor offset simples. 🟢

Endpoints de listagem limitam `limit` entre 1 e 200 em outcomes. 🟢

### Resiliência

Conversa usa fallback determinístico se OpenRouter estiver sem chave ou falhar. 🟢

Intelligence Feed retorna feed vazio em falha de montagem, logando exceção. 🟢

Notification logs ausentes geram warning e enriquecimento vazio. 🟢

### Observabilidade

Ações do feed tentam registrar `AuditLog`; falha de audit não bloqueia ação. 🟢

Outcomes registram status de entrega, provider message id, erro, timestamps e impacto financeiro. 🟢

## Critérios de Aceitação

### CA-01 - Contexto com cache

Dado snapshot recente para uma loja, quando o usuário consultar contexto sem `force`, então o sistema deve retornar `snapshot_json` sem rematerializar. 🟢

### CA-02 - Conversa sem OpenRouter

Dado ausência de `OPENROUTER_API_KEY`, quando usuário enviar mensagem ao Copilot, então o sistema deve criar mensagem user, criar mensagem assistant determinística e retornar HTTP 201. 🟢

### CA-03 - ActionOutcome concluído

Dado outcome existente, quando PATCH enviar `status=completed`, `outcome_status=resolved`, comentário, impacto e confiança, então o sistema deve atualizar campos, preencher `completed_at` se necessário, sincronizar ledger e retornar HTTP 200. 🟢

### CA-04 - Callback inválido

Dado token de serviço inválido, quando callback de outcome for chamado, então deve retornar 403 com `code=FORBIDDEN`. 🟢

### CA-05 - Ledger sem dados

Dado loja sem linhas de ledger no período, quando consultar ledger diário, então deve retornar `pipeline_health.status=no_data`, totais zerados e items vazios. 🟢

### CA-06 - Intelligence Feed resiliente

Dado falha interna ao montar feed, quando endpoint for chamado, então deve retornar HTTP 200 com `items=[]`, `has_more=false` e counts zerados. 🟢

### CA-07 - Ação de feed inválida

Dado `feed_item_id` com prefixo desconhecido ou UUID inválido, quando ação for enviada, então deve retornar 400 `INVALID_FEED_ITEM_ID`. 🟢

### CA-08 - Política operacional sem org

Dado usuário sem organização, quando consultar ou atualizar política operacional, então deve receber 403 `No organization associated.`. 🟢

## MoSCoW

### Must

- Contexto de dashboard, insights, report 72h e conversa por loja. 🟢
- RBAC por loja em leituras e ações críticas. 🟢
- ActionOutcome e Value Ledger sincronizados. 🟢
- Intelligence Feed consolidado com ações. 🟢
- Fallback determinístico do Copilot quando LLM falhar. 🟢

### Should

- Snapshot de contexto com TTL. 🟢
- Jobs de materialização e auditoria de ledger. 🟢
- Ranking de eficiência e visões de rede. 🟢
- Dispatch best-effort para n8n/WhatsApp. 🟢

### Could

- Adicionar assets de conversa no backend para rotas chamadas pelo frontend. 🔴
- Consolidar rotas de callback testadas mas ausentes do `urls.py`. 🔴
- Reforçar autorização de policy específica por loja. 🟡

### Won't

- Executar reconhecimento facial ou identificação biométrica. 🟢
- Depender exclusivamente de LLM para operação crítica; há fallback determinístico. 🟢

## Lacunas

| Lacuna | Impacto | Confiança |
|---|---|---|
| Frontend chama `conversation-assets`, mas rota correspondente não aparece em `apps/copilot/urls.py`. | Upload/lista de anexos pode quebrar em 404. | 🔴 |
| View/testes de callback de ActionOutcome existem, mas rota não aparece no `urls.py` lido. | Integração n8n/externa pode não alcançar callback. | 🔴 |
| `sync_operational_insights.py` importa `StoreProfile` de `apps.core.models`, mas o modelo real lido está em `apps.copilot.models`. | Comando legado pode falhar ou estar obsoleto. | 🔴 |
| `NetworkOperationalPolicyView` não usa `require_store_role` para store específica. | Usuário de org pode alterar policy de loja sem papel granular. | 🟡 |
| `CopilotConversationView` grava metadata `mode=deterministic` mesmo quando resposta pode ter vindo do OpenRouter. | Observabilidade do modo real do assistente fica imprecisa. | 🟡 |
