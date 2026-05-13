# billing - Questions

## Lacunas

1. 🔴 O plano `pro` aparece com 15 câmeras em `BillingPlansView`, mas `apps.cameras.limits` aplica 12 câmeras. Qual é o limite correto?

2. 🟡 O catálogo público usa `network`, mas limites internos usam `growth` e `enterprise` como ilimitados. `network` deve mapear para qual plano interno?

3. 🟡 O webhook não aceita status `blocked`, embora o model aceite. Status `blocked` deve ser recebido de billing ou é somente interno?

4. 🟡 Não há integração Stripe SDK/webhook assinado real no código, apenas secret simples. Isso é intencional para MVP?

5. 🟡 Quando subscription vira `past_due` ou `canceled`, o webhook não bloqueia stores automaticamente. Qual deve ser a política de bloqueio?

6. 🟡 `BillingCustomer.update_or_create` atualiza `created_at` no defaults. Confirmar se deveria haver `updated_at` ou preservar created_at original.
