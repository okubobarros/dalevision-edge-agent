# edge - Tasks

- [ ] 🟢 Implementar extração multi-header de Edge Token.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`.
  - Critério de pronto: `X-EDGE-TOKEN` vence sobre Authorization; Bearer, Token, query e X-STORE-TOKEN continuam aceitos.

- [ ] 🟢 Implementar validação hash de token.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`, `apps\edge\models.py`.
  - Critério de pronto: token é comparado por SHA-256 com `EdgeToken.token_hash` e atualiza `last_used_at`.

- [ ] 🟢 Implementar rejeição por store mismatch e store disabled.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`.
  - Critério de pronto: retorna `edge_store_mismatch` ou `edge_store_disabled` com status correto.

- [ ] 🟢 Implementar serializer de envelope edge.
  - Fonte: `C:\workspace\dale-vision\apps\edge\serializers.py`.
  - Critério de pronto: `event_name` obrigatório e campos opcionais compatíveis.

- [ ] 🟢 Implementar pipeline de ingestão `/api/edge/events/`.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: autentica, valida, deduplica, persiste receipt, projeta evento e retorna `receipt_id`.

- [ ] 🟢 Implementar geração de receipt id.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\receipts.py`.
  - Critério de pronto: vision usa bucket de minuto, retail usa bucket de 5 minutos e fallback usa hash de campos principais.

- [ ] 🟢 Implementar dedupe Redis e Postgres.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\vision_metrics.py`.
  - Critério de pronto: retry imediato retorna `cache_hit`/`deduped`; `event_receipts` usa `ON CONFLICT`.

- [ ] 🟢 Implementar update otimizado de `stores.last_seen_at`.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: eventos comuns respeitam throttle de 30s; heartbeat força update.

- [ ] 🟢 Implementar controle de `EdgeDevice`.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\stores\services\activation_registry.py`.
  - Critério de pronto: device retired é rejeitado; device visto é atualizado com versão e canal.

- [ ] 🟢 Implementar contratos vision e retail.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: payloads incompletos retornam `400` com reason específico.

- [ ] 🟢 Implementar persistência de `EdgeEventRaw`.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\models.py`.
  - Critério de pronto: eventos não-heartbeat criam raw log canônico.

- [ ] 🟢 Implementar projeções vision.
  - Fonte: `C:\workspace\dale-vision\apps\edge\vision_metrics.py`.
  - Critério de pronto: eventos suportados atualizam tabelas de métricas e receipts.

- [ ] 🟢 Implementar agregação por minuto.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\models.py`.
  - Critério de pronto: contador por `(store_id,event_name,minute_bucket)` é criado/incrementado.

- [ ] 🟢 Implementar pruning de estatísticas por minuto.
  - Fonte: `C:\workspace\dale-vision\apps\edge\management\commands\prune_edge_event_minute_stats.py`.
  - Critério de pronto: comando remove dados antigos com retenção default de 7 dias e `--dry-run`.

- [ ] 🟢 Implementar endpoints de câmeras para edge.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\urls.py`.
  - Critério de pronto: `/api/edge/cameras/` e `/api/edge/stores/{store_id}/cameras/` validam token e retornam câmeras ativas.

- [ ] 🟢 Implementar endpoint MVP legado.
  - Fonte: `C:\workspace\dale-vision\apps\edge\mvp_ingest.py`, `backend\urls.py`.
  - Critério de pronto: `/api/v1/ingest/events/` valida token, campos obrigatórios, store mismatch e idempotência.

- [ ] 🔴 Corrigir/validar referência `name` no fluxo de heartbeat.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views.py`.
  - Critério de pronto: busca por câmera por nome usa variável definida e teste cobre heartbeat sem `external_id`.

- [ ] 🟡 Atualizar testes legados do MVP ingest.
  - Fonte: `C:\workspace\dale-vision\apps\edge\tests_mvp_ingest.py`, `apps\edge\models.py`.
  - Critério de pronto: testes usam campos reais de `EdgeToken`.
