# billing - Design

## Visão Geral

- 🟢 O app `billing` é uma camada fina: lista planos e sincroniza estado de cobrança recebido por webhook.
- 🟢 A enforcement de acesso ao produto fica distribuída em utilitários chamados pelos módulos de domínio.
- 🟢 Os dados de billing são modelos unmanaged em `apps.core.models`, não models do app billing.

## Componentes

### BillingPlansView

- 🟢 View pública que retorna constante `PLANS`.
- 🟢 Não consulta banco.

### BillingWebhookSyncView

- 🟢 View pública com proteção opcional por secret.
- 🟢 Normaliza plan/status/datas.
- 🟢 Atualiza `BillingCustomer` e `Subscription` em transação.
- 🟢 Reativa stores bloqueadas por trial quando subscription fica ativa.

### apps.billing.utils

- 🟢 Define `PaywallError`.
- 🟢 Calcula `is_trial`.
- 🟢 Registra `paywall_blocked`.
- 🟢 Aplica limite de stores do trial.

### backend.utils.entitlements

- 🟢 Detecta trial expirado.
- 🟢 Detecta assinatura ativa.
- 🟢 Expõe `require_trial_active`, `enforce_can_use_product` e aliases.
- 🟢 Usa introspecção para tolerar schema sem `trial_ends_at`.

### apps.cameras.limits

- 🟢 Define limites reais por plano para câmeras.
- 🟢 Aplica limites considerando câmera ativa e plano da org.

## Fluxo de Webhook

1. 🟢 Request chega em `/api/v1/billing/webhook-sync`.
2. 🟢 Se secret está configurado, header deve bater.
3. 🟢 Valida `org_id`.
4. 🟢 Extrai customer e subscription.
5. 🟢 Normaliza plan e status.
6. 🟢 Abre transação.
7. 🟢 Upsert de customer quando aplicável.
8. 🟢 Busca subscription por Stripe id ou última da org.
9. 🟢 Atualiza ou cria subscription.
10. 🟢 Se status ativo, desbloqueia stores `trial_expired`.
11. 🟢 Retorna subscription serializada.

## Fluxo de Enforcement

1. 🟢 Módulo de domínio chama entitlement/paywall antes da mutação.
2. 🟢 Staff/superuser bypassa.
3. 🟢 Entitlement verifica trial expirado por org/store/blocked store.
4. 🟢 Limite verifica plan e contagem.
5. 🟢 Bloqueio registra audit log.
6. 🟢 Erro HTTP 402 é propagado para a view.

## Decisões

- 🟢 Webhook não implementa Stripe SDK; espera payload normalizado.
- 🟢 Falha de lookup de subscription em `is_trial` defaulta para trial, postura conservadora.
- 🟢 Falha de lookup de subscription em `is_subscription_active` defaulta para false.
- 🟢 Staff/superuser bypassa limites para suporte/administração.
- 🟢 `active` subscription reativa apenas stores bloqueadas por `trial_expired`, não por outros motivos.

## Inconsistências

- 🟡 Catálogo público `pro` anuncia 15 câmeras, mas `apps.cameras.limits` aplica 12 câmeras para `pro`.
- 🟡 Catálogo público usa `network`, enquanto limites internos usam `growth`/`enterprise` como ilimitados e normalizam `rede/network/enterprise` para `network` apenas no webhook.
- 🟡 `Subscription.status` no modelo aceita `blocked`, mas webhook considera `blocked` inválido e normaliza para `incomplete`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\views.py`.
- 🟢 `C:\workspace\dale-vision\backend\utils\entitlements.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\limits.py`.
