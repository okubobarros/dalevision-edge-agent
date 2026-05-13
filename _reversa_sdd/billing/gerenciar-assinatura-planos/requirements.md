# gerenciar-assinatura-planos - Requirements

## Escopo

- 🟢 Caso de uso de listar planos e sincronizar assinatura/customer.

## Requisitos

- 🟢 Plans deve retornar plano público sem auth.
- 🟢 Webhook deve exigir secret quando configurado.
- 🟢 Webhook deve validar org_id.
- 🟢 Webhook deve normalizar plan/status.
- 🟢 Webhook deve criar/atualizar BillingCustomer.
- 🟢 Webhook deve criar/atualizar Subscription.
- 🟢 Subscription ativa deve reativar stores trial_expired.

## Critérios de Aceitação

- 🟢 Sem org_id retorna 400.
- 🟢 Secret errado retorna 403.
- 🟢 Payload válido cria subscription.
- 🟢 Active reativa stores bloqueadas por trial.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\core\models.py`.
