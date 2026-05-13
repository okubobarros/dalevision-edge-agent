# Edge Agent Heartbeat e Camera Health, Contratos

## Contrato `edge_heartbeat`

| Campo | Tipo | Obrigatório | Confiança |
|---|---|---:|---|
| `event_name` | string, `edge_heartbeat` | Sim | 🟢 |
| `source` | string, `edge` | Sim | 🟢 |
| `data.store_id` | string | Sim | 🟢 |
| `data.agent_id` | string | Sim | 🟢 |
| `data.edge_version` | string | Sim | 🟢 |
| `data.status` | string | Sim | 🟢 |
| `data.device_key` | string | Sim | 🟢 |
| `data.installed_version` | string | Sim | 🟢 |
| `data.update_channel` | string | Sim | 🟢 |
| `data.uptime_seconds` | int | Sim | 🟢 |
| `data.cameras_connected` | int | Sim | 🟢 |
| `data.*camera fields` | mixed | Não | 🟢 |

## Contrato `camera_health`

| Campo | Tipo | Obrigatório | Confiança |
|---|---|---:|---|
| `camera_id` | string | Sim | 🟢 |
| `status` | `online/degraded/offline/error` | Sim | 🟢 |
| `latency_ms` | int/null | Sim | 🟢 |
| `checked_at` | datetime/string | Sim | 🟢 |
| `error` | string/null | Não | 🟢 |
| `roi_version` | string/null | Não | 🟢 |
| `snapshot_url` / upload metadata | string/null | Não | 🟢 |

## Headers

| Header | Uso | Confiança |
|---|---|---|
| `X-EDGE-TOKEN` | Autenticação edge preferencial. | 🟢 |
| `Authorization` | Fallback/compatibilidade; não deve vencer `X-EDGE-TOKEN`. | 🟢 |

## Retornos

| Situação | Retorno agente | Estado local | Confiança |
|---|---|---|---|
| HTTP 2xx | `(True, status, None)` | `active` | 🟢 |
| HTTP não 2xx | `(False, status, detail)` | depende status | 🟢 |
| RequestException | `(False, None, str(exc))` | `degraded` | 🟢 |
| 401/403 | auth failure | `error` | 🟢 |
