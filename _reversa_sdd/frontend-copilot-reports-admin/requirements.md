# frontend-copilot-reports-admin

> Template do arquivo `requirements.md`. Foca no QUE a unit faz, não no como.

## Visão Geral
Módulo que agrupa três subsistemas de alto valor estratégico da plataforma DaleVision: (1) o **Copilot Hub** — interface de IA conversacional com suporte a upload de ativos, tarefas e Audit Trail; (2) o módulo de **Reports** — painel executivo de análise de impacto, cobertura operacional, ledger de valor e ranking de eficiência; (3) o **Admin Control Tower** — visão de saúde do SaaS restrita ao time interno, com drilldowns por métrica, calibração, suporte e funil de produto.

## Responsabilidades
- **Copilot Hub**: Enviar mensagens ao Copilot com contexto operacional, renderizar respostas estruturadas, gerir tarefas Kanban (todo/in_progress/done) em localStorage, e gerenciar assets de conversa. Suporta modos de investigação (network/store/staff/roi).
- **Reports**: Exibir métricas de operação, calcular valor recuperado, gerar score consolidado de operação, exportar relatórios, exibir ranking de eficiência e acionar intervention cards via Copilot/WhatsApp.
- **Admin Control Tower**: Exibir KPIs SaaS (usuários, orgs, incidentes), apresentar funil de produto, gerenciar calibrações e acesso de suporte, e verificar qualidade da visão computacional e pipeline observability.

## Regras de Negócio

### Copilot Hub
- `storeId = ?store_id ?? (selectedStoreId === "all" ? null : selectedStoreId)` — params da URL têm precedência 🟢
- Sem loja selecionada: copilot responde com mensagem estática sem chamar API 🟢
- Tarefas e assets salvos com fallback no `localStorage` 🟢
- Contexto de URL (`contextPrompt`, `contextTemplate`) injeta mensagens iniciais e tarefas automaticamente apenas uma vez 🟢
- `operationalState` calculado localmente baseado em eventos críticos/ativos 🟢
- Upload sem loja salva asset apenas localmente (status="ready") 🟢

### Reports
- `consolidatedScore` baseado em fórmula híbrida (fila, conversão, confidence) 🟢
- `revenueAtRiskToday` derivado de custo ocioso + fila ou potencial estimado 🟢
- Intervention cards acionam `triggerCopilotAction` ou `handleDelegateStoreIntervention` via WhatsApp 🟢

### Admin Control Tower
- Gate de acesso: `isInternalAdmin = is_staff || is_superuser || is_internal_admin || @dalevision.com email` 🟢
- Permissão via `grantSupportMutation` concede acesso temporário (2h) 🟢
- Todas as queries têm `refetchInterval: 300_000` (5 minutos) 🟢

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | Copilot Hub: chat com API por loja | Must | IA responde mantendo a sessão do chat em foco |
| RF-02 | Copilot Hub: modos de investigação | Must | Exibe modos e botões rápidos de prompts (rede/loja/roi) |
| RF-03 | Copilot Hub: tarefas Kanban persistidas | Should | Tarefa arrastada é mantida após reload |
| RF-04 | Copilot Hub: auto-iniciar conversa por URL | Must | `?prompt=X` escreve "X" e envia à IA ao carregar |
| RF-05 | Reports: Ledger de valor recuperado | Must | Compara MoM e YoY em base financeira real |
| RF-06 | Reports: Intervention cards delegáveis | Should | Clicar em "Delegar" notifica o WhatsApp/Copilot da loja |
| RF-07 | Admin: KPIs SaaS com drilldown | Must | Dashboard carrega e métricas expõem detalhes no clique |
| RF-08 | Admin: Score de qualidade de dados | Should | Exibe health da base de payloads por loja |
| RF-09 | Admin: Gerenciar calibrações/suporte | Must | Usuário interno clica para conceder 2h e API autoriza |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Resiliência | Fallback para localstorage no Kanban e assets sem loja | `Copilot.tsx:200-201`, `Copilot.tsx:475-479` | 🟢 |
| Performance | Refetch assíncrono e constante no painel admin (5min) para aliviar DB | `AdminControlTower.tsx:177-270` | 🟢 |
| Segurança | RBAC local com short-circuit para admin (`isInternalAdmin`) e grant explícito temporário | `AdminControlTower.tsx:168-174`, `279` | 🟢 |
| Disponibilidade| Falhas nas queries analíticas de rede não impedem fallback por query padrão em Reports | `Reports.tsx:671-696` | 🟢 |

## Critérios de Aceitação

```gherkin
Dado que a URL da página do Copilot possui "?prompt=avaliar_caixa"
Quando a interface renderizar completamente
Então a mensagem "avaliar_caixa" é enviada à API automaticamente 
E a conversa é vinculada à loja no escopo ativo

Dado que o usuário logado possui e-mail de domínio não-interno
Quando ele tentar acessar o componente AdminControlTower
Então a aplicação bloqueia os dados analíticos
E não dispara os fetch calls de KPI
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Interface Copilot Hub | Must | O núcleo da interação com a IA para a operação diária |
| Reports KPIs e Ledger | Must | Fundamental para justificar o ROI da plataforma para C-levels |
| Admin Health Dashboard | Must | Necessário para sustentar o SaaS e garantir SLA operacional |
| Gerenciamento Kanban | Should | Recurso valioso, mas pode ser suprimido caso de falha de storage temporária |
| Intervention cards via Whats | Should | Alto valor de engajamento humano, porém não vital para IA |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `frontend/src/pages/Copilot/Copilot.tsx` | Componentes do Hub e Hooks | 🟢 |
| `frontend/src/pages/Reports/Reports.tsx` | Dashboard Executivo e Cálculo MoM | 🟢 |
| `frontend/src/pages/Admin/AdminControlTower.tsx` | Painel Interno e Gates | 🟢 |
| `frontend/src/services/copilot.ts` | Chamadas de IA e Assets | 🟡 |
| `frontend/src/services/admin.ts` | Chamadas de Health e Grants | 🟡 |
