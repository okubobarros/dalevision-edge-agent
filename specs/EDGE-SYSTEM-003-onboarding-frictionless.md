# EDGE-SYSTEM-003 - Onboarding Frictionless

> Especificacao de produto + arquitetura para ativacao de loja/cameras com zero terminal e zero conhecimento tecnico de rede por parte do lojista.

## Meta
- Titulo / ID: `EDGE-SYSTEM-003 - Onboarding Frictionless`
- Objetivo: reduzir friccao de ativacao para fluxo guiado no app web, com handshake automatico via Edge e descoberta assistida de cameras.
- Estado: `draft`
- Ultima atualizacao: `2026-04-14`

## 1. Problema e resultado esperado
- **Problema atual**:
  - Ativacao depende de passos manuais tecnicos (terminal/script).
  - Confirmacoes manuais no frontend geram falso positivo ("ja conclui") e quebra de funil.
  - Suporte recebe casos inconclusivos por falta de estados objetivos e telemetria de etapa.
- **Resultado esperado (wow moment)**:
  - Usuario baixa setup e executa com duplo clique.
  - Tela web avanca automaticamente ao detectar primeiro heartbeat valido do agente.
  - CFTV encontrado automaticamente, com fallback manual simples.
  - Primeira camera configurada em minutos, com diagnostico de 72h iniciado.

## 2. Escopo
- **Dentro**:
  - Download inteligente do instalador por loja.
  - Handshake automatico web <-> backend <-> edge.
  - Descoberta de cameras assistida por Edge.
  - Modelo "camera como sensor" com `indicators[]`.
  - Telemetria de funil e codigos curtos de erro.
- **Fora**:
  - Treinamento/modelagem de IA cloud para calibracao fina.
  - Politica comercial de rollout por segmento.
  - Mudancas em protocolo legado de heartbeat fora de campos opcionais.

## 3. Restricoes duras
- Nao quebrar compatibilidade do protocolo atual de heartbeat/camera health.
- Nao exigir CMD/PowerShell para ativacao de loja.
- Nao logar token, senha RTSP ou segredo em texto plano.
- Fluxo deve oferecer fallback guiado quando autodiscovery falhar.

## 4. Jornada do usuario (UX alvo)
1. Usuario cria loja e aceita termos (incluindo bases LGPD aplicaveis).
2. Clica em "Baixar Setup".
3. Instala o `.exe` localmente com fluxo guiado.
4. Frontend exibe "Aguardando conexao do Edge..." com polling de status.
5. Ao primeiro heartbeat valido, frontend mostra sucesso e avanca automaticamente.
6. Usuario escolhe camera descoberta (ou adiciona manualmente).
7. Usuario marca indicadores por camera (ex.: `flow`, `queue`, `occupancy`).
8. Sistema confirma inicio da calibracao/diagnostico de 72h.

Contrato de handoff web (obrigatorio):
- A conclusao do LGPD deve redirecionar diretamente para `/app/dashboard?openEdgeSetup=1&store_id={store_id}`.
- Nao deve haver retorno intermediario para `/onboarding` apos conclusao do wizard.
- O modal de ativacao Edge deve abrir automaticamente ao chegar no dashboard.

## 5. Estados de ativacao (fonte de verdade)
- `pending_download`: loja criada, aguardando download.
- `pending_install`: setup baixado, aguardando primeiro contato do edge.
- `agent_seen`: primeiro heartbeat aceito, aguardando estabilidade minima.
- `ready_for_cameras`: handshake estavel e apto a configurar cameras.
- `activation_completed`: primeira camera valida e indicadores persistidos.
- `activation_failed`: falha terminal da etapa (com `error_code`).

Regras:
- `agent_seen` nao equivale a ativacao concluida.
- `ready_for_cameras` exige janela minima de heartbeats com sucesso (SLO abaixo).
- Contrato canonico versionado em `docs/harness/contracts/CONTRACT-ACTIVATION-STATE-V1.md`.

## 6. Contratos e APIs

### 6.1 Smart Download
- `GET /api/v1/stores/{store_id}/download-agent`
- Resposta:
  - URL assinada e expirada para download.
  - Nome de arquivo amigavel com identificador curto de onboarding (nao token pleno).
  - Metadados: `expires_at`, `onboarding_ref`, `installer_version`.

Observacao de seguranca:
- Nao embutir token de longa duracao em nome de arquivo.
- Preferir token efemero de uso unico ligado a `store_id` + expira curta.

### 6.2 Status de ativacao para frontend
- `GET /api/v1/stores/{store_id}/status`
- Resposta minima:
  - `activation_state`
  - `agent_online`
  - `last_heartbeat_at`
  - `discovered_devices_count`
  - `error_code` (quando houver)
  - `next_recommended_action`

### 6.3 Heartbeat edge
- Endpoint atual de heartbeat permanece compativel.
- Campos novos devem ser opcionais (ex.: `onboarding_ref`, `agent_capabilities`).

### 6.4 Camera config cloud-edge
- Payload de cameras deve incluir:
  - `camera_id`
  - `name`
  - `rtsp_url` (protegido/sanitizado fora de logs)
  - `indicators: string[]`
  - `schema_version`

Compatibilidade:
- Se `indicators` ausente, backend fornece default definido por produto.
- Edge deve tolerar payload legado sem quebrar processamento.

## 7. Arquitetura por repositorio

### 7.1 Backend (Django/PostgreSQL)
- Persistir `indicators` no modelo de camera (`ArrayField` ou `JSONField`).
- Expor `indicators` em serializers e endpoints de camera.
- Implementar status de onboarding por `activation_state`.
- Validar heartbeat para transicao de estado (`pending_install` -> `agent_seen` -> `ready_for_cameras`).
- Integrar resultado de autodiscovery reportado pelo Edge.

### 7.2 Frontend (React)
- Wizard sem botao de confirmacao manual "ja conclui instalacao".
- Polling de status (ex.: 3s) com auto-advance por estado.
- UI clara de erro com codigo curto e orientacao leiga.
- Form de camera envia `indicators[]` no POST/PUT.

### 7.3 Edge Agent (Python + setup installer)
- Instalacao silenciosa/guiada sem terminal manual.
- Bootstrap le configuracao inicial, autentica e inicia heartbeat.
- Scanner LAN rapido para portas de CFTV comuns e envio de resultados.
- Worker de visao instancia pipelines conforme `indicators[]` por camera.

## 8. Sensores (feedback loop)
- Eventos obrigatorios:
  - `onboarding_started`
  - `agent_installer_downloaded`
  - `agent_first_heartbeat`
  - `camera_discovered`
  - `camera_validated`
  - `activation_completed`
  - `activation_failed`
- Codigos de erro curtos:
  - `NVR_AUTH_FAIL`
  - `NVR_UNREACHABLE`
  - `RTSP_TIMEOUT`
  - `HEARTBEAT_REJECTED`
  - `DOCTOR_SHARE_FAIL`

## 9. SLOs e metas iniciais
- `activation_success_rate >= 90%`
- `median_time_to_activation < 15 min`
- `doctor_share_success_rate >= 95%`
- `inconclusive_diagnosis_rate < 10%`
- Tempo maximo para auto-advance apos primeiro heartbeat valido: `<= 10s` (polling incluido).

## 10. LGPD e governanca minima
- Edge processa video localmente; cloud recebe metadados/eventos.
- Sem reconhecimento facial por padrao.
- Logs e artefatos de diagnostico devem mascarar segredos.
- Onboarding deve registrar aceite de termos e base legal declarada pelo controlador.

## 11. Riscos e mitigacoes
- **Falso online**: heartbeat unico isolado.
  - Mitigar com janela de estabilidade para `ready_for_cameras`.
- **Autodiscovery incompleto**: rede segmentada/bloqueios.
  - Mitigar com fallback manual guiado + doctor.
- **Exposicao de credencial**: token em nome de arquivo/log.
  - Mitigar com token efemero + politicas de sanitizacao.
- **Loop de handoff LGPD -> dashboard (frontend)**: retorno indevido para onboarding e perda do modal de ativacao.
  - Mitigar com contrato unico de redirecionamento e testes de nao-regressao no harness (10/10 execucoes sem rebound).

## 12. Definition of Done (DoD)
- Usuario conclui instalacao sem terminal.
- Frontend avanca automaticamente por estado real de backend.
- Primeira camera com `indicators[]` persiste no backend e chega ao edge.
- Edge aplica configuracao sem regressao de heartbeat/camera health.
- `doctor --share` permanece funcional e sem segredo.
- Eventos de funil e metricas publicados e consultaveis.

## 13. Evidencias de aceite
- Registro de execucao end-to-end em ambiente de homologacao.
- Logs sanitizados do edge e backend.
- Capturas da transicao automatica de steps no frontend.
- Payloads de camera com `indicators[]` persistidos e consumidos.
