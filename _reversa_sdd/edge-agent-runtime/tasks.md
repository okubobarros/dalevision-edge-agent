# Edge Agent Runtime, Tarefas de Implementação

## Pré-requisitos

- [ ] 🟢 Dependências documentadas em `design.md` disponíveis: runtime Python, logger, parser CLI, paths, env loader, activation, heartbeat client, setup API, diagnostics e update.
- [ ] 🟢 Variáveis obrigatórias documentadas: `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN`, `AGENT_ID` e aliases `DALE_*` quando aplicáveis.
- [ ] 🟢 Ambiente Windows considerado para paths `%LOCALAPPDATA%` e `%APPDATA%`, com fallback para cwd em ambiente de desenvolvimento/teste.
- [ ] 🟢 Contratos de compatibilidade preservados: `heartbeat`, campos agregados de `camera_health`, logs sem segredos e mensagens diagnósticas claras.
- [ ] 🔴 SLA final de `degraded` versus erro fatal validado com operação antes de alterar thresholds em produção.

## Tarefas

- [ ] T-01, Implementar entrypoint CLI do agente.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_parse_args`
  - Critério de pronto: CLI aceita execução contínua, `--once`, `--smoke-seconds`, `doctor`, `setup-api`, `scan` e `test-rtsp` sem quebrar compatibilidade de argumentos.
  - Confiança: 🟢

- [ ] T-02, Implementar configuração de logging rotacionado.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_setup_logging`
  - Critério de pronto: logger `dalevision-edge-agent` grava mensagens com timestamp/level, usa handler rotacionado e não propaga duplicando logs.
  - Confiança: 🟢

- [ ] T-03, Implementar resolução de diretórios de runtime.
  - Origem no legado: `src/dalevision_edge_agent/paths.py` `RuntimePaths`, `resolve_runtime_paths`
  - Critério de pronto: app/config/log/cache/tmp são resolvidos por AppData ou overrides `DALE_APP_DIR`, `DALE_CONFIG_DIR`, `DALE_LOG_DIR`, `DALE_CACHE_DIR`, e criados quando ausentes.
  - Confiança: 🟢

- [ ] T-04, Implementar limpeza segura de temporários antigos.
  - Origem no legado: `src/dalevision_edge_agent/paths.py` `cleanup_old_runtime_tmp`
  - Critério de pronto: mantém versões recentes configuradas, remove diretórios antigos dentro de `runtime_tmp_root` e reporta erros sem interromper o runtime.
  - Confiança: 🟢

- [ ] T-05, Implementar carregamento e validação de ambiente.
  - Origem no legado: `src/dalevision_edge_agent/env.py` `REQUIRED_ENV`, `load_env_from_cwd`, `load_settings`
  - Critério de pronto: runtime falha com mensagem diagnóstica quando `CLOUD_BASE_URL`, `STORE_ID` ou `EDGE_TOKEN` estão ausentes; aliases `DALE_*` são aceitos.
  - Confiança: 🟢

- [ ] T-06, Implementar normalização de URL e parsing de flags/inteiros.
  - Origem no legado: `src/dalevision_edge_agent/env.py`; `src/dalevision_edge_agent/main.py` `_parse_bool_env`, `_parse_int_env`
  - Critério de pronto: `CLOUD_BASE_URL` é normalizada e flags como `EDGE_SETUP_API_ENABLED`, `VISION_ENABLED` e `AUTO_UPDATE_ENABLED` aceitam valores booleanos válidos e rejeitam inválidos com erro claro.
  - Confiança: 🟢

- [ ] T-07, Implementar `AgentState` e máquina de estado.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `AgentState`, `StateMachine`
  - Critério de pronto: estados `unprovisioned`, `activating`, `active`, `degraded`, `error` existem e toda transição registra motivo.
  - Confiança: 🟢

- [ ] T-08, Implementar gerenciador de configuração persistida.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `ConfigManager`
  - Critério de pronto: configuração é lida/escrita em JSON, respeitando `DALE_AGENT_CONFIG_PATH`, `DALE_CONFIG_DIR` e fallback para cwd.
  - Confiança: 🟢

- [ ] T-09, Implementar bootstrap de ativação integrado ao runtime.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `bootstrap_activation`
  - Critério de pronto: device já provisionado inicia `active`; token ausente sem device fica `unprovisioned`; token presente tenta ativar; 401/403/409 vira `error`.
  - Confiança: 🟢

- [ ] T-10, Implementar hidratação segura de `.env` após ativação.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `hydrate_runtime_env_from_activation_config`
  - Critério de pronto: grava `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID` quando disponíveis, sem registrar token bruto em logs.
  - Confiança: 🟢

- [ ] T-11, Implementar montagem de capabilities do agente.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_build_agent_capabilities`
  - Critério de pronto: payload de capabilities reflete setup API, onboarding blueprint/readiness, diagnostics, camera health, vision e auto-update conforme flags.
  - Confiança: 🟢

- [ ] T-12, Implementar envio de heartbeat no loop operacional.
  - Origem no legado: `src/dalevision_edge_agent/main.py` criação de `HeartbeatPayload` e `HeartbeatClient.send`
  - Critério de pronto: heartbeat inclui device key, versão, canal de update, status, uptime e contagem/campos agregados de cameras.
  - Confiança: 🟢

- [ ] T-13, Implementar transição de estado pós-heartbeat.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_next_agent_state_after_heartbeat`; `tests/test_heartbeat_state.py`
  - Critério de pronto: sucesso retorna `active`, erro de rede retorna `degraded`, 401/403 retorna `error`.
  - Confiança: 🟢

- [ ] T-14, Implementar cálculo de sleep/backoff por estado.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_heartbeat_sleep_seconds`; `tests/test_heartbeat_state.py`
  - Critério de pronto: `degraded` usa 300 segundos por padrão; demais estados respeitam intervalo ativo/backoff configurado.
  - Confiança: 🟢

- [ ] T-15, Integrar camera sync de forma não destrutiva ao runtime.
  - Origem no legado: `src/dalevision_edge_agent/main.py` fluxo de camera sync; `src/dalevision_edge_agent/cameras.py`
  - Critério de pronto: falhas recuperáveis de camera/ROI/snapshot são registradas e não encerram o loop quando `CAMERA_SYNC_FATAL=0`.
  - Confiança: 🟢

- [ ] T-16, Implementar emissão do primeiro heartbeat como evento de onboarding.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_safe_emit_onboarding_event`
  - Critério de pronto: após primeiro heartbeat OK, evento `agent_first_heartbeat` é enviado uma única vez com store, agent, status e onboarding ref quando existir.
  - Confiança: 🟢

- [ ] T-17, Integrar Setup API local ao subcomando.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_parse_args`; `src/dalevision_edge_agent/setup_api.py` `serve_setup_api`
  - Critério de pronto: `setup-api --host 127.0.0.1 --port 8787` inicia servidor local e responde JSON/arquivos conforme rotas de onboarding.
  - Confiança: 🟢

- [ ] T-18, Integrar Doctor ao subcomando.
  - Origem no legado: `src/dalevision_edge_agent/main.py` parser `doctor`; `src/dalevision_edge_agent/diagnostics.py` `run_doctor`
  - Critério de pronto: `doctor --nvr-ip <IP> --share` executa diagnóstico e gera artefatos compartilháveis conforme configuração.
  - Confiança: 🟢

- [ ] T-19, Integrar checagem de update e health gate ao runtime.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_run_post_update_health_gate`, `_rollback_update_if_needed`; `src/dalevision_edge_agent/update.py`
  - Critério de pronto: update é checado em intervalo configurado; health gate exige heartbeat OK; rollback é tentado quando gate falha.
  - Confiança: 🟢

- [ ] T-20, Implementar tratamento de erro e códigos de saída.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `EXIT_CONFIG_ERROR`, `EXIT_AUTH_ERROR`, `EXIT_NETWORK_ERROR`
  - Critério de pronto: falhas de configuração, autenticação e rede retornam códigos distintos quando fatais, com mensagem clara ao suporte.
  - Confiança: 🟢

## Tarefas de Teste

- [ ] TT-01, Testar transição de estado com heartbeat bem-sucedido.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: `DEGRADED + ok=True + 201` retorna `ACTIVE`.
  - Confiança: 🟢

- [ ] TT-02, Testar transição de estado com falha de rede.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: `ACTIVE + ok=False + status=None` retorna `DEGRADED`.
  - Confiança: 🟢

- [ ] TT-03, Testar transição de estado com erro de autenticação.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: `ACTIVE + ok=False + status=401` retorna `ERROR`.
  - Confiança: 🟢

- [ ] TT-04, Testar intervalo degradado.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: `_heartbeat_sleep_seconds(AgentState.DEGRADED, active=30, degraded=300)` retorna `300`.
  - Confiança: 🟢

- [ ] TT-05, Testar resolução de paths com overrides.
  - Origem no legado: `src/dalevision_edge_agent/paths.py`
  - Critério de pronto: com `DALE_CONFIG_DIR` e `DALE_LOG_DIR`, os paths retornados apontam para os diretórios informados e existem no filesystem.
  - Confiança: 🟢

- [ ] TT-06, Testar validação de env obrigatório.
  - Origem no legado: `src/dalevision_edge_agent/env.py`
  - Critério de pronto: ausência de `EDGE_TOKEN` ou `CLOUD_BASE_URL` falha com erro diagnosticável; aliases `DALE_EDGE_TOKEN` e `DALE_CLOUD_BASE_URL` são aceitos.
  - Confiança: 🟢

- [ ] TT-07, Testar que logs não contêm token bruto.
  - Origem no legado: `src/dalevision_edge_agent/activation.py`; `src/dalevision_edge_agent/setup_api.py`
  - Critério de pronto: durante hidratação e erros redigidos, o valor literal de `EDGE_TOKEN` ou senha RTSP não aparece em log.
  - Confiança: 🟢

- [ ] TT-08, Testar subcomandos sem entrar no loop operacional.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_parse_args`
  - Critério de pronto: `doctor`, `setup-api`, `scan` e `test-rtsp` roteiam para seus fluxos e não executam loop contínuo por acidente.
  - Confiança: 🟡

## Tarefas de Migração de Dados

- [ ] TM-01, Não aplicável para esta unit.
  - Origem no legado: runtime local não define schema relacional próprio.
  - Critério de pronto: nenhuma migração de banco é necessária para reimplementar o runtime local.
  - Confiança: 🟢

## Ordem Sugerida

1. Implementar T-03, T-04, T-05 e T-06 primeiro, porque paths e settings bloqueiam qualquer execução real.
2. Implementar T-07, T-08, T-09 e T-10 para estabelecer estado local e ativação antes do loop.
3. Implementar T-01 e T-02 para tornar o entrypoint observável e operável.
4. Implementar T-11, T-12, T-13 e T-14 para preservar heartbeat e estado, que são contratos críticos.
5. Implementar T-15 e T-16 para completar integração operacional com cameras e onboarding.
6. Implementar T-17 e T-18 para suporte/onboarding local.
7. Implementar T-19 e T-20 por último, pois update e códigos fatais dependem do loop base já confiável.
8. Executar TT-01 a TT-07 antes de qualquer release para clientes; TT-08 deve ser executado com mocks para evitar processos longos.

## Tarefas Estratégicas (0 a 10 Users)

- [ ] TR-01 — Implementar Autostart User-level via Startup Folder
  - Origem no legado: Decisão de instalação sem admin.
  - Critério de pronto: Criar atalho em `%APPDATA%\...\Startup` no fim da instalação; agente inicia com login do usuário.
  - Confiança: 🟢

- [ ] TR-02 — Implementar Lógica de Self-Healing respeitando Horário Comercial
  - Origem no legado: Decisão de resiliência e redução de ruído.
  - Critério de pronto: Agente reinicia workers após 15 min em `degraded` somente se dentro do horário da loja; standby automático fora do horário.
  - Confiança: 🟢

- [ ] TR-03 — Monitoramento de Recursos (Hardware Limit Alert)
  - Origem no legado: Decisão de estabilidade em hardware variável.
  - Critério de pronto: Telemetria de CPU/RAM constante; alerta em 80% de uso sugerindo redução de câmeras.
  - Confiança: 🟢

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Todas as decisões técnicas de deployment e saúde foram validadas.
