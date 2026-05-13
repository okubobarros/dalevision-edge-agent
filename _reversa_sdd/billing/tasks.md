# billing - Tasks

- [ ] 🟢 Implementar catálogo público de planos.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`.
  - Critério de pronto: `GET /api/v1/billing/plans` retorna `start`, `pro`, `network`.

- [ ] 🟢 Implementar webhook com secret opcional.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`.
  - Critério de pronto: secret configurado exige header `X-Billing-Webhook-Secret`.

- [ ] 🟢 Implementar normalização de plano/status.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`.
  - Critério de pronto: aliases são normalizados e status inválido vira `incomplete`.

- [ ] 🟢 Implementar upsert de billing customer.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`, `apps\core\models.py`.
  - Critério de pronto: customer Stripe é persistido por org.

- [ ] 🟢 Implementar sincronização de subscription.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`.
  - Critério de pronto: subscription é atualizada por Stripe id ou última da org.

- [ ] 🟢 Implementar reativação de stores por pagamento ativo.
  - Fonte: `C:\workspace\dale-vision\apps\billing\views.py`.
  - Critério de pronto: stores `blocked/trial_expired` voltam para `active`.

- [ ] 🟢 Implementar PaywallError.
  - Fonte: `C:\workspace\dale-vision\apps\billing\utils.py`.
  - Critério de pronto: HTTP 402 com `PAYWALL_TRIAL_LIMIT`.

- [ ] 🟢 Implementar limite de stores trial.
  - Fonte: `C:\workspace\dale-vision\apps\billing\utils.py`.
  - Critério de pronto: trial com store existente bloqueia nova store.

- [ ] 🟢 Implementar trial expired entitlement.
  - Fonte: `C:\workspace\dale-vision\backend\utils\entitlements.py`.
  - Critério de pronto: trial expirado bloqueia ações protegidas com audit log.

- [ ] 🟢 Implementar limite de câmeras por plano.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\limits.py`.
  - Critério de pronto: criação/ativação de câmera respeita limite.

- [ ] 🟡 Alinhar limites de planos.
  - Fonte: `views.py` vs `cameras/limits.py`.
  - Critério de pronto: `pro` tem o mesmo limite no catálogo público e no enforcement.

- [ ] 🟡 Definir plano ilimitado único.
  - Fonte: `views.py`, `cameras/limits.py`.
  - Critério de pronto: `network/growth/enterprise` têm regra única documentada.
