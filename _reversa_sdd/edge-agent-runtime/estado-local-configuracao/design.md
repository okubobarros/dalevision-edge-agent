# Estado Local e Configuração, Design Técnico

## Componentes

| Componente | Responsabilidade | Confiança |
|---|---|---|
| `ConfigManager` | Ler/salvar JSON de configuração do agente. | 🟢 |
| `RuntimePaths` | Transportar app/config/log/cache/tmp dirs. | 🟢 |
| `load_settings` | Validar e normalizar settings operacionais. | 🟢 |
| `hydrate_runtime_env_from_activation_config` | Gravar `.env` após ativação. | 🟢 |

## Fluxo de Resolução

```mermaid
flowchart TD
    A[Início] --> B{DALE_AGENT_CONFIG_PATH?}
    B -- sim --> C[Usar path explícito]
    B -- nao --> D{DALE_CONFIG_DIR?}
    D -- sim --> E[Usar DALE_CONFIG_DIR/agent_config.json]
    D -- nao --> F[Usar cwd/agent_config.json]
    C --> G[Load JSON ou dict vazio]
    E --> G
    F --> G
```

## Fluxo de Paths

```mermaid
flowchart TD
    A[Resolver local root] --> B[LOCALAPPDATA ou USERPROFILE/AppData/Local ou cwd]
    A --> C[Resolver roaming root]
    C --> D[APPDATA ou USERPROFILE/AppData/Roaming ou cwd]
    B --> E[app/log/cache]
    D --> F[config]
    E --> G[Criar dirs]
    F --> G
```

## Segurança

- 🟢 `EDGE_TOKEN` pode ser escrito em `.env`, mas não deve ser logado bruto.
- 🟢 Erros contendo credenciais RTSP devem ser redigidos no setup API.
- 🟢 Logs podem conter tamanho do token, store_id e path.

## Lacunas

- 🔴 Confirmar política de permissões ACL esperada para arquivos em AppData.
- 🔴 Confirmar retenção final de temporários por versão em produção.
