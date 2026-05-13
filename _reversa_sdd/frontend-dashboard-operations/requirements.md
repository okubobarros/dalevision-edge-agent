# frontend-dashboard-operations

## Visão Geral
Módulo responsável pelas telas de inteligência operacional da plataforma DaleVision: o Dashboard Principal (com três experiências distintas por estado da conta) e a Torre de Operações (visão 360 da rede de lojas). É o hub central após autenticação, integrando dados de câmeras, edge agent, alertas, copilot e métricas de negócio em tempo quase-real.

## Responsabilidades
- Selecionar e renderizar a experiência de dashboard adequada (Trial / Paid Setup / Paid Executive) com base no estado da conta e operação
- Gerenciar seletor de loja (individual vs. "todas as lojas" — modo rede)
- Consultar e exibir métricas operacionais: fluxo, conversão, fila, staff, receita estimada, risco financeiro
- Exibir status do edge agent e acionar `StoreActivationWizard` quando necessário
- Redirecionar para `/onboarding` quando nenhuma loja existe (sem supressão de grace period)
- Exibir e gerenciar alertas abertos com ações de resolver/ignorar
- Renderizar a Torre de Controle (`OperationsTower`) com KPIs de rede, fila de intervenção e ranking de lojas
- Disponibilizar atalho para o Copilot em múltiplos pontos da interface

## Regras de Negócio
- Se o usuário não tem lojas e o grace period de onboarding expirou (`dv_onboarding_just_completed` TTL 45s), redireciona para `/onboarding` 🟢 (`Dashboard.tsx:453-458`)
- Experiência de dashboard determinada por `getDashboardExperience()`: trial_active → `TrialDashboardView`; plan_active + operational → `PaidExecutiveDashboardView`; demais → `PaidSetupDashboardView` 🟢 (`dashboardExperience.ts:103-125`)
- `AccountState` derivado de `meStatus.has_subscription`, `meStatus.trial_active` e status das lojas 🟢 (`dashboardExperience.ts:38-57`)
- `StoreOperationalState`: `not_connected → connected_no_capture → collecting → operational`; heartbeat timeout → `technical_incident` 🟢 (`dashboardExperience.ts:59-88`)
- Edge status considera online/degraded via `connectivity_status`; fallback para campo `online` boolean; fallback para `isRecentTimestamp(last_seen_at, 120s)` 🟢 (`Dashboard.tsx:58-80`)
- Modo rede (`ALL_STORES_VALUE = "all"`) ativa queries de network e desabilita queries de loja individual 🟢 (`Dashboard.tsx:442-451`)
- `openEdgeSetup=1` na URL abre `StoreActivationWizard` automaticamente; persiste handoff em sessionStorage com TTL de 45s 🟢 (`Dashboard.tsx:352-379`)
- `activation_success=true` na URL dispara toast de sucesso e invalida cache de edge status 🟢 (`Dashboard.tsx:382-395`)
- Update do edge agent é solicitado via mutação `requestEdgeUpdate`; toast confirma início; auto-confirmação detectada por polling do `activationStatus.installed_version` 🟢 (`Dashboard.tsx:759-810`)
- Limites de câmeras por plano: trial/start/basic = 3; pro = 12; growth/enterprise = sem limite 🟢 (`Dashboard.tsx:211-221`)
- Revenue gap estimado por fórmula: `queueAbandonRate = max(0, min(35%, (avgQueue - 180s) / 1200s))`, `lostCustomers = visitors/h × abandonRate × 8h`, `revenueGap = lostCustomers × avgTicket` 🟢 (`Dashboard.tsx:169-188`)
- Planos normalizados: `trial/free` → `trial`; `basic/start/starter/paid` → `start`; `pro` → `pro`; `growth` → `growth`; `enterprise/entreprise` → `enterprise` 🟢 (`Dashboard.tsx:200-209`)
- Torre de Operações filtra intervenções por `severity in [critical, warning]` e `!resolved`; ordena críticas primeiro 🟢 (`OperationsTower.tsx:84-101`)
- `networkHealthPercent = round(onlineStores / totalStores × 100)` 🟢 (`OperationsTower.tsx:75`)
- Store ranking: lojas com conversão ≥ meta = "Top Performance"; abaixo da meta e online = "Decadência Crítica" 🟢 (`OperationsTower.tsx:105-112`)
- Edge status refetch: 15s quando offline, 30s quando online e wizard fechado, 15s quando wizard aberto; pausa quando aba oculta 🟢 (`Dashboard.tsx:641-656`)
- PDV modal: mostra interesse de integração (Vtex/Linx/VT) via WhatsApp link 🟢 (`PaidExecutiveDashboardView.tsx:426`)
- `canManageStore`: roles `owner`, `admin`, `manager` têm acesso a ações de gestão 🟢 (`Dashboard.tsx:682-684`)

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|------------|-------------------|
| RF-01 | Selecionar experiência de dashboard (Trial / PaidSetup / PaidExecutive) com base em accountState + storeState | Must | Usuário trial vê TrialDashboardView; plano ativo com operação completa vê PaidExecutiveDashboardView |
| RF-02 | Seletor de loja individual vs. rede ("Todas as Lojas") | Must | Trocar loja recarrega todos os widgets com dados da loja selecionada |
| RF-03 | Redirecionar para /onboarding se usuário sem lojas e grace period expirado | Must | Após 45s do último onboarding_just_completed, redireciona automaticamente |
| RF-04 | Exibir KPIs executivos: receita estimada, dinheiro em risco, fluxo (footfall), infraestrutura/rede | Must | Quatro cards com valores em tempo quase-real; atualização conforme período selecionado |
| RF-05 | Exibir KPIs secundários: tempo de fila, ociosidade de staff, conversão real | Must | Três métricas com badge de confiança (estimated/operational/auditable) |
| RF-06 | Gráfico de fluxo de visitantes por período (hoje / 7d / 30d) | Should | BarChart Recharts renderizado com dados de `flowSeries`; tooltip customizado |
| RF-07 | Detectar `?openEdgeSetup=1` e abrir StoreActivationWizard automaticamente | Must | Modal abre sem interação manual do usuário |
| RF-08 | Detectar `?activation_success=true` e exibir toast + invalidar cache de edge status | Must | Toast "Agente Local Conectado" exibido em ≤ 1s; queries invalidadas |
| RF-09 | Exibir e gerenciar alertas abertos com resolve/ignore | Must | Lista de eventos abertos; botões de resolver/ignorar com feedback |
| RF-10 | Solicitar update do edge agent e monitorar conclusão | Should | Mutação `requestStoreEdgeUpdate` acionada; toast de confirmação; polling detecta nova versão instalada |
| RF-11 | Torre de Operações: KPIs de rede (faturamento em risco, intervenções críticas, conversão, cobertura) | Must | 4 KPIs globais com dados do networkDashboard |
| RF-12 | Torre de Operações: Fila de Intervenção ordenada por severity | Must | Intervenções críticas exibidas primeiro; ações "Resolver com Copilot" e "Ver Detalhes da Loja" |
| RF-13 | Torre de Operações: Ranking de lojas (Top Performance vs. Decadência Crítica) | Must | Lojas ranqueadas por taxa de conversão vs. meta |
| RF-14 | Copilot panel integrado com prompt contextual | Should | Botão "Gerar Plano de Ação" navega para copilot com prompt pré-preenchido |
| RF-15 | Intelligence Feed panel na sidebar do dashboard executivo | Should | `IntelligenceFeedPanel` exibido para store ou rede |
| RF-16 | PDV integration modal com link WhatsApp | Could | Modal de interesse aberto ao clicar em "Receita Bruta"; WhatsApp link correto |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------| 
| Performance | `staleTime: 30000ms` em todas as queries de dashboard; `staleTime: 60000ms` em briefing e revenue-progress | `Dashboard.tsx:404-680` | 🟢 |
| Disponibilidade | `retry: false` em todas as queries (falha silenciosa, sem loop de retry) | `Dashboard.tsx:405-657` | 🟢 |
| Performance | Refetch de edge status suspenso quando aba oculta (`document.visibilityState === "hidden"`) | `Dashboard.tsx:642-644` | 🟢 |
| Escalabilidade | Modo rede: queries `perStoreFlowQueries` usam `useQueries` para busca paralela por loja | `Dashboard.tsx:504-519` | 🟢 |
| Performance | `StoreActivationWizard` e todas as páginas com lazy loading | `App.tsx:1-38` | 🟢 |
| Segurança | Queries de dados sensíveis condicionais a `canFetchAuth = authReady && isAuthenticated` | `Dashboard.tsx:398` | 🟢 |
| Usabilidade | Estado de operação do agente (edge) com polling adaptativo (15/30s) baseado em conectividade e visibilidade | `Dashboard.tsx:641-656` | 🟢 |

> Inferido a partir do código. Validar com equipe de operações.

## Critérios de Aceitação

```gherkin
# RF-01 — Experiência trial
Dado que o usuário tem meStatus.trial_active = true
Quando o Dashboard é carregado
Então TrialDashboardView é exibido; PaidExecutiveDashboardView não é renderizado

# RF-01 — Experiência executiva
Dado que o usuário tem has_subscription = true e storeState = "operational"
Quando o Dashboard é carregado
Então PaidExecutiveDashboardView é exibido com KPIs e gráfico de fluxo

# RF-03 — Redirect para onboarding
Dado que o usuário não tem lojas e sessionStorage["dv_onboarding_just_completed"] está ausente ou expirado (>45s)
Quando o Dashboard é carregado
Então navigate("/onboarding") é chamado

# RF-07 — Abertura automática do wizard
Dado que a URL contém ?openEdgeSetup=1
Quando o Dashboard monta
Então edgeSetupOpen = true e StoreActivationWizard é exibido sem ação manual

# RF-08 — Activation success toast
Dado que a URL contém ?activation_success=true
Quando o Dashboard monta
Então toast.success("Agente Local Conectado com Sucesso!") é exibido; store-edge-status e store-activation-status-dashboard são invalidados

# RF-12 — Fila de intervenção vazia
Dado que não há insights com severity = critical ou warning
Quando OperationsTower é carregado
Então mensagem "Fluxo Operacional Saudável" é exibida no lugar da fila
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Seleção de experiência (RF-01) | Must | Define toda a UX do produto |
| Redirect onboarding (RF-03) | Must | Crítico para não deixar usuário preso |
| KPIs executivos (RF-04, RF-05) | Must | Valor central do produto |
| Edge setup auto-open (RF-07, RF-08) | Must | Portão de ativação do produto |
| Alertas (RF-09) | Must | Diferencial operacional |
| Torre de Operações KPIs (RF-11, RF-12, RF-13) | Must | Visão de rede é feature premium |
| Seletor de loja (RF-02) | Must | Multi-store é core |
| Gráfico de fluxo (RF-06) | Should | Contexto temporal importante |
| Update do edge agent (RF-10) | Should | Manutenção da infra |
| Copilot panel (RF-14) | Should | Diferencial de IA |
| Intelligence Feed (RF-15) | Should | Decisão em tempo real |
| PDV modal (RF-16) | Could | Feature de expansão de receita |

> Prioridade inferida por frequência de chamada e posição na cadeia de dependências.

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------| 
| `frontend/src/pages/Dashboard/Dashboard.tsx` | `Dashboard`, `isRecentTimestamp`, `getConnectivityStatus`, `estimateRevenueGapFromOperations`, `normalizePlanCode`, `getDashboardExperience` calls | 🟢 |
| `frontend/src/pages/Dashboard/dashboardExperience.ts` | `getDashboardExperience`, `deriveAccountState`, `deriveStoreState` | 🟢 |
| `frontend/src/pages/Dashboard/views/PaidExecutiveDashboardView.tsx` | `PaidExecutiveDashboardView` | 🟢 |
| `frontend/src/pages/Dashboard/views/TrialDashboardView.tsx` | `TrialDashboardView` | 🟡 (não lido) |
| `frontend/src/pages/Dashboard/views/PaidSetupDashboardView.tsx` | `PaidSetupDashboardView` | 🟡 (não lido) |
| `frontend/src/pages/Dashboard/views/InfrastructureSection.tsx` | `InfrastructureSection` | 🟡 (não lido) |
| `frontend/src/pages/Dashboard/views/AlertsSection.tsx` | `AlertsSection` | 🟡 (não lido) |
| `frontend/src/pages/Operations/OperationsTower.tsx` | `OperationsTower` | 🟢 |
| `frontend/src/contexts/StoreContext.tsx` | `useStore`, `selectedStoreId`, `setSelectedStoreId` | 🟡 (não lido) |
| `frontend/src/services/stores.ts` | múltiplas queries de store/network | 🟡 |
| `frontend/src/components/StoreActivationWizard.tsx` | `StoreActivationWizard` | 🟡 |
