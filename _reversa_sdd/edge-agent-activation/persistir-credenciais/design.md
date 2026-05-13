# Persistir Credenciais, Design Técnico

## Fluxo

```mermaid
flowchart TD
    A[Payload de ativação] --> B[ConfigManager.update_partial]
    B --> C[Salvar device_key/store_id/edge_token/edge_device_id]
    C --> D[Salvar activation_token=None]
    D --> E[hydrate_runtime_env_from_activation_config]
    E --> F[os.environ + .env opcional]
    F --> G[Log edge_token_len]
```

## Campos

| Campo | Destino | Confiança |
|---|---|---|
| `edge_token` | config, env, `.env` | 🟢 |
| `store_id` | config, env, `.env` | 🟢 |
| `agent_id` | env/`.env` quando presente | 🟢 |
| `device_key` | config | 🟢 |
| `edge_device_id` | config | 🟢 |
| `activation_token` | config como `None` | 🟢 |

## Segurança

- 🟢 O valor do token pode ser persistido localmente porque é necessário para runtime.
- 🟢 O valor do token não pode ser logado.
- 🔴 Confirmar proteção ACL final do arquivo local no Windows.
