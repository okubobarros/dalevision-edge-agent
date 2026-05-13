# ingerir-eventos-edge - Requirements

## Escopo

- 🟢 Caso de uso principal de ingestão em `/api/edge/events/`.
- 🟢 Fonte principal: `C:\workspace\dale-vision\apps\edge\views.py`.

## Requisitos

- 🟢 Validar payload com `EdgeEventSerializer`.
- 🟢 Resolver `store_id` a partir de `data`, payload raiz ou `agent`.
- 🟢 Resolver `receipt_id` por `idempotency_key`, `receipt_id` ou hash.
- 🟢 Resolver `trace_id` ou usar `receipt_id`.
- 🟢 Deduplicar via cache Redis por 60 segundos.
- 🟢 Autenticar por Knox user token ou Edge Token.
- 🟢 Rejeitar store inválida, token inválido, mismatch, disabled e device retired.
- 🟢 Atualizar `EdgeDevice` visto.
- 🟢 Validar contratos `vision.*` e `retail.event.v1`.
- 🟢 Atualizar `stores.last_seen_at`.
- 🟢 Validar câmera para eventos dependentes de câmera.
- 🟢 Inserir `event_receipts`.
- 🟢 Persistir `EdgeEventRaw` para eventos não-heartbeat.
- 🟢 Incrementar estatística por minuto.
- 🟢 Despachar handlers específicos por evento.
- 🟢 Retornar `ok`, `receipt_id`, `trace_id`, `stored` e `deduped`.

## Critérios de Aceitação

- 🟢 Evento novo válido retorna `201` e `stored=true`.
- 🟢 Evento duplicado retorna `200` e `deduped=true`.
- 🟢 Contrato inválido retorna `400` sem projetar métricas.
- 🟢 Erro de banco em receipt retorna `db_write_failed`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\serializers.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\vision_metrics.py`.
