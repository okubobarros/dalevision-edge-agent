# billing - Edge Cases

## Plans

- 🟢 Plans não dependem de autenticação.
- 🟢 Plano `network` tem preço/limites nulos e `contact_only=true`.
- 🟡 Limite mostrado para `pro` diverge do enforcement real.

## Webhook

- 🟢 Secret configurado e header ausente/incorreto retorna 403.
- 🟢 `org_id` ausente retorna 400.
- 🟢 Status desconhecido vira `incomplete`.
- 🟢 Datas inválidas viram `None`.
- 🟢 Sem `stripe_subscription_id`, webhook atualiza a última subscription da org ou cria nova.
- 🟢 `customer_id` ausente não cria billing customer.
- 🟢 Status `active` só reativa stores bloqueadas por `trial_expired`.

## Trial/Entitlements

- 🟢 Org sem subscription é considerada trial em `is_trial`.
- 🟢 Falha de lookup em `is_trial` defaulta para trial.
- 🟢 Org inválida não é considerada trial expirada.
- 🟢 Org inexistente não é considerada trial expirada.
- 🟢 Assinatura ativa cancela trial expirado.
- 🟢 Store bloqueada por `trial_expired` força trial expirado.
- 🟢 Ausência da coluna `trial_ends_at` é tolerada.

## Paywall

- 🟢 Staff/superuser bypassa store/camera limit e trial expired.
- 🟢 `requested_active=false` não aplica limite de câmera.
- 🟢 Câmera ativa excluída por `exclude_camera_id` não conta na ativação.
- 🟢 Falha de contagem de câmeras retorna 0 e não bloqueia.
- 🟢 Growth/enterprise sem limite não bloqueiam.

## Edge

- 🟢 `subscription_inactive` como `blocked_reason` desabilita edge auth/activation.
- 🟢 Billing webhook não reativa `subscription_inactive`; só `trial_expired`.
- 🟡 Se subscription vira `past_due`, não há bloqueio automático neste app.
