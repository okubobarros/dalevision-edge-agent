# agregar-estatisticas-minuto - Tasks

- [ ] 🟢 Implementar bucket de minuto.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: timestamp vira minuto com segundos/micros zerados.

- [ ] 🟢 Implementar modelo de stats.
  - Fonte: `C:\workspace\dale-vision\apps\edge\models.py`.
  - Critério de pronto: `EdgeEventMinuteStats` tem unicidade por store/event/minuto.

- [ ] 🟢 Implementar incremento.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: cria linha nova ou incrementa `count` atomicamente com `F`.

- [ ] 🟢 Integrar ao pipeline de ingestão.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: evento novo e duplicado tentam atualizar stats sem bloquear resposta.

- [ ] 🟢 Implementar pruning.
  - Fonte: `C:\workspace\dale-vision\apps\edge\management\commands\prune_edge_event_minute_stats.py`.
  - Critério de pronto: `--days` e `--dry-run` funcionam; default respeita settings/env.

- [ ] 🟡 Avaliar troca de `get_or_create` por upsert SQL.
  - Fonte: comentário em `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: benchmark define se alta frequência exige `INSERT ... ON CONFLICT DO UPDATE`.
