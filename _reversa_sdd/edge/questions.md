# edge - Questions

## Lacunas que exigem validação humana

1. 🔴 No fluxo de heartbeat em `apps\edge\views.py`, a busca `Camera.objects.filter(store_id=store_id, name=name).first()` usa `name` sem origem clara. Confirmar se deveria ser `incoming_name`.

2. 🔴 Os testes em `apps\edge\tests_mvp_ingest.py` parecem usar `EdgeToken.objects.create(store=..., name=...)` e `token_cleartext`, mas o modelo atual expõe `store_id`, `token_hash` e `token_plaintext`. Confirmar se esse teste está morto, defasado ou se há migração não analisada.

3. 🟡 O endpoint `/api/v1/ingest/events/` ainda deve ser mantido em produção ou só existe para compatibilidade histórica do MVP?

4. 🟡 `EdgeEventRaw` falha sem bloquear o processamento. Confirmar se perda de raw auditável é aceitável em produção ou se deveria tornar o evento failed.

5. 🟡 O dedupe Redis antes da autenticação/validação completa é intencional? Confirmar se um payload inválido com receipt válido pode bloquear retry imediato por 60 segundos.

## Decisões pendentes sugeridas

- 🟡 Decidir se `event_receipts` deve ser formalizado como modelo Django ou permanecer via SQL direto.
- 🟡 Definir retenção operacional padrão para `edge_events_raw`, além da retenção de `edge_event_minute_stats`.
- 🟡 Separar handlers de `EdgeEventsIngestView` em serviços menores para reduzir risco de regressão.
