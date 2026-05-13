# billing - Requirements

## Escopo

- 🟢 Esta unit cobre o app `apps.billing`, os modelos unmanaged de cobrança em `apps.core.models`, e os utilitários de entitlement/paywall usados por stores, cameras, edge e frontend.
- 🟢 `apps.billing.models` não define modelos próprios.
- 🟢 As entidades persistidas são `BillingCustomer` e `Subscription` em `apps.core.models`.
- 🟢 O módulo expõe catálogo de planos e webhook de sincronização de assinatura.
- 🟢 A enforcement real do trial/paywall acontece em `apps.billing.utils`, `backend.utils.entitlements`, `apps.cameras.limits` e pontos de chamada em `apps.stores`/`apps.cameras`/`apps.edge`.

## Requisitos Funcionais

### RF-001 - Expor catálogo público de planos

- 🟢 `GET /api/v1/billing/plans` deve ser público.
- 🟢 Deve retornar planos `start`, `pro` e `network`.
- 🟢 Plano `start`: mensalidade 297, 1 loja, 3 câmeras.
- 🟢 Plano `pro`: mensalidade 597, 3 lojas, 15 câmeras, `popular=true`, `recommended=true`.
- 🟢 Plano `network`: preço, lojas e câmeras indefinidos; `contact_only=true`.

### RF-002 - Sincronizar cobrança por webhook

- 🟢 `POST /api/v1/billing/webhook-sync` deve ser público, mas pode exigir `X-Billing-Webhook-Secret` quando `BILLING_WEBHOOK_SECRET` estiver configurado.
- 🟢 Secret divergente deve retornar `403 unauthorized webhook`.
- 🟢 `org_id` é obrigatório.
- 🟢 Deve aceitar `customer_id` direto ou em `customer.id`.
- 🟢 Deve aceitar dados de subscription no payload raiz ou em `subscription`.
- 🟢 Deve normalizar plan code.
- 🟢 Status aceitos: `trialing`, `active`, `past_due`, `canceled`, `incomplete`.
- 🟢 Status desconhecido deve virar `incomplete`.
- 🟢 Datas ISO de período devem ser parseadas com suporte a `Z`.
- 🟢 Deve criar/atualizar `BillingCustomer` quando `customer_id` existir.
- 🟢 Deve localizar subscription por `stripe_subscription_id`; se não encontrar, usa subscription mais recente da org.
- 🟢 Deve criar subscription quando nenhuma existente for encontrada.
- 🟢 Quando status virar `active`, stores bloqueadas por `trial_expired` devem ser reativadas.

### RF-003 - Representar customer e subscription

- 🟢 `BillingCustomer` deve mapear `org_id`, `stripe_customer_id` e `created_at`.
- 🟢 `Subscription` deve mapear `org_id`, `stripe_subscription_id`, `plan_code`, `status`, períodos, cancelamento ao fim do período, `created_at` e `updated_at`.
- 🟢 `Subscription.status` aceita também `blocked` no modelo core, embora o webhook aceite apenas o subconjunto sem `blocked`.

### RF-004 - Detectar trial e assinatura ativa

- 🟢 `is_trial` deve considerar trial quando não há subscription para a org.
- 🟢 Falha ao consultar subscription deve logar exceção e defaultar para trial.
- 🟢 Subscription com `status=trialing` ou `plan_code=trial` deve ser trial.
- 🟢 `is_subscription_active` deve retornar true somente para subscription mais recente com `status=active`.

### RF-005 - Aplicar limite de lojas no trial

- 🟢 `TRIAL_STORE_LIMIT` deve ser 1.
- 🟢 Staff/superuser devem bypassar limite.
- 🟢 Se a org não está em trial, limite não deve ser aplicado.
- 🟢 Se quantidade de stores da org for maior ou igual ao limite, deve criar audit log `paywall_blocked` e lançar `PaywallError`.
- 🟢 `PaywallError` deve retornar HTTP 402 com `code=PAYWALL_TRIAL_LIMIT`.

### RF-006 - Aplicar limite de câmeras por plano

- 🟢 `apps.cameras.limits` deve calcular limites a partir da subscription mais recente da org.
- 🟢 Sem org ou sem subscription deve defaultar para `trial`.
- 🟢 Status `trialing` ou plan `trial` deve usar limite trial.
- 🟢 Plan aliases: `free->trial`, `basic/starter/paid->start`, `entreprise->enterprise`.
- 🟢 Limites aplicados: trial 3 câmeras/1 store, start 3/1, pro 12/3, growth/enterprise sem limite.
- 🟢 Staff/superuser devem bypassar limite.
- 🟢 Câmera inativa não deve contar se coluna `active` existe.
- 🟢 Falha de banco em subscription deve defaultar para trial.
- 🟢 Bloqueio deve gerar audit log `paywall_blocked` e `PaywallError` com meta `limit`, `entity=camera`, `plan_code`.

### RF-007 - Bloquear uso após trial expirado

- 🟢 `backend.utils.entitlements` deve detectar trial expirado por `organizations.trial_ends_at`, `stores.trial_ends_at` ou store bloqueada com `blocked_reason=trial_expired`.
- 🟢 Assinatura ativa deve cancelar a condição de trial expirado.
- 🟢 Org inexistente ou org_id inválido não deve ser tratada como expirada.
- 🟢 O utilitário deve tolerar ausência de coluna `trial_ends_at` via introspecção.
- 🟢 `require_trial_active` deve bypassar staff/superuser.
- 🟢 Quando bloquear, deve criar audit log `trial_expired_blocked` e lançar `TrialExpiredError`.
- 🟢 `TrialExpiredError` deve retornar HTTP 402 com `code=TRIAL_EXPIRED` e `action=UPGRADE_REQUIRED`.

### RF-008 - Integrar paywall com stores/cameras/edge

- 🟢 Criação/ativação de câmera deve chamar `enforce_can_use_product` e `enforce_trial_camera_limit`.
- 🟢 Criação de store deve chamar `enforce_trial_store_limit` ou entitlement equivalente.
- 🟢 Heartbeat que cria câmera automaticamente no edge deve respeitar `enforce_trial_camera_limit`.
- 🟢 Edge access deve considerar `blocked_reason=subscription_inactive` como `edge_store_disabled`.
- 🟢 Billing webhook ativo deve desbloquear stores bloqueadas por `trial_expired`.

## Requisitos Não Funcionais

- 🟢 Segurança: webhook secret deve ser validado quando configurado.
- 🟢 Auditabilidade: bloqueios de paywall/trial devem registrar `AuditLog`.
- 🟢 Resiliência: ausência de colunas trial deve ser tolerada por introspecção.
- 🟢 Compatibilidade: plano `network` no catálogo deve coexistir com `enterprise/growth` nos limites internos.
- 🟢 Clareza operacional: erros de paywall usam HTTP 402 e códigos curtos.

## MoSCoW

- **Must** 🟢: plans, webhook sync, subscription active, trial expired, PaywallError, camera/store limits.
- **Should** 🟢: reativação automática de stores após pagamento ativo.
- **Could** 🟡: unificar tabela de limites entre billing public plans e cameras limits.
- **Won't** 🟢: processar Stripe diretamente; webhook recebe payload já normalizado.

## Critérios de Aceitação

- 🟢 Dado `BILLING_WEBHOOK_SECRET` configurado, quando webhook vem sem secret correto, então retorna 403.
- 🟢 Dado webhook com subscription ativa, quando org tem store bloqueada por trial, então store volta para `active`.
- 🟢 Dado trial com uma store existente, quando cria outra store, então recebe 402 `PAYWALL_TRIAL_LIMIT`.
- 🟢 Dado plano start com 3 câmeras ativas, quando cria outra câmera ativa, então recebe 402 `PAYWALL_TRIAL_LIMIT`.
- 🟢 Dado org com trial expirado e sem assinatura ativa, quando chama ação protegida, então recebe 402 `TRIAL_EXPIRED`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\billing\utils.py`.
- 🟢 `C:\workspace\dale-vision\apps\billing\urls.py`.
- 🟢 `C:\workspace\dale-vision\backend\utils\entitlements.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\limits.py`.
- 🟢 `C:\workspace\dale-vision\apps\core\models.py`.
