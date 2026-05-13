# gerenciar-assinatura-planos - Design

## Plans

- 🟢 Constante em memória.
- 🟢 Público.
- 🟢 Sem persistência.

## Webhook Sync

- 🟢 Recebe payload já normalizado por integração externa.
- 🟢 Usa transação para customer/subscription/reactivação.
- 🟢 Preferência de identificação de subscription: Stripe id, depois última da org.

## Normalização

- 🟢 `starter/start/basic/paid` viram `start`.
- 🟢 `pro/professional` viram `pro`.
- 🟢 `rede/network/enterprise` viram `network`.
- 🟢 `trial/trialing` viram `trial`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\views.py`.
