# billing - Contracts

## GET /api/v1/billing/plans

```json
{
  "plans": [
    {
      "id": "start",
      "name": "Start",
      "monthly": 297,
      "stores": 1,
      "cameras": 3
    },
    {
      "id": "pro",
      "name": "Pro",
      "monthly": 597,
      "stores": 3,
      "cameras": 15,
      "popular": true,
      "recommended": true
    },
    {
      "id": "network",
      "name": "Rede",
      "monthly": null,
      "stores": null,
      "cameras": null,
      "contact_only": true
    }
  ]
}
```

## POST /api/v1/billing/webhook-sync

### Headers

- 🟢 `X-Billing-Webhook-Secret`: obrigatório somente quando `BILLING_WEBHOOK_SECRET` está configurado.

### Body

```json
{
  "org_id": "uuid",
  "customer_id": "cus_...",
  "subscription_id": "sub_...",
  "plan_code": "pro",
  "status": "active",
  "current_period_start": "2026-05-01T00:00:00Z",
  "current_period_end": "2026-06-01T00:00:00Z",
  "cancel_at_period_end": false
}
```

- 🟢 `customer.id` também é aceito.
- 🟢 `subscription.id`, `subscription.plan_code`, `subscription.status`, `subscription.current_period_start`, `subscription.current_period_end`, `subscription.cancel_at_period_end` também são aceitos.

### Response

```json
{
  "ok": true,
  "org_id": "uuid",
  "subscription": {
    "id": "uuid",
    "status": "active",
    "plan_code": "pro",
    "stripe_subscription_id": "sub_...",
    "current_period_start": "iso-or-null",
    "current_period_end": "iso-or-null",
    "cancel_at_period_end": false
  },
  "billing_customer_id": "uuid-or-null",
  "reactivated_stores": 1
}
```

## PaywallError

```json
{
  "ok": false,
  "code": "PAYWALL_TRIAL_LIMIT",
  "message": "Limite do trial atingido.",
  "meta": {
    "limit": 3,
    "entity": "camera",
    "plan_code": "start"
  }
}
```

## TrialExpiredError

```json
{
  "code": "TRIAL_EXPIRED",
  "action": "UPGRADE_REQUIRED",
  "message": "Trial expired. Subscription required."
}
```

## BillingCustomer

- 🟢 Tabela: `billing_customers`.
- 🟢 Campos: `id`, `org_id`, `stripe_customer_id`, `created_at`.

## Subscription

- 🟢 Tabela: `subscriptions`.
- 🟢 Campos: `id`, `org_id`, `stripe_subscription_id`, `plan_code`, `status`, `current_period_start`, `current_period_end`, `cancel_at_period_end`, `created_at`, `updated_at`.
- 🟢 Status model: `trialing`, `active`, `past_due`, `canceled`, `incomplete`, `blocked`.
