# Edge Agent Heartbeat e Camera Health, Tasks

## Tarefas

- [ ] T-HB-01, Implementar envio de heartbeat.
  - Origem: `src/dalevision_edge_agent/heartbeat.py` `send_heartbeat`
  - Critério: payload contém `event_name=edge_heartbeat`, `source=edge`, `data` e retorna `(ok,status,error)`.
  - Confiança: 🟢

- [ ] T-HB-02, Implementar `HeartbeatPayload`.
  - Origem: `src/dalevision_edge_agent/heartbeat_client.py`
  - Critério: `to_extra_data()` retorna device, versão, canal, status, uptime e cameras_connected.
  - Confiança: 🟢

- [ ] T-HB-03, Integrar heartbeat ao loop.
  - Origem: `src/dalevision_edge_agent/main.py`
  - Critério: loop chama `HeartbeatClient.send()` com `edge_token` e extra_data de cameras.
  - Confiança: 🟢

- [ ] T-HB-04, Implementar transições pós-heartbeat.
  - Origem: `tests/test_heartbeat_state.py`
  - Critério: sucesso -> active, rede -> degraded, 401 -> error.
  - Confiança: 🟢

- [ ] T-HB-05, Implementar sleep degradado.
  - Origem: `tests/test_heartbeat_state.py`
  - Critério: `AgentState.DEGRADED` usa 300s por padrão.
  - Confiança: 🟢

- [ ] T-HB-06, Implementar `check_camera_health`.
  - Origem: `src/dalevision_edge_agent/cameras.py`
  - Critério: retorna camera_id, status, latency_ms, checked_at e error quando aplicável.
  - Confiança: 🟢

- [ ] T-HB-07, Implementar envio de evento `camera_health`.
  - Origem: `src/dalevision_edge_agent/cameras.py`, `main.py`
  - Critério: evento é enviado com store/agent/camera health e auth tracker.
  - Confiança: 🟢

- [ ] T-HB-08, Implementar watchdog local.
  - Origem: `src/dalevision_edge_agent/main.py`
  - Critério: atualiza últimos timestamps de heartbeat e camera health bem-sucedidos.
  - Confiança: 🟢

- [ ] T-HB-09, Implementar backend receiver/aggregation compatível.
  - Origem: `C:\workspace\dale-vision\apps\edge\models.py`, `views_edge_status.py`
  - Critério: sinais edge alimentam stats/status online/degraded/offline.
  - Confiança: 🟢

## Testes

- [ ] TT-HB-01, Heartbeat 2xx retorna OK.
- [ ] TT-HB-02, HTTP não 2xx retorna erro com detalhe.
- [ ] TT-HB-03, RequestException retorna `(False, None, str(exc))`.
- [ ] TT-HB-04, Auth 401/403 vira estado error.
- [ ] TT-HB-05, Camera sem RTSP retorna erro controlado.
- [ ] TT-HB-06, Camera online atualiza watchdog e emite evento.
- [ ] TT-HB-07, Backend calcula status degraded/offline a partir de sinais expirados.

## Lacunas

- [ ] 🟢 Definir thresholds finais de status: 15 minutos em `degraded` dentro do horário comercial é o gatilho para restart/alerta.
