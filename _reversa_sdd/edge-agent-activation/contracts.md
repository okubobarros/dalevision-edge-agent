# Edge Agent Activation, Contratos

## Contrato de Emissão

| Campo de resposta | Tipo | Obrigatório | Confiança |
|---|---|---:|---|
| `ok` | boolean | Sim | 🟢 |
| `store_id` | string | Sim | 🟢 |
| `activation_token` | string | Sim | 🟢 |
| `expires_at` | datetime/string | Sim | 🟢 |
| `issued_at` | datetime/string | Sim | 🟢 |
| `expires_in_seconds` | int | Sim | 🟢 |
| `server_now_utc` | datetime/string | Sim | 🟢 |
| `single_use` | boolean | Sim, true | 🟢 |
| `method.id` | string | Sim | 🟢 |

## Contrato de Ativação Local -> Backend

| Campo request | Tipo | Obrigatório | Origem |
|---|---|---:|---|
| `activation_token` ou `token` | string | Sim | Backend/UI/config |
| `device_key` ou `agent_id` | string | Sim | Config local ou gerado |
| `installed_version` ou `version` | string | Não, mas esperado | Runtime |
| `update_channel` | string | Não, padrão `stable` | Config/runtime |

## Contrato de Ativação Backend -> Agente

| Campo response | Tipo | Obrigatório | Uso |
|---|---|---:|---|
| `ok` | boolean | Sim | Validação de sucesso |
| `store_id` | string | Sim | `.env` e heartbeat |
| `device_key` | string | Sim | Identidade local |
| `device_id` | string | Sim | Marca device provisionado |
| `update_channel` | string | Sim | Update policy |
| `edge_token` | string | Sim | Autenticação edge |
| `method.id` | string | Sim | Versionamento do contrato |

## Códigos e Estados

| Situação | Agente | HTTP esperado | Confiança |
|---|---|---|---|
| Sucesso | `active` | 2xx/200 | 🟢 |
| Rede indisponível | `activating` | n/a | 🟢 |
| Token inválido/sem permissão/conflito | `error` | 401/403/409 | 🟢 |
| Outro erro backend recuperável | `activating` | outro não 2xx | 🟢 |

## Segurança

- 🟢 `activation_token` e `edge_token` não devem ser logados em claro.
- 🟢 Edge token posterior deve ser enviado preferencialmente por `X-EDGE-TOKEN`.
- 🟢 Backend armazena/valida hash do token ativo.
