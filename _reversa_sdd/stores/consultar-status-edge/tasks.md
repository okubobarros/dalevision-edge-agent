# consultar-status-edge - Tasks

- [ ] 🟢 Implementar classificação por idade.
  - Fonte: `views_edge_status.py`.
  - Critério de pronto: online/degraded/offline seguem thresholds.

- [ ] 🟢 Implementar leitura de heartbeat.
  - Fonte: `views_edge_status.py`.
  - Critério de pronto: usa stats e event_receipts, escolhendo timestamp mais recente.

- [ ] 🟢 Implementar classificação de câmeras.
  - Fonte: `views_edge_status.py`.
  - Critério de pronto: health recente vence; fallback por sinal recente funciona.

- [ ] 🟢 Implementar payload estável.
  - Fonte: `views_edge_status.py`.
  - Critério de pronto: campos essenciais sempre presentes.

- [ ] 🟢 Implementar derivação de activation status.
  - Fonte: `services\activation_status.py`.
  - Critério de pronto: status técnico, valor e next_action batem com fatos.

- [ ] 🟢 Implementar funil de onboarding.
  - Fonte: `services\activation_status.py`.
  - Critério de pronto: eventos EdgeEventRaw alimentam timestamps e stage.
