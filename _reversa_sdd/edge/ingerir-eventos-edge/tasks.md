# ingerir-eventos-edge - Tasks

- [ ] 🟢 Implementar serializer e validação inicial.
  - Fonte: `C:\workspace\dale-vision\apps\edge\serializers.py`.
  - Critério de pronto: payload sem `event_name` falha.

- [ ] 🟢 Implementar resolução de store/receipt/trace.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: ids são extraídos ou calculados conforme contrato.

- [ ] 🟢 Implementar dedupe Redis.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: retry imediato retorna `cache_hit=true`.

- [ ] 🟢 Implementar dedupe Postgres.
  - Fonte: `C:\workspace\dale-vision\apps\edge\vision_metrics.py`.
  - Critério de pronto: `ON CONFLICT (event_id) DO NOTHING`.

- [ ] 🟢 Implementar validação de contratos.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: vision/retail inválidos retornam `400`.

- [ ] 🟢 Implementar handlers vision.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\vision_metrics.py`.
  - Critério de pronto: cada evento suportado marca receipt corretamente.

- [ ] 🟢 Implementar handlers heartbeat/camera_health.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: câmera e store são atualizadas e health log é criado.

- [ ] 🟢 Implementar handler alert.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: alert é encaminhado para `AlertRuleViewSet.ingest`.

- [ ] 🔴 Adicionar teste para heartbeat sem external_id.
  - Fonte: lacuna em `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: cobre a variável de nome da câmera e evita `NameError`.
