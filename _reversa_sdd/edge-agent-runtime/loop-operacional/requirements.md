# Loop Operacional, Requirements

## Visão Geral

🟢 CONFIRMADO: Este caso de uso cobre o loop contínuo do agente, que mantém presença na cloud via heartbeat, agrega camera health, envia eventos de onboarding, verifica update e ajusta estado/sleep conforme sucesso, rede ou autenticação.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-LOOP-01 | 🟢 Enviar heartbeat periódico. | Must | `HeartbeatClient.send()` é chamado com payload e token. |
| RF-LOOP-02 | 🟢 Agregar campos de camera health no heartbeat. | Must | Payload inclui contagem/campos derivados de camera states. |
| RF-LOOP-03 | 🟢 Atualizar watchdog a cada heartbeat. | Must | Último status/erro/ok são armazenados em memória. |
| RF-LOOP-04 | 🟢 Atualizar `AgentState` após heartbeat. | Must | Sucesso/rede/auth seguem regras testadas. |
| RF-LOOP-05 | 🟢 Emitir `agent_first_heartbeat` uma única vez. | Should | Evento só é enviado após primeiro sucesso. |
| RF-LOOP-06 | 🟢 Verificar update por intervalo configurado. | Should | `check_for_update()` é chamado quando intervalo vence. |
| RF-LOOP-07 | 🟢 Continuar em falhas recuperáveis. | Must | Rede/camera/snapshot recuperáveis não encerram processo. |

## Critérios de Aceitação

```gherkin
Dado um agente ativo
Quando o heartbeat retorna sucesso
Então o estado permanece ou muda para active
E o primeiro sucesso emite agent_first_heartbeat
```

```gherkin
Dado um agente ativo
Quando ocorre erro de rede no heartbeat
Então o estado muda para degraded
E o loop continua com intervalo degradado
```

## Rastreabilidade

| Arquivo | Símbolo | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/main.py` | loop principal, `HeartbeatPayload`, `_next_agent_state_after_heartbeat` | 🟢 |
| `src/dalevision_edge_agent/heartbeat_client.py` | `HeartbeatClient` | 🟢 |
| `tests/test_heartbeat_state.py` | transições de estado | 🟢 |
