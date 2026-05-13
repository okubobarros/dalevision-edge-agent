# edge - Design

## Visão Geral

- 🟢 `apps.edge` é a borda HTTP do backend para receber telemetria e eventos do agente local.
- 🟢 A entrada principal é `EdgeEventsIngestView`.
- 🟢 A estratégia central é: autenticar, normalizar, deduplicar, persistir receipt, projetar efeitos operacionais e responder com `receipt_id`/`trace_id`.
- 🟢 O módulo usa uma combinação de DRF, cache Django/Redis, SQL direto em `event_receipts` e modelos Django para tabelas próprias do app edge.

## Componentes

### Autenticação

- 🟢 `authenticate_edge_token` extrai token de múltiplos headers, query param e Authorization.
- 🟢 `EdgeAwareJWTAuthentication` evita tratar Edge Token explícito como JWT de usuário.
- 🟢 `EdgeOrUserTokenPermission` e `EdgeTokenPermission` oferecem permissões alternativas para views que precisem de autorização por edge/user.

### Ingestão

- 🟢 `EdgeEventsIngestView.post` valida `EdgeEventSerializer`, resolve `store_id`, `receipt_id`, `trace_id`, dedupe Redis, autenticação, device touch, contratos e persistência.
- 🟢 `MvpEventIngestView` mantém ingestão minimalista legada para `/api/v1/ingest/events/`.

### Persistência

- 🟢 `insert_event_receipt_if_new` escreve em `public.event_receipts` com `ON CONFLICT DO NOTHING`.
- 🟢 `EdgeEventRaw` guarda raw canonicalizado para eventos não-heartbeat.
- 🟢 `EdgeEventMinuteStats` guarda contadores por minuto.
- 🟢 `mark_event_receipt_processed` e `mark_event_receipt_failed` atualizam status operacional do receipt.

### Projeções

- 🟢 `apply_vision_metrics`, `apply_vision_crossing`, `apply_vision_queue_state`, `apply_vision_checkout_proxy` e `apply_vision_zone_occupancy` transformam eventos de visão em métricas.
- 🟢 `insert_vision_atomic_event_if_new` cria amostra atômica com `ON CONFLICT`.
- 🟢 `_resolve_camera_role_with_zone_precedence` usa semântica de zona/ROI para inferir papel da câmera.

### Status Events

- 🟢 Heartbeat pode emitir `store_status_changed` e `camera_status_changed`.
- 🟢 `status_events.py` envia webhook N8N quando `N8N_EVENTS_WEBHOOK` está configurado.
- 🟢 Eventos de status usam idempotência por receipt e cooldown por status.

## Fluxo Principal

1. 🟢 Cliente envia POST `/api/edge/events/`.
2. 🟢 Serializer valida envelope mínimo.
3. 🟢 View extrai `store_id`, `receipt_id` e `trace_id`.
4. 🟢 Redis tenta dedupe rápido por 60 segundos.
5. 🟢 View normaliza `event_name` e nome canônico.
6. 🟢 Se houver Knox user token, valida acesso à store.
7. 🟢 Caso contrário, autentica Edge Token.
8. 🟢 View rejeita store inválida, device retired ou contrato inválido.
9. 🟢 View atualiza `stores.last_seen_at`.
10. 🟢 View valida câmera para eventos que dependem de câmera.
11. 🟢 View insere receipt canônico.
12. 🟢 Duplicata retorna `200`.
13. 🟢 Evento novo persiste `EdgeEventRaw` quando não heartbeat.
14. 🟢 View incrementa `EdgeEventMinuteStats`.
15. 🟢 View executa handler específico por tipo de evento.
16. 🟢 Receipt é marcado como processed ou failed.

## Idempotência

- 🟢 Prioridade de receipt: `idempotency_key`, depois `receipt_id`, depois hash calculado.
- 🟢 Redis reduz custo de retries imediatos.
- 🟢 Postgres é a fonte de verdade contra duplicidade.
- 🟢 `vision.*` usa bucket de minuto.
- 🟢 `retail.event.v1` usa bucket de 5 minutos.
- 🟢 Status outgoing usa receipt determinístico por transição/cooldown.

## Modelos

| Modelo | Função | Confiança |
| --- | --- | --- |
| `EdgeToken` | token hash ativo por store | 🟢 |
| `EdgeEventMinuteStats` | contagem por minuto | 🟢 |
| `EdgeDevice` | device local e versão instalada | 🟢 |
| `EdgeEventRaw` | log raw canônico de eventos não-heartbeat | 🟢 |
| `EdgeUpdatePolicy` | policy de update | 🟢 |
| `EdgeUpdateEvent` | reports de update | 🟢 |
| `EdgeRelease` | release Windows por canal | 🟢 |
| `ActivationToken` | ativação do agente | 🟢 |

## Eventos Suportados

- 🟢 `edge_heartbeat`.
- 🟢 `camera_heartbeat`.
- 🟢 `edge_camera_heartbeat`.
- 🟢 `camera_health`.
- 🟢 `alert`.
- 🟢 `retail.event.v1`.
- 🟢 `vision.metrics.v1`.
- 🟢 `vision.crossing.v1`.
- 🟢 `vision.queue_state.v1`.
- 🟢 `vision.checkout_proxy.v1`.
- 🟢 `vision.zone_occupancy.v1`.
- 🟡 Outros nomes são aceitos como receipt genérico e retornam `ok=true` após marcar processed.

## Decisões

- 🟢 O backend aceita múltiplos formatos de token para compatibilidade com builds antigos do agente.
- 🟢 Heartbeats não são gravados em `EdgeEventRaw` para reduzir custo de armazenamento.
- 🟢 `stores.last_seen_at` é throttled em eventos comuns, mas forçado para heartbeat.
- 🟢 Projeções de visão usam SQL direto para upsert/insert em tabelas de métricas.
- 🟢 O endpoint MVP legado mantém contrato mínimo separado do endpoint atual.

## Riscos e Lacunas

- 🔴 Em `EdgeEventsIngestView`, há referência a `name` ao procurar câmera por nome no fluxo de heartbeat; a origem dessa variável não está clara no trecho analisado.
- 🟡 Testes de `mvp_ingest` parecem usar campos antigos de `EdgeToken` (`store`, `name`, `token_cleartext`) que não aparecem no modelo atual.
- 🟡 `EdgeEventRaw` falha apenas em warning, então perda de raw auditável não bloqueia o processamento.
- 🟡 Dedupe Redis ocorre antes de validações completas; se um evento inválido criar cache key, retries imediatos podem ser afetados dependendo de store/receipt.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\auth.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\vision_metrics.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\status_events.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 `C:\workspace\dale-vision\backend\urls.py`.
