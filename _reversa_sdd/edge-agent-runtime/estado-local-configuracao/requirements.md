# Estado Local e Configuração, Requirements

## Visão Geral

🟢 CONFIRMADO: Este caso de uso cobre persistência local, `.env`, paths Windows, aliases de ambiente, estado de ativação e proteção contra vazamento de segredos.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-CONF-01 | 🟢 Resolver config por `DALE_AGENT_CONFIG_PATH`, `DALE_CONFIG_DIR` ou cwd. | Must | `ConfigManager.from_default()` segue essa precedência. |
| RF-CONF-02 | 🟢 Persistir config em JSON ASCII/UTF-8. | Must | `ConfigManager.save()` grava JSON indentado. |
| RF-CONF-03 | 🟢 Resolver diretórios AppData com fallback. | Must | `resolve_runtime_paths()` cria diretórios. |
| RF-CONF-04 | 🟢 Hidratar `.env` após ativação. | Must | Cloud/store/token/agent são escritos quando disponíveis. |
| RF-CONF-05 | 🟢 Não logar token bruto. | Must | Logs usam `edge_token_len` ou redaction. |
| RF-CONF-06 | 🟢 Limpar temporários antigos de forma conservadora. | Should | Mantém mais recentes e reporta erros. |

## Critérios de Aceitação

```gherkin
Dado DALE_CONFIG_DIR configurado
Quando o agente resolver configuração
Então o arquivo de config deve ficar dentro desse diretório
```

```gherkin
Dado uma ativação com edge_token válido
Quando hidratar o .env
Então EDGE_TOKEN deve ser escrito no arquivo
Mas o valor literal não deve aparecer nos logs
```

## Rastreabilidade

| Arquivo | Símbolo | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/activation.py` | `ConfigManager`, `hydrate_runtime_env_from_activation_config` | 🟢 |
| `src/dalevision_edge_agent/paths.py` | `resolve_runtime_paths`, `cleanup_old_runtime_tmp` | 🟢 |
| `src/dalevision_edge_agent/env.py` | `REQUIRED_ENV`, `load_settings` | 🟢 |
