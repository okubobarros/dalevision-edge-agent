# ingerir-eventos-edge - Design

## Pipeline

- 🟢 `EdgeEventsIngestView` concentra o pipeline de ingestão.
- 🟢 O pipeline é síncrono: valida, persiste e projeta antes de responder.
- 🟢 Dedupe tem duas camadas: Redis para retry rápido e Postgres para garantia.
- 🟢 Projeções de visão são executadas apenas após receipt novo.

## Handlers por evento

- 🟢 `vision.metrics.v1`: aplica métricas agregadas de tráfego/conversão.
- 🟢 `vision.crossing.v1`: insere evento atômico e acumula footfall.
- 🟢 `vision.queue_state.v1`: insere evento atômico e calcula fila.
- 🟢 `vision.checkout_proxy.v1`: deriva checkout events.
- 🟢 `vision.zone_occupancy.v1`: deriva ocupação e dwell.
- 🟢 `camera_health`: atualiza câmera e health log.
- 🟢 `edge_heartbeat`/`camera_heartbeat`/`edge_camera_heartbeat`: atualiza store/câmeras e transições.
- 🟢 `alert`: reencaminha para ingestão de alerts.
- 🟢 Demais eventos: marcam receipt processed e retornam ok.

## Persistência

- 🟢 `event_receipts` é escrito antes das projeções.
- 🟢 `EdgeEventRaw` é best-effort e não bloqueante.
- 🟢 `EdgeEventMinuteStats` é best-effort e não bloqueante.
- 🟢 Receipts são marcados processed/failed conforme resultado do handler.

## Respostas

- 🟢 Novo evento processado normalmente retorna `201`.
- 🟢 Evento duplicado retorna `200`.
- 🟢 Falha de contrato retorna `400`.
- 🟢 Falha de projeção retorna `500`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
