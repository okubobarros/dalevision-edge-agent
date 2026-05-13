# Edge Agent Runtime, Casos Extremos

## Escopo

🟢 CONFIRMADO: Este arquivo documenta casos extremos do runtime local do DaleVision Edge Agent, extraídos de `main.py`, `activation.py`, `env.py`, `paths.py`, `setup_api.py` e `tests/test_heartbeat_state.py`.

## Casos de Configuração

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-01 | `.env` ausente, mas variáveis `DALE_*` presentes | O runtime deve aceitar aliases e montar settings válidos. | `src/dalevision_edge_agent/env.py` `REQUIRED_ENV` | 🟢 |
| EC-02 | `CLOUD_BASE_URL` ausente | O runtime deve falhar com erro de configuração/ativação claro antes de operar. | `src/dalevision_edge_agent/activation.py` `missing_cloud_base_url`; `env.py` | 🟢 |
| EC-03 | `EDGE_TOKEN` ausente | O runtime não deve enviar heartbeat autenticado e deve reportar configuração inválida. | `src/dalevision_edge_agent/env.py` `REQUIRED_ENV` | 🟢 |
| EC-04 | `AGENT_ID` ausente | O runtime deve usar fallback quando possível, mas o contrato operacional pede `AGENT_ID` preenchido no `.env`. | AGENTS.md e `env.load_settings` | 🟡 |
| EC-05 | Variável booleana inválida | O parser deve rejeitar valor inválido com `ValueError` diagnosticável. | `src/dalevision_edge_agent/main.py` `_parse_bool_env` | 🟢 |
| EC-06 | Variável inteira inválida | O parser deve rejeitar valor inválido com `ValueError` diagnosticável. | `src/dalevision_edge_agent/main.py` `_parse_int_env` | 🟢 |

## Casos de Ativação e Estado

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-07 | Sem device salvo e sem activation token | Estado deve permanecer `unprovisioned`; log deve orientar falta de token. | `src/dalevision_edge_agent/activation.py` `bootstrap_activation` | 🟢 |
| EC-08 | Activation token presente, rede indisponível | Estado deve permanecer `activating` para retry, não `error` fatal. | `src/dalevision_edge_agent/activation.py` `activation_network_retry` | 🟢 |
| EC-09 | Activation token recusado por 401/403/409 | Estado deve virar `error`, pois é falha não recuperável de credencial/conflito. | `src/dalevision_edge_agent/activation.py` | 🟢 |
| EC-10 | Device já provisionado no config | Runtime deve iniciar como `active` sem reativar. | `src/dalevision_edge_agent/activation.py` `has_device` | 🟢 |
| EC-11 | Heartbeat OK após estado degradado | Próximo estado deve ser `active`. | `tests/test_heartbeat_state.py` | 🟢 |
| EC-12 | Heartbeat com erro de rede | Próximo estado deve ser `degraded`, preservando retry. | `tests/test_heartbeat_state.py` | 🟢 |
| EC-13 | Heartbeat com 401/403 | Próximo estado deve ser `error`; falhas consecutivas podem encerrar com auth error. | `tests/test_heartbeat_state.py`; `main.py` | 🟢 |

## Casos de Paths e Windows

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-14 | `%LOCALAPPDATA%` ausente | Runtime deve tentar `%USERPROFILE%\\AppData\\Local`; se ausente, cwd. | `src/dalevision_edge_agent/paths.py` `_resolve_local_appdata` | 🟢 |
| EC-15 | `%APPDATA%` ausente | Runtime deve tentar `%USERPROFILE%\\AppData\\Roaming`; se ausente, cwd. | `src/dalevision_edge_agent/paths.py` `_resolve_roaming_appdata` | 🟢 |
| EC-16 | Versão contém caracteres inválidos para pasta | Runtime deve sanitizar componente do caminho. | `src/dalevision_edge_agent/paths.py` `_safe_component` | 🟢 |
| EC-17 | Diretório temporário antigo não pode ser removido | Runtime deve acumular erro e continuar, sem apagar fora de `runtime_tmp_root`. | `src/dalevision_edge_agent/paths.py` `cleanup_old_runtime_tmp` | 🟢 |
| EC-18 | Usuário sem privilégio administrativo | Startup/scheduled task pode falhar; runtime deve registrar mensagem clara. | `src/dalevision_edge_agent/main.py` `_is_windows_admin`, install helpers | 🟡 |

## Casos de Logging e Segredos

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-19 | Hidratação de `.env` com token válido | Log pode registrar `edge_token_len`, nunca o token bruto. | `src/dalevision_edge_agent/activation.py` `hydrate_runtime_env_from_activation_config` | 🟢 |
| EC-20 | Erro de RTSP contém credenciais na URL | Setup API deve redigir texto sensível antes de expor/logar. | `src/dalevision_edge_agent/setup_api.py` `_redact_sensitive_text` | 🟢 |
| EC-21 | Logger chamado múltiplas vezes no mesmo processo | `_setup_logging()` deve retornar logger existente sem duplicar handlers. | `src/dalevision_edge_agent/main.py` `_setup_logging` | 🟢 |
| EC-22 | Update rollback falha | Runtime deve registrar `UPD051` e não esconder erro. | `src/dalevision_edge_agent/main.py` `_rollback_update_if_needed` | 🟢 |

## Casos de Setup API

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-23 | Setup API em rota desconhecida | Deve retornar JSON controlado, não stack trace. | `src/dalevision_edge_agent/setup_api.py` `build_setup_api_response` | 🟡 |
| EC-24 | Snapshot local solicitado mas captura falha | Deve retornar payload de falha controlado e logar aviso. | `src/dalevision_edge_agent/setup_api.py` snapshot path flow | 🟢 |
| EC-25 | Arquivo HLS ainda não existe | Servidor aguarda tentativas curtas antes de retornar. | `src/dalevision_edge_agent/setup_api.py` stream handling | 🟢 |
| EC-26 | Host alterado para rede local | CORS aberto facilita onboarding, mas amplia superfície local. Deve ser decisão explícita. | `src/dalevision_edge_agent/setup_api.py` `_set_cors_headers` | 🟡 |

## Casos de Loop Operacional

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-27 | Camera sync desabilitado | Runtime deve registrar periodicamente que camera sync está desabilitado e continuar heartbeat. | `src/dalevision_edge_agent/main.py` `CAMERA_SYNC_ENABLED=0` | 🟢 |
| EC-28 | Camera sem candidatos RTSP | Estado da camera deve indicar erro `rtsp_candidates_missing`; runtime continua. | `src/dalevision_edge_agent/main.py` camera loop | 🟢 |
| EC-29 | Camera auth falha repetidamente | Se fatal, runtime retorna `EXIT_AUTH_ERROR`; se não fatal, loga e reseta tracker. | `src/dalevision_edge_agent/main.py` camera auth tracker | 🟢 |
| EC-30 | Vision proxy habilitado e envio de bucket falha | Deve logar warning e preservar loop principal. | `src/dalevision_edge_agent/main.py` `VISION_PROXY` warning | 🟢 |
| EC-31 | Health gate pós-update não recebe heartbeat OK | Deve reportar falha de health gate e permitir rollback. | `src/dalevision_edge_agent/main.py` `_run_post_update_health_gate` | 🟢 |

## Cenários Gherkin de Regressão

```gherkin
Dado um runtime sem EDGE_TOKEN configurado
Quando o agente iniciar em modo contínuo
Então ele deve falhar antes de enviar heartbeat
E deve registrar mensagem diagnóstica sem segredo
```

```gherkin
Dado um agente ativo com rede indisponível
Quando o envio de heartbeat retornar erro sem status HTTP
Então o estado deve mudar para degraded
E o próximo sleep deve usar o intervalo degradado
```

```gherkin
Dado um agente ativo com token revogado
Quando o backend responder 401 no heartbeat
Então o estado deve mudar para error
E após falhas consecutivas o runtime deve retornar erro de autenticação
```

```gherkin
Dado um runtime em Windows sem LOCALAPPDATA
Quando resolver os paths locais
Então deve usar USERPROFILE/AppData/Local ou cwd como fallback
E deve criar os diretórios necessários
```

```gherkin
Dado um erro contendo uma URL RTSP com senha
Quando o setup API montar a resposta de erro
Então a senha não deve aparecer no payload nem nos logs
```

## Lacunas Pendentes

- 🔴 Confirmar o tempo máximo aceitável em `degraded` antes de alerta externo, restart ou intervenção humana.
- 🔴 Validar startup/autostart em Windows limpo sem privilégios administrativos.
- 🔴 Confirmar se `setup-api` pode escutar fora de `127.0.0.1` em algum procedimento oficial de instalação.
