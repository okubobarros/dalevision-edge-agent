# enforce-trial-paywall - Tasks

- [ ] 🟢 Implementar `PaywallError`.
  - Fonte: `apps\billing\utils.py`.
  - Critério de pronto: payload HTTP 402 contém código, mensagem e meta.

- [ ] 🟢 Implementar limite de stores.
  - Fonte: `apps\billing\utils.py`.
  - Critério de pronto: trial bloqueia count >= 1.

- [ ] 🟢 Implementar limite de câmeras.
  - Fonte: `apps\cameras\limits.py`.
  - Critério de pronto: limites por plano são aplicados só para câmeras ativas.

- [ ] 🟢 Implementar trial expired.
  - Fonte: `backend\utils\entitlements.py`.
  - Critério de pronto: trial vencido bloqueia com audit log.

- [ ] 🟡 Consolidar fonte única de limites.
  - Fonte: divergência billing/cameras.
  - Critério de pronto: catálogo e enforcement leem a mesma tabela/config.
