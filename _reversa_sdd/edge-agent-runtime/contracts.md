# Edge Agent Runtime, Contratos

## Escopo

🟢 CONFIRMADO: O runtime local expõe contratos de processo, CLI, ambiente, filesystem, logs e chamadas outbound para o backend. Ele não expõe uma API cloud pública; a API local de onboarding é tratada como contrato local do agente.

## Contrato de Processo

| Contrato | Entrada | Saída | Compatibilidade | Confiança |
|---|---|---|---|---|
| Execução contínua | `python -m dalevision_edge_agent.main` ou EXE empacotado | Processo long-running com heartbeat periódico | Deve preservar heartbeat e camera health atuais | 🟢 |
| Execução única | `--once` | Um envio de heartbeat e exit code | Usado para teste de conectividade | 🟢 |
| Smoke test | `--smoke-seconds N` | Execução temporária de heartbeat/camera health | Usado para validação pré-release/suporte | 🟢 |
| Doctor | `doctor --nvr-ip <IP> --share` | Diagnóstico compartilhável | Deve gerar arquivos legíveis para suporte | 🟢 |
| Setup API | `setup-api --host --port` | HTTP local | Padrão `127.0.0.1:8787` | 🟢 |

## Contrato de Ambiente

| Variável | Obrigatória | Alias | Uso | Confiança |
|---|---:|---|---|---|
| `CLOUD_BASE_URL` | Sim | `DALE_CLOUD_BASE_URL` | Base URL do backend cloud. | 🟢 |
| `STORE_ID` | Sim | `DALE_STORE_ID` | Identifica a loja. | 🟢 |
| `EDGE_TOKEN` | Sim | `DALE_EDGE_TOKEN` | Autentica chamadas edge. Nunca deve ser logado bruto. | 🟢 |
| `AGENT_ID` | Sim no contrato operacional | `DALE_AGENT_ID` | Identifica o agente local. | 🟢 |
| `DALE_CONFIG_DIR` | Não | n/a | Override do diretório de config. | 🟢 |
| `DALE_LOG_DIR` | Não | n/a | Override do diretório de logs. | 🟢 |
| `EDGE_SETUP_API_ENABLED` | Não | n/a | Liga/desliga setup API capability. | 🟢 |
| `VISION_ENABLED` | Não | n/a | Liga/desliga vision proxy. | 🟢 |
| `AUTO_UPDATE_ENABLED` | Não | n/a | Liga/desliga auto-update capability. | 🟢 |

## Contrato de Estado

| Estado | Significado | Transição de entrada | Transição de saída | Confiança |
|---|---|---|---|---|
| `unprovisioned` | Sem device/token suficiente para operar. | Sem device e sem activation token. | Token presente -> `activating`. | 🟢 |
| `activating` | Tentando ativar ou aguardando retry. | Token presente ou erro recuperável de rede. | Sucesso -> `active`; 401/403/409 -> `error`. | 🟢 |
| `active` | Operando e heartbeat ok. | Ativação ou heartbeat OK. | Rede falha -> `degraded`; auth falha -> `error`. | 🟢 |
| `degraded` | Rede/heartbeat instável, mas recuperável. | Heartbeat sem status HTTP. | Heartbeat OK -> `active`; auth falha -> `error`. | 🟢 |
| `error` | Falha não recuperável sem intervenção. | Auth/config inválida. | Requer correção externa/restart. | 🟢 |

## Contrato de Filesystem

| Artefato | Local padrão | Regra | Confiança |
|---|---|---|---|
| App dir | `%LOCALAPPDATA%\\DaleVision\\app` | Pode ser sobrescrito por `DALE_APP_DIR`. | 🟢 |
| Config dir | `%APPDATA%\\DaleVision` | Pode ser sobrescrito por `DALE_CONFIG_DIR`. | 🟢 |
| Log dir | `%LOCALAPPDATA%\\DaleVision\\logs` | Pode ser sobrescrito por `DALE_LOG_DIR`. | 🟢 |
| Cache dir | `%LOCALAPPDATA%\\DaleVision\\cache` | Pode ser sobrescrito por `DALE_CACHE_DIR`. | 🟢 |
| Runtime tmp | `cache/runtime/<version>/<timestamp>` | Deve ser limpo de forma conservadora. | 🟢 |
| Pending update | `updates/pending.json` | Lido por health gate pós-update. | 🟢 |

## Contrato de Heartbeat Outbound

| Campo | Origem | Obrigatório | Confiança |
|---|---|---:|---|
| `device_key` | Config/activation | Sim | 🟢 |
| `installed_version` | package metadata/env/path | Sim | 🟢 |
| `update_channel` | Config/activation | Sim | 🟢 |
| `status` | `AgentState` | Sim | 🟢 |
| `uptime_seconds` | Runtime clock | Sim | 🟢 |
| `cameras_connected` | Camera states | Sim | 🟢 |
| camera fields agregados | `build_camera_heartbeat_fields` | Quando disponível | 🟢 |

## Contrato de Logs

- 🟢 Logs devem ser legíveis por suporte remoto.
- 🟢 Logs devem registrar códigos curtos quando existentes, como `UPD041`, `UPD050`, `UPD051`.
- 🟢 Logs não podem conter senha, token bruto ou credenciais RTSP.
- 🟢 Quando necessário, registrar presença booleana, tamanho do token ou texto redigido.

## Lacunas

- 🟢 DECIDIDO: `setup-api` escuta por padrão em `127.0.0.1` (segurança local).
- 🟢 DECIDIDO: Modo opcional de **Configuração Remota** permite bind em `0.0.0.0` com token temporário (15 min) para acesso via celular/tablet na mesma rede WiFi.
