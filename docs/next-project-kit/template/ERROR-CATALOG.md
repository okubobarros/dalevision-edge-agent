# ERROR-CATALOG.md - Template

## Formato
- `ERROR_CODE`
- Causa provavel
- Como detectar
- Acao para operador
- Acao para suporte
- Telemetria associada

## Exemplo
### `HEARTBEAT_REJECTED`
- Causa provavel: token invalido/expirado ou ambiente incorreto.
- Como detectar: heartbeat 401/403.
- Acao para operador: regenerar ativacao no app e reexecutar setup.
- Acao para suporte: validar store_id e vinculacao do edge_token.
- Telemetria associada: `activation_failed`, `agent_first_heartbeat` ausente.
