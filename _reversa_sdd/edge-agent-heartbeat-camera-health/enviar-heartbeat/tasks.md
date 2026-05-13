# Enviar Heartbeat, Tasks

- [ ] T-EH-01, Implementar payload edge heartbeat.
  - Origem: `src/dalevision_edge_agent/heartbeat.py`
  - Critério: JSON contém `event_name`, `source`, `data`.
  - Confiança: 🟢

- [ ] T-EH-02, Implementar envio HTTP com timeout.
  - Origem: `heartbeat.py` `REQUEST_TIMEOUT_SECONDS=10`
  - Critério: timeout padrão de 10s.
  - Confiança: 🟢

- [ ] T-EH-03, Implementar tratamento de retorno.
  - Origem: `heartbeat.py`
  - Critério: 2xx ok, não 2xx detail, exception status none.
  - Confiança: 🟢

- [ ] T-EH-04, Testar transições de estado.
  - Origem: `tests/test_heartbeat_state.py`
  - Critério: active/degraded/error conforme status.
  - Confiança: 🟢
