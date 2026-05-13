# gerenciar-assinatura-planos - Tasks

- [ ] 🟢 Implementar listagem de planos.
  - Fonte: `apps\billing\views.py`.
  - Critério de pronto: endpoint retorna constante `PLANS`.

- [ ] 🟢 Implementar validação de webhook secret.
  - Fonte: `apps\billing\views.py`.
  - Critério de pronto: secret errado retorna 403.

- [ ] 🟢 Implementar parse de payload.
  - Fonte: `apps\billing\views.py`.
  - Critério de pronto: aceita dados raiz e objeto `subscription`.

- [ ] 🟢 Implementar upsert transacional.
  - Fonte: `apps\billing\views.py`.
  - Critério de pronto: customer/subscription atualizados na mesma transação.

- [ ] 🟢 Implementar reativação de stores.
  - Fonte: `apps\billing\views.py`.
  - Critério de pronto: stores `blocked/trial_expired` viram `active`.

- [ ] 🟢 Unificar limite do plano Pro para 12 câmeras em todas as camadas (Frontend e Backend).
  - Fonte: `apps\billing\views.py`, `apps\cameras\limits.py`.
  - Critério de pronto: catálogo e enforcement concordam.
