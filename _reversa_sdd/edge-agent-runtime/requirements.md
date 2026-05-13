# Edge Agent Runtime

## Visão Geral

🟢 CONFIRMADO: Esta unit define o runtime local do DaleVision Edge Agent, responsável por iniciar o processo Python/EXE, carregar configuração, preparar diretórios locais, configurar logs, expor comandos CLI e orquestrar o loop operacional do agente instalado no computador do cliente.

🟢 CONFIRMADO: O runtime é o ponto de integração entre ativação, heartbeat, camera health, setup API, doctor, snapshot, vision proxy, watchdog e auto-update. Ele deve preservar compatibilidade com o protocolo atual de `heartbeat` e `camera_health`.

## Responsabilidades

- 🟢 CONFIRMADO: Resolver caminhos de runtime em `%LOCALAPPDATA%`, `%APPDATA%` ou overrides `DALE_*`, criando diretórios de app, config, logs, cache e temporários.
- 🟢 CONFIRMADO: Carregar `.env` e variáveis obrigatórias `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID`.
- 🟢 CONFIRMADO: Configurar logging legível com rotação para suporte remoto.
- 🟢 CONFIRMADO: Expor CLI para execução contínua, heartbeat único, smoke test, setup API, doctor, scan, RTSP test e instalação/autostart.
- 🟢 CONFIRMADO: Manter máquina de estado do agente entre `unprovisioned`, `activating`, `active`, `degraded` e `error`.
- 🟢 CONFIRMADO: Orquestrar loop operacional que envia heartbeat, sincroniza cameras, emite eventos de onboarding, chama update e calcula intervalo de espera por estado.
- 🟢 CONFIRMADO: Evitar logar segredos em claro; quando necessário, registrar apenas presença, tamanho ou mensagens redigidas.

## Regras de Negócio

- 🟢 CONFIRMADO: O agente sem identidade de device e sem activation token permanece `unprovisioned`; com token presente entra em `activating`; ativação bem-sucedida leva a `active`.
- 🟢 CONFIRMADO: Falha de rede no heartbeat move o agente para `degraded`; sucesso posterior volta para `active`; erro 401/403 move para `error`.
- 🟢 CONFIRMADO: Estado `degraded` usa intervalo de heartbeat degradado de 300 segundos por padrão, validado por teste.
- 🟢 CONFIRMADO: O runtime deve continuar operacional quando camera sync, snapshot ou vision falham de forma recuperável, registrando erro claro e preservando o loop principal quando a falha não for fatal.
- 🟢 CONFIRMADO: Autenticação rejeitada repetidamente pelo backend deve encerrar com código de erro de autenticação, para que suporte/autostart não mascare token inválido.
- 🟢 CONFIRMADO: Setup API local deve ser habilitável por configuração e escutar por padrão em `127.0.0.1:8787`.
- 🟡 INFERIDO: Em instalação Windows empacotada, o runtime deve priorizar diretórios de usuário em AppData para reduzir necessidade de privilégios administrativos.
- 🔴 LACUNA: O SLA operacional definitivo para diferenciar `degraded` tolerável de erro fatal em produção ainda precisa ser confirmado com operação.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟢 O runtime deve iniciar pelo comando `python -m dalevision_edge_agent.main` ou pelo executável empacotado, configurando logger e argumentos CLI antes de executar fluxos. | Must | Ao chamar o entrypoint, `_parse_args()` interpreta os comandos suportados e `_setup_logging()` prepara o logger antes do loop ou subcomando. |
| RF-02 | 🟢 O runtime deve resolver diretórios locais de app, config, logs, cache e temporários, criando-os quando ausentes. | Must | `resolve_runtime_paths()` retorna `RuntimePaths` com diretórios existentes. |
| RF-03 | 🟢 O runtime deve carregar configuração obrigatória de cloud/store/token/agent a partir de `.env` ou variáveis equivalentes `DALE_*`. | Must | `load_settings()` falha quando falta campo obrigatório e normaliza `CLOUD_BASE_URL`. |
| RF-04 | 🟢 O runtime deve manter estado do agente por `AgentState` e registrar transições com motivo. | Must | `StateMachine.set_state()` altera estado e registra old/new/reason. |
| RF-05 | 🟢 O runtime deve enviar heartbeat no loop principal com payload contendo device, versão, canal de update, estado, uptime e campos de camera. | Must | O loop cria `HeartbeatPayload` e chama `HeartbeatClient.send()` com `edge_token`. |
| RF-06 | 🟢 O runtime deve calcular o próximo estado após heartbeat: sucesso = `active`, erro de rede = `degraded`, 401/403 = `error`. | Must | `tests/test_heartbeat_state.py` cobre as três transições principais. |
| RF-07 | 🟢 O runtime deve usar intervalo degradado quando o estado estiver `degraded`. | Must | `_heartbeat_sleep_seconds(... AgentState.DEGRADED ...)` retorna 300 no teste existente. |
| RF-08 | 🟢 O runtime deve expor subcomando `doctor --nvr-ip <IP> --share` para gerar diagnostico compartilhável. | Should | `_parse_args()` registra subparser `doctor` com `--nvr-ip` e `--share`. |
| RF-09 | 🟢 O runtime deve expor subcomando `setup-api --host --port` para onboarding local. | Should | `_parse_args()` registra `setup-api` com host padrão `127.0.0.1` e porta `8787`. |
| RF-10 | 🟢 O runtime deve reportar primeiro heartbeat como evento de onboarding quando o envio for bem-sucedido. | Should | Após heartbeat OK, o loop chama `_safe_emit_onboarding_event()` com `agent_first_heartbeat`. |
| RF-11 | 🟢 O runtime deve executar checagem de update em intervalo configurado e respeitar health gate/rollback quando aplicável. | Should | O loop chama `check_for_update()` e funções de update; health gate exige heartbeat bem-sucedido. |
| RF-12 | 🟡 O runtime deve permitir execução como tarefa de autostart no Windows. | Should | Funções `_create_startup_shortcut()` e `_create_logon_scheduled_task()` indicam suporte a startup; validação completa depende de ambiente Windows real. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Disponibilidade | O agente deve degradar em falha de rede e continuar tentando em vez de encerrar imediatamente. | `src/dalevision_edge_agent/main.py` `_next_agent_state_after_heartbeat`; `tests/test_heartbeat_state.py` | 🟢 |
| Disponibilidade | O intervalo de heartbeat degradado deve evitar retry agressivo em rede instável. | `src/dalevision_edge_agent/main.py` `DEGRADED_HEARTBEAT_INTERVAL_SECONDS = 300`; `tests/test_heartbeat_state.py` | 🟢 |
| Operabilidade | Logs devem ser gravados com rotação para suporte remoto. | `src/dalevision_edge_agent/main.py` `_setup_logging()` usa `RotatingFileHandler` | 🟢 |
| Operabilidade | Diretórios de runtime devem ser criados automaticamente em AppData ou paths configurados. | `src/dalevision_edge_agent/paths.py` `resolve_runtime_paths()` | 🟢 |
| Segurança | Segredos não devem aparecer em logs; tokens devem ser tratados por presença/tamanho ou texto redigido. | `src/dalevision_edge_agent/activation.py` loga `edge_token_len`; `src/dalevision_edge_agent/setup_api.py` redige credenciais em texto sensível | 🟢 |
| Configurabilidade | Paths e capacidades devem aceitar overrides por variáveis `DALE_*` e flags como `EDGE_SETUP_API_ENABLED`, `VISION_ENABLED`, `AUTO_UPDATE_ENABLED`. | `src/dalevision_edge_agent/paths.py`; `src/dalevision_edge_agent/main.py` `_build_agent_capabilities()` | 🟢 |
| Manutenibilidade | O runtime deve separar subcomandos CLI de fluxos especializados para doctor/setup/scan/RTSP. | `src/dalevision_edge_agent/main.py` `_parse_args()` | 🟢 |

## Critérios de Aceitação

```gherkin
Dado um agente com CLOUD_BASE_URL, STORE_ID, EDGE_TOKEN e AGENT_ID válidos
Quando o runtime iniciar em modo contínuo
Então ele deve configurar logs, resolver diretórios locais e entrar no loop operacional de heartbeat
```

```gherkin
Dado um agente em estado degraded
Quando um heartbeat for enviado com sucesso ao backend
Então o próximo estado deve ser active
```

```gherkin
Dado um agente em estado active
Quando o heartbeat falhar por erro de rede sem status HTTP
Então o próximo estado deve ser degraded
E o próximo intervalo de espera deve usar o intervalo degradado configurado
```

```gherkin
Dado um agente em estado active
Quando o backend responder 401 ou 403 para heartbeat
Então o próximo estado deve ser error
E o runtime deve tratar a falha como autenticação inválida
```

```gherkin
Dado um computador de cliente sem diretórios DaleVision em AppData
Quando o runtime resolver paths de execução
Então ele deve criar diretórios de app, config, logs, cache e runtime temporário sem exigir escrita no diretório do projeto
```

```gherkin
Dado um operador de suporte executando doctor
Quando chamar python -m dalevision_edge_agent.main doctor --nvr-ip <IP> --share
Então o runtime deve rotear para o fluxo de diagnóstico e permitir geração de pacote compartilhável
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Inicialização, logging e resolução de paths | Must | Caminho crítico para qualquer execução local do cliente. |
| Carregamento de configuração obrigatória | Must | Sem cloud/store/token o agente não consegue autenticar nem publicar presença. |
| Máquina de estado e heartbeat loop | Must | Base do protocolo atual e dos testes existentes. |
| Tratamento de autenticação inválida | Must | Evita agente “rodando” sem estar autorizado pelo backend. |
| Doctor e setup API | Should | Essenciais para suporte/onboarding, mas não são o loop operacional principal. |
| Auto-update no runtime | Should | Importante para operação em campo, com alternativa manual por release zip. |
| Startup shortcut/scheduled task | Could | Relevante para Windows, mas dependente de permissões e ambiente local. |
| Vision proxy dentro do runtime | Could | Funcionalidade acionada por flag, não obrigatória para heartbeat básico. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `src/dalevision_edge_agent/main.py` | `_parse_args`, `_setup_logging`, `_next_agent_state_after_heartbeat`, `_heartbeat_sleep_seconds`, loop principal | 🟢 |
| `src/dalevision_edge_agent/activation.py` | `AgentState`, `ConfigManager`, `StateMachine`, `bootstrap_activation`, `hydrate_runtime_env_from_activation_config` | 🟢 |
| `src/dalevision_edge_agent/env.py` | `REQUIRED_ENV`, `load_env_from_cwd`, `load_settings` | 🟢 |
| `src/dalevision_edge_agent/paths.py` | `RuntimePaths`, `resolve_runtime_paths`, `cleanup_old_runtime_tmp` | 🟢 |
| `src/dalevision_edge_agent/setup_api.py` | `serve_setup_api`, `build_setup_api_response`, `_redact_sensitive_text` | 🟢 |
| `tests/test_heartbeat_state.py` | Testes de estado e intervalo degradado | 🟢 |
| `_reversa_sdd/code-analysis.md` | Linha de inventário `edge-agent-runtime` | 🟢 |
| `_reversa_sdd/state-machines.md` | `AgentState` | 🟢 |

## Lacunas de Validação

- 🔴 Confirmar com operação o SLA final para estado `degraded` versus encerramento ou alerta crítico.
- 🔴 Validar comportamento de autostart/scheduled task em Windows limpo com usuário sem privilégios administrativos.
