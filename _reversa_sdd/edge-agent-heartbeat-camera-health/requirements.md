# Edge Agent Heartbeat e Camera Health

## Visão Geral

🟢 CONFIRMADO: Esta unit define o protocolo operacional mais sensível do DaleVision Edge Agent: envio periódico de `edge_heartbeat`, coleta de `camera_health`, agregação de estado das câmeras no heartbeat e transição local entre `active`, `degraded` e `error`.

🟢 CONFIRMADO: A unit envolve os dois repositórios. O agente local implementa envio e coleta em `heartbeat.py`, `heartbeat_client.py`, `cameras.py` e `main.py`; o backend recebe, autentica e agrega sinais em `apps/edge`, `apps/cameras` e `apps/stores/views_edge_status.py`.

## Responsabilidades

- 🟢 Enviar heartbeat com `EDGE_TOKEN`, `STORE_ID`, `AGENT_ID`, versão, status, uptime e campos agregados de câmera.
- 🟢 Coletar health por câmera, incluindo status, latência, erro, timestamp, ROI e snapshot quando disponível.
- 🟢 Publicar eventos `camera_health` no backend por endpoint edge.
- 🟢 Manter watchdog local com último heartbeat e último camera health bem-sucedidos.
- 🟢 Mudar estado local para `degraded` em falha de rede e para `error` em falha de autenticação.
- 🟢 Preservar compatibilidade do protocolo atual de heartbeat e camera health.

## Regras de Negócio

- 🟢 Heartbeat é enviado como evento `edge_heartbeat` com `source=edge`.
- 🟢 Timeout de heartbeat padrão é 10 segundos.
- 🟢 Sucesso HTTP 2xx no heartbeat é considerado OK.
- 🟢 Falha de rede no heartbeat não encerra o agente; move para `degraded`.
- 🟢 HTTP 401/403 é falha de autenticação e pode levar a `EXIT_AUTH_ERROR` após falhas consecutivas.
- 🟢 Status do heartbeat enviado deve ser `active` ou `degraded`; estados não operacionais são normalizados para `active` no payload legado.
- 🟢 Camera health sem URL/host RTSP retorna erro controlado (`rtsp_url_missing` ou `rtsp_host_missing`).
- 🟢 Camera health usa status como `online`, `degraded`, `offline` ou `error`, com latência em ms quando mensurável.
- 🟢 Backend usa sinais recentes para calcular online/degraded/offline.
- 🔴 SLA exato online/degraded/offline por ambiente ainda precisa validação operacional.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-HB-01 | 🟢 Enviar `edge_heartbeat` periódico para o backend. | Must | `send_heartbeat()` monta payload com `event_name=edge_heartbeat`, `source=edge` e `data`. |
| RF-HB-02 | 🟢 Incluir identidade e versão no heartbeat. | Must | Payload inclui `store_id`, `agent_id`, `edge_version`/`installed_version`, `device_key` e canal de update quando disponíveis. |
| RF-HB-03 | 🟢 Incluir status operacional no heartbeat. | Must | `HeartbeatPayload.status` usa `active` ou `degraded`. |
| RF-HB-04 | 🟢 Agregar campos de câmera no heartbeat. | Must | `build_camera_heartbeat_fields(camera_states)` é mesclado ao `extra_data`. |
| RF-HB-05 | 🟢 Enviar `camera_health` por câmera ativa. | Must | Loop chama `check_camera_health()` e `send_camera_health_event()`. |
| RF-HB-06 | 🟢 Atualizar watchdog local após heartbeat e camera health bem-sucedidos. | Should | `watchdog_state` recebe `last_heartbeat_ok_at` e `last_camera_health_ok_at`. |
| RF-HB-07 | 🟢 Mudar estado para `degraded` em erro de rede. | Must | Teste existente valida `status_code=None` -> `AgentState.DEGRADED`. |
| RF-HB-08 | 🟢 Mudar estado para `error` em auth error. | Must | Teste existente valida `status_code=401` -> `AgentState.ERROR`. |
| RF-HB-09 | 🟢 Usar intervalo degradado em estado `degraded`. | Must | Teste existente valida 300s. |
| RF-HB-10 | 🟢 Registrar eventos de onboarding `agent_first_heartbeat`, `camera_validated` e falhas quando aplicável. | Should | `main.py` emite eventos após primeiro heartbeat e health online. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência | Confiança |
|---|---|---|---|
| Disponibilidade | Rede instável degrada, mas não derruba o agente imediatamente. | `tests/test_heartbeat_state.py` | 🟢 |
| Performance | Heartbeat HTTP usa timeout de 10s; camera HTTP usa timeout específico de 5s por padrão. | `heartbeat.py`, `cameras.py` | 🟢 |
| Operabilidade | Logs mostram URL/status/erro sem segredo para suporte remoto. | `main.py` logs de heartbeat/camera | 🟢 |
| Segurança | 401/403 são tratados como auth failure e não ignorados indefinidamente. | `main.py`, `cameras.py` `AUTH_FAILURE_STATUSES` | 🟢 |
| Compatibilidade | Endpoint edge legado `/api/edge/events/` e campos de camera health são preservados. | `cameras.py`, `domain.md` | 🟢 |

## Critérios de Aceitação

```gherkin
Dado um agente ativo com edge token válido
Quando o loop executar heartbeat
Então o backend deve receber um evento edge_heartbeat
E o agente deve registrar status HTTP 2xx como sucesso
```

```gherkin
Dado um agente ativo com rede indisponível
Quando o heartbeat falhar sem status HTTP
Então o estado local deve mudar para degraded
E o próximo sleep deve usar o intervalo degradado
```

```gherkin
Dado um agente com token inválido
Quando o backend responder 401 ou 403
Então o estado local deve mudar para error
E a falha deve ser registrada como autenticação rejeitada
```

```gherkin
Dado uma câmera com RTSP válido
Quando o camera health executar com sucesso
Então o payload deve conter camera_id, status, latency_ms e checked_at
E o evento camera_health deve ser enviado ao backend
```

## Rastreabilidade

| Arquivo | Função / Classe | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/heartbeat.py` | `send_heartbeat` | 🟢 |
| `src/dalevision_edge_agent/heartbeat_client.py` | `HeartbeatPayload`, `HeartbeatClient` | 🟢 |
| `src/dalevision_edge_agent/cameras.py` | `check_camera_health`, `send_camera_health_event`, `build_camera_heartbeat_fields` | 🟢 |
| `src/dalevision_edge_agent/main.py` | loop operacional, estado, watchdog | 🟢 |
| `tests/test_heartbeat_state.py` | transições e sleep degradado | 🟢 |
| `C:\workspace\dale-vision\apps\edge\models.py` | `EdgeEventMinuteStats`, `EdgeDevice` | 🟢 |
| `C:\workspace\dale-vision\apps\stores\views_edge_status.py` | status online/degraded/offline | 🟢 |
