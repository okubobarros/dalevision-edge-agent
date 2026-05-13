# Calcular Degradação Local, Tasks

- [ ] T-DG-01, Implementar função de próximo estado.
  - Origem: `src/dalevision_edge_agent/main.py` `_next_agent_state_after_heartbeat`
  - Critério: cobre sucesso, rede e auth.
  - Confiança: 🟢

- [ ] T-DG-02, Implementar sleep degradado.
  - Origem: `main.py` `_heartbeat_sleep_seconds`
  - Critério: degraded retorna 300 por padrão.
  - Confiança: 🟢

- [ ] T-DG-03, Registrar transição com motivo.
  - Origem: `main.py` `_log_agent_state_transition`
  - Critério: log contém estado anterior, próximo e reason.
  - Confiança: 🟢

- [ ] T-DG-04, Testar regressões.
  - Origem: `tests/test_heartbeat_state.py`
  - Critério: todos os testes atuais passam.
  - Confiança: 🟢
