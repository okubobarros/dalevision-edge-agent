# Loop Operacional, Tasks

## Tarefas

- [ ] T-LOOP-01, Implementar tick principal do loop.
  - Origem no legado: `src/dalevision_edge_agent/main.py`
  - Critério de pronto: loop executa camera sync, heartbeat, update e sleep em sequência.
  - Confiança: 🟢

- [ ] T-LOOP-02, Implementar payload de heartbeat.
  - Origem no legado: `main.py` `HeartbeatPayload`
  - Critério de pronto: payload contém device, versão, canal, status, uptime e cameras.
  - Confiança: 🟢

- [ ] T-LOOP-03, Implementar regra de estado pós-heartbeat.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: testes de sucesso/rede/auth passam.
  - Confiança: 🟢

- [ ] T-LOOP-04, Implementar sleep por estado.
  - Origem no legado: `tests/test_heartbeat_state.py`
  - Critério de pronto: degraded usa intervalo degradado.
  - Confiança: 🟢

- [ ] T-LOOP-05, Integrar update interval.
  - Origem no legado: `src/dalevision_edge_agent/main.py`; `update.py`
  - Critério de pronto: update só é checado quando intervalo vence.
  - Confiança: 🟢

## Testes

- [ ] TT-LOOP-01, Heartbeat OK muda estado para active.
- [ ] TT-LOOP-02, Erro de rede muda estado para degraded.
- [ ] TT-LOOP-03, 401 muda estado para error.
- [ ] TT-LOOP-04, Evento `agent_first_heartbeat` é emitido uma vez.
- [ ] TT-LOOP-05, Falha de camera sync não fatal preserva loop.
