# Reportar Camera Health, Tasks

- [ ] T-CH-01, Implementar extração de identidade/RTSP.
  - Origem: `src/dalevision_edge_agent/cameras.py`
  - Critério: suporta chaves legadas de camera.
  - Confiança: 🟢

- [ ] T-CH-02, Implementar probe de saúde.
  - Origem: `check_camera_health`
  - Critério: retorna online/degraded/offline/error com latência.
  - Confiança: 🟢

- [ ] T-CH-03, Implementar evento camera health.
  - Origem: `send_camera_health_event`, `main.py`
  - Critério: evento chega ao backend e falha é logada.
  - Confiança: 🟢

- [ ] T-CH-04, Testar erros controlados.
  - Origem: `cameras.py`
  - Critério: sem RTSP não lança exceção não tratada.
  - Confiança: 🟢
