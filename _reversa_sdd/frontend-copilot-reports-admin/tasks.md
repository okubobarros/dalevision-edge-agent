# frontend-copilot-reports-admin, Tarefas de Implementação

> Template do arquivo `tasks.md`. Foca em uma sequência de tarefas executáveis para reimplementar a unit a partir do legado, com rastreabilidade ao código original.

## Pré-requisitos
- [ ] Dependências da unit listadas em `design.md` (serviços de API `copilotService`, `storesService`, `adminService`) implementadas ou mockadas.
- [ ] Hooks e utilitários globais (`useAgent`) exportados e testados.
- [ ] Variáveis de ambiente relacionadas a analytics injetadas.

## Tarefas

### Copilot Hub

- [ ] T-01, Implementar `FormattedMessage` com renderer de blocos estruturados
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:13-51`
  - Critério de pronto: Identifica e colore 5 blocos (HIPÓTESE, EVIDÊNCIA, CAUSA, IMPACTO, AÇÃO); faz fallback seguro para texto plano se não houver marcadores.
  - Confiança: 🟢

- [ ] T-02, Implementar constantes `MODE_PROMPTS` e templates `taskTemplates`
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:78-141`
  - Critério de pronto: Estruturas de dados presentes para 4 modos de investigação e 3 templates padrões de tarefa.
  - Confiança: 🟢

- [ ] T-03, Implementar mapeadores `mapAssetKind`, `mapAssetStatus`, `normalizeApiAsset`
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:150-177`
  - Critério de pronto: Mapeadores não crasham com strings nulas ou desconhecidas; fallback de status "ready".
  - Confiança: 🟢

- [ ] T-04, Implementar React Query stack e sincronização de storeId
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:180-245`
  - Critério de pronto: Parâmetros da URL têm precedência sobre StoreContext global; queries de briefing/outcomes configuradas.
  - Confiança: 🟢

- [ ] T-05, Derivar `operationalState` e `maturityLevel`
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:249-279`
  - Critério de pronto: Retorna 'Crítico' se eventos > 3, e calcula fallback local de maturidade se o servidor falhar.
  - Confiança: 🟢

- [ ] T-06, Implementar envio de mensagem (`send`) e chat history
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:403-454`
  - Critério de pronto: Emite chamada na API usando `sessionIdRef`, salva histórico local, mostra fallback em caso de rede (store nula).
  - Confiança: 🟢

- [ ] T-07, Implementar Kanban (persistência de tarefas local)
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:394-460`, `498-511`
  - Critério de pronto: Permite mover tarefas (todo/in_progress/done), reflete na UI imutavelmente e persiste em `localStorage`.
  - Confiança: 🟢

- [ ] T-08, Implementar upload de Assets
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:462-541`
  - Critério de pronto: Mescla perfeitamente respostas da API com uploads pendentes locais (source="local").
  - Confiança: 🟢

- [ ] T-09, Consumo do Contexto Inicial (URL `contextPrompt`/`contextTemplate`)
  - Origem no legado: `frontend/src/pages/Copilot/Copilot.tsx:547-574`
  - Critério de pronto: Cria a tarefa com template e envia a primeira mensagem automaticamente, marcando em Ref para não loopar.
  - Confiança: 🟢

### Reports

- [ ] T-10, Utilitários base do Reports (Janelas e Conversões)
  - Origem no legado: `frontend/src/pages/Reports/Reports.tsx:31-110`
  - Critério de pronto: Parsers de hora e formatação BRL/Percent exportados e testados unitariamente.
  - Confiança: 🟢

- [ ] T-11, Construção das 14 Queries Operacionais
  - Origem no legado: `frontend/src/pages/Reports/Reports.tsx:210-358`
  - Critério de pronto: Queries `enabled` estritamente ligadas a não ter loja selecionada se fore de rede (ex: `networkQ`).
  - Confiança: 🟢

- [ ] T-12, Lógica Comparativa MoM/YoY e Janela Operacional de Lojas
  - Origem no legado: `frontend/src/pages/Reports/Reports.tsx:119-131`, `411-540`
  - Critério de pronto: Exibe percentual de crescimento baseado em `sumLedgerRecoveredInRange`; exclui lojas fechadas pela janela via horário do config.
  - Confiança: 🟢

- [ ] T-13, Pontuação de Consolidated Score Executiva
  - Origem no legado: `frontend/src/pages/Reports/Reports.tsx:483-540`
  - Critério de pronto: Usa fórmula exata provisoriamente, planejada para migração ao backend em débito técnico.
  - Confiança: 🟢

- [ ] T-14, Acionamento de Intervention e Custom Events
  - Origem no legado: `frontend/src/pages/Reports/Reports.tsx:569-830`
  - Critério de pronto: Acionar card envia payload pro WhatsApp ou abre aba Copilot (`dv-open-copilot`); status tracked via analytics.
  - Confiança: 🟢

### Admin Control Tower

- [ ] T-15, Segurança e Validação de Status (Gatekeeping)
  - Origem no legado: `frontend/src/pages/Admin/AdminControlTower.tsx:157-445`
  - Critério de pronto: Carrega queries globais a cada 5min apenas se for superusuário, staff, domíno validado ou api grant.
  - Confiança: 🟢

- [ ] T-16, Criação e Gestão de Calibração (Action Items)
  - Origem no legado: `frontend/src/pages/Admin/AdminControlTower.tsx:278-326`
  - Critério de pronto: Gera/cria ações de calibração (`autoGenerateCalibrationMutation`); invalida query ao invés de atualizar manualmente array.
  - Confiança: 🟢

- [ ] T-17, Drilldown Panels Interativos de KPIs do SaaS
  - Origem no legado: `frontend/src/pages/Admin/AdminControlTower.tsx:86-418`
  - Critério de pronto: Clicar no card interativo injeta nome de métrica ativa; aciona modal ou sidebar com drilldown table.
  - Confiança: 🟢

- [ ] T-18, Repair Gap Mutation & Pontuação Qualidade
  - Origem no legado: `frontend/src/pages/Admin/AdminControlTower.tsx:328-413`
  - Critério de pronto: `repairIngestionGapMutation` limpa o estado de 3 queries vinculadas na promise chain, fórmula data quality refletida na HUD.
  - Confiança: 🟢

## Débitos Técnicos e Refatorações Pós-Revisão

- [ ] TR-01, Refatorar `Reports` para consumir `StoreContext` global
  - Origem no legado: Decisão de arquitetura via Revisão.
  - Critério de pronto: Remover `selectedStore` local de Reports; a tela reage à troca de loja no header principal.
  - Confiança: 🟢

- [ ] TR-02, Migrar cálculo de Consolidated Score para o Backend
  - Origem no legado: Decisão de arquitetura via Revisão.
  - Critério de pronto: Remover fórmula do Frontend e consumir campo `consolidated_score` vindo do endpoint de resumos do Dashboard.
  - Confiança: 🟢

- [ ] TR-03, Implementar Exportação Client-Side (CSV/PDF)
  - Origem no legado: Validação via Revisão.
  - Critério de pronto: O botão de export gera relatórios processando o array em memória usando `react-csv` / `jspdf`.
  - Confiança: 🟢

- [ ] TR-04, Ajustar Fallback de Maturidade para M0 estrito
  - Origem no legado: Validação via Revisão.
  - Critério de pronto: A função `getDataMaturityLevel` deve retornar `"M0"` como segurança máxima em caso de catch de exceptions ou payloads não mapeados.
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Copilot: send sem loja aciona render local estático corretamente (sem requests falharem de bobeira).
- [ ] TT-02, Copilot: consumedContextRef não gera renders infinitos.
- [ ] TT-03, Copilot: contextTemplate só cria pendência se não houver o mesmo template engatilhado e incompleto.
- [ ] TT-04, Copilot: persistência local-only do file storage em fallback merge.
- [ ] TT-05, Reports: Teste paramétrico `consolidatedScore` (e.g. `queue=0, conv=14, conf=60 -> 82`).
- [ ] TT-06, Reports: Null checks do MoM.
- [ ] TT-07, Reports: `fallbackOperationalWindow` para estabelecimentos que não têm config preenchida, apenas footfall no banco.
- [ ] TT-08, Admin: Validar rejeição de acesso para contas de email externas não staff.

## Tarefas de Migração de Dados (se aplicável)

- [ ] TM-01, N/A - Nenhuma migração de dados pendente atrelada ao Frontend.

## Ordem Sugerida
1. Pré-requisitos de APIs em stubs/mocks localmente.
2. T-10 a T-14 (Painéis de relatórios estáticos, sem estado).
3. T-01 a T-09 (O cérebro complexo e estado do chat no Hub do Copilot, incluindo localstorage sync).
4. T-15 a T-18 (Módulo Admin e bloqueio de segurança final).

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Todas as decisões foram validadas.
