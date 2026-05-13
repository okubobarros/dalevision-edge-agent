# gerenciar-release-edge - Tasks

- [ ] 🟢 Implementar latest release.
  - Fonte: `views_activation.py`.
  - Critério de pronto: retorna release ativa ou fallback settings por canal.

- [ ] 🟢 Implementar upsert admin de release.
  - Fonte: `views_activation.py`.
  - Critério de pronto: staff/superuser cria release e desativa anteriores.

- [ ] 🟢 Implementar policy GET/PUT.
  - Fonte: `views_edge_update_management.py`.
  - Critério de pronto: policy serializada e validada por role.

- [ ] 🟢 Implementar trigger update.
  - Fonte: `views_edge_update_management.py`.
  - Critério de pronto: cria policy a partir da release e evento requested.

- [ ] 🟢 Implementar status/events/attempts.
  - Fonte: `views_edge_update_status.py`, `views_edge_update_attempts.py`.
  - Critério de pronto: dashboard consegue ver versão, health e tentativas.

- [ ] 🟢 Implementar runbooks.
  - Fonte: `views_edge_update_management.py`.
  - Critério de pronto: reason_code conhecido retorna ações imediatas, diagnóstico e evidências.

- [ ] 🟢 Implementar network summaries.
  - Fonte: `views_edge_update_network.py`.
  - Critério de pronto: métricas respeitam lojas das orgs do usuário.

- [ ] 🟢 Implementar canary batch/health/rollback.
  - Fonte: `views_canary.py`.
  - Critério de pronto: staff controla rollout canary e rollback stable.

- [ ] 🟡 Adicionar preview/auditoria de seleção canary.
  - Fonte: lacuna operacional.
  - Critério de pronto: operador consegue ver lojas selecionadas antes de aplicar.
