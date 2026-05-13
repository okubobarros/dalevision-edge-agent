# billing - Flows

## Fluxo 1 - Consultar Planos

1. 🟢 Cliente chama `GET /api/v1/billing/plans`.
2. 🟢 Backend retorna constante `PLANS`.
3. 🟢 Não há autenticação nem acesso ao banco.

## Fluxo 2 - Sincronizar Webhook

1. 🟢 Provedor/backend interno chama `POST /api/v1/billing/webhook-sync`.
2. 🟢 Se `BILLING_WEBHOOK_SECRET` existe, header é validado.
3. 🟢 Backend exige `org_id`.
4. 🟢 Extrai customer e subscription.
5. 🟢 Normaliza plan/status/datas.
6. 🟢 Em transação, upsert de customer e subscription.
7. 🟢 Se subscription ativa, reativa stores `trial_expired`.
8. 🟢 Retorna subscription e contagem de stores reativadas.

## Fluxo 3 - Bloquear Criação de Store no Trial

1. 🟢 Store flow chama `enforce_trial_store_limit`.
2. 🟢 Staff/superuser bypassa.
3. 🟢 `is_trial` consulta última subscription.
4. 🟢 Se org não é trial, permite.
5. 🟢 Conta stores da org.
6. 🟢 Se count >= 1, registra audit log e lança `PaywallError`.

## Fluxo 4 - Bloquear Câmera por Plano

1. 🟢 Camera/store/edge chama `enforce_trial_camera_limit`.
2. 🟢 Staff/superuser ou câmera inativa bypassa.
3. 🟢 Resolve org da store.
4. 🟢 Resolve subscription/plan.
5. 🟢 Conta câmeras ativas.
6. 🟢 Se count >= limite, registra audit log e lança `PaywallError`.

## Fluxo 5 - Bloquear Trial Expirado

1. 🟢 Módulo chama `enforce_can_use_product`.
2. 🟢 Staff/superuser bypassa.
3. 🟢 `is_trial_expired` valida org.
4. 🟢 Se subscription ativa, permite.
5. 🟢 Se store está bloqueada por trial ou trial_ends_at venceu, bloqueia.
6. 🟢 Registra `trial_expired_blocked`.
7. 🟢 Lança `TrialExpiredError`.
