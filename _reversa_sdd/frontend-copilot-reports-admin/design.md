# frontend-copilot-reports-admin, Design Técnico

> Template do arquivo `design.md`. Foca no COMO a unit é construída, com base no código legado lido.

## Interface

### Rotas e Telas Principais

| Método/Tipo | Caminho/Componente | Entrada / Parâmetros | Saída / View | Status / Proteção |
|-------------|--------------------|----------------------|--------------|-------------------|
| View | `/app/copilot` | `?store_id`, `?prompt`, `?template`, `?event_id` | `CopilotPage` | `PrivateRoute` |
| View | `/app/reports` | Seletor interno de loja | `Reports` | `PrivateRoute` |
| View | `/app/admin` | Nenhum parâmetro principal | `AdminControlTower` | Gate `isInternalAdmin` |

### Tipos de Dados Chave

| Símbolo | Detalhe Relevante | Retorno / Estrutura | Observação |
|---------|-------------------|---------------------|------------|
| `CopilotTask` | Tarefa local Kanban | `id`, `templateKey`, `status` | `Copilot.tsx` |
| `UploadedAsset` | Arquivo do Copilot | `name`, `status`, `source`, `url` | `Copilot.tsx` |
| `DrillMetric` | Métrica de Admin | union de 20 strings | `AdminControlTower.tsx` |
| `RolloutChannelFilter`| Filtro de edge agent | `"all" \| "stable" \| "canary"`| `Reports.tsx` |

## Fluxo Principal

### 1. Copilot Hub: Inicialização e Mensageria
1. Inicializa lendo `assetsStorageKey` do `localStorage` e exibe assets locais (fallback de carregamento imediato).
2. Avalia a URL. Se `contextPrompt` existir e não foi consumido, envia mensagem automática; se `contextTemplate`, cria a tarefa no Kanban e altera estado de `consumedContextRef`.
3. Ao enviar nova mensagem (`send`), adiciona como `role: "user"`.
4. Chama a API `copilotService.sendConversationMessage` passando `session_id`, período e `storeId`.
5. Se `storeId` estiver nulo (rede completa), retorna estático local e não chama a API.
6. Ao receber a resposta, atualiza `sessionIdRef` e insere `role: "assistant"` no chat.

### 2. Reports: Stack de Queries e Cálculo de Score
1. Dispara N queries em paralelo (ex: `storesQ`, `summaryQ`, `impactQ`, `ledgerQ`, `outcomesQ`).
2. Se `selectedStore` não existir, dispara também as queries de rede (`networkQ`, `rolloutSummaryQ`, `rankingQ`).
3. Ao receber dados do `summaryQ` e `coverageQ`, calcula o `consolidatedScore` no frontend (começa com 82, aplica redutores de fila, bônus de conversão e bônus de confiança).
4. Renderiza gráficos e comparações MoM/YoY processadas no lado cliente utilizando o ledger (`ledgerMoMQ`, `ledgerYoYQ`).

### 3. Admin Control Tower: Gatekeeping e Drilldowns
1. Avalia se o usuário tem permissão via `isInternalAdmin` (`is_staff`, `is_superuser`, status API ou e-mail `@dalevision.com`).
2. Libera a UI com o hook react-query ativado (`enabled: isInternalAdmin` nas chamadas de `refetchInterval: 300_000`).
3. Ao clicar num painel (`openDrilldown`), o frontend chama a API específica para a métrica via `getControlTowerDrilldown`.

## Fluxos Alternativos

- **Sem loja selecionada no Copilot:** Não executa chamadas externas, apenas provê feedback estático de erro amigável ao invés de lançar erro fatal.
- **Falha em janela operacional:** Caso os dados de operação venham vazios para a loja, ativa o fallback `fallbackOperationalWindow(bars)` que agrupa horas com tráfego pedestre válido para encontrar horários de funcionamento.
- **Requisição de intervenção:** Ao acionar Copilot Action num card (`Reports.tsx`), emite chamadas para `alertsService` para aprovação prioritária e envia evento interno na tela `dv-open-copilot`.

## Dependências

- `copilotService`, gerencia chamadas REST do LLM, persistência de IA e assets.
- `storesService`, para puxar KPIs globais, resumos analíticos e saúdes dos Edge Agents instalados.
- `adminService`, API interna com chamadas estritas a superusuários para métricas de falha PDV e integrações em lote.
- `useAgent`, Contexto React para compartilhar o estado global da IA entre os painéis (usado no Copilot).
- `IntelligenceFeedPanel`, Componente para injetar eventos do lado no chat do Copilot Hub.

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---------|---------------------|-----------|
| Copilot sem loja selecionada responde apenas local (sem acionar LLM e poupando custos) | `Copilot.tsx:411-419` | 🟢 |
| Contexto URL `?prompt` protegido por `useRef` e `consumedContextRef` (impede loops de renderização) | `Copilot.tsx:547-574` | 🟢 |
| Janelas (MoM / YoY) calculadas pelo próprio frontend (poupa backend mas custa CPU de cliente) | `Reports.tsx:411-481` | 🟢 |
| Auth local-fallback estático para domínios institucionais de funcionário | `AdminControlTower.tsx:168-174` | 🟢 |
| Padrão permissivo de merge de estado `mapAssetStatus`, caindo pra `ready` | `Copilot.tsx:153-159` | 🟡 |

## Estado Interno

### Copilot Hub
- O estado de tarefas (`tasks: CopilotTask[]`) é mantido em sincronia via React hooks e `localStorage`, persistindo Kanban Board across reloads.
- A ID da sessão (`sessionIdRef`) é mutada silenciosamente como ref sem disparar renders e resetada ao trocar a loja.

### Reports e Admin
- O painel de relatórios mantém hooks locais agressivos (ex: `selectedStore`, `period`, `exporting` state) apartados do store global.

## Observabilidade

- Ao aprovar delegações via chat/painel, um evento de analytics customizado é disparado via função helper `trackJourneyEvent("operation_action_delegated")`.
- Audit Trails (Logs operacionais via Action Outcomes) são registrados durante a falha ou sucesso no acionamento do serviço (`createActionOutcome("failed", ...)`).

## Riscos e Débitos Técnicos (Tech Debt)

- **Unificação de StoreContext**: A tela `Reports` historicamente usava um estado próprio (`selectedStore`), o que quebrava a consistência da aba. **Resolução:** Anotado como débito técnico para refatoração obrigatória, unificando a tela com o `StoreContext` global da aplicação. 🟢
- **Cálculo de Score no Backend**: Atualmente o Score (82 pts + bônus/pênaltis) é calculado no frontend. **Resolução:** Como envolve regras de SLA, este cálculo foi classificado como débito técnico e será migrado para o backend (adicionando o campo `consolidated_score` na resposta do endpoint `/api/stores/dashboard`). 🟢
- **Exportação de Relatórios (CSV/PDF)**: O mapeamento definiu que a exportação ocorrerá preferencialmente no client-side. **Resolução:** Utilizaremos libs como `react-csv` (ou `papaparse`) para exportação em planilhas e `jspdf` para PDFs, aproveitando o payload já trafegado em tela sem sobrecarregar o backend. 🟢
- **Fallback de Maturidade de Dados**: O método `getDataMaturityLevel` tenta inferir dados, mas em caso de anomalia, **a regra oficial é assumir M0** preventivamente, não permitindo que a UI minta para cima a saúde dos dados. 🟢
