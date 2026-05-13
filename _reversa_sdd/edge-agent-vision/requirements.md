# Edge Agent Vision

## Visão Geral

🟢 CONFIRMADO: Esta unit define o pipeline opcional de visão computacional do DaleVision Edge Agent, responsável por ler frames de RTSP, snapshot remoto ou vídeo local, aplicar YOLO/ROI, calcular métricas por câmera e enviar eventos para o backend em `/api/edge/events/`.

🟢 CONFIRMADO: O pipeline é controlado por `VISION_ENABLED`; quando desabilitado, o worker registra que está desabilitado e não executa processamento de visão.

🟢 CONFIRMADO: O backend em `C:\workspace\dale-vision` recebe os eventos de visão, valida contrato, deduplica por `receipt_id`/`idempotency_key`, persiste eventos atômicos e projeta métricas de tráfego/conversão.

## Responsabilidades

- 🟢 CONFIRMADO: Carregar configuração de visão via variáveis `VISION_*`.
- 🟢 CONFIRMADO: Buscar câmeras por API edge, `CAMERAS_JSON`, `.env`, `agent_config.json` ou cache local.
- 🟢 CONFIRMADO: Normalizar câmera com `camera_id`, `rtsp_url`, `last_snapshot_url`, indicadores e plano de processamento.
- 🟢 CONFIRMADO: Carregar ROI local por YAML, ROI remoto por backend ou override global `VISION_ROI_PATH`.
- 🟢 CONFIRMADO: Ler frame por RTSP com OpenCV; se falhar, tentar frame por snapshot remoto.
- 🟢 CONFIRMADO: Em modo replay, ler frames de vídeo local por `VISION_SOURCE=video`.
- 🟢 CONFIRMADO: Processar detecções YOLO com tracking para pessoas e opcionalmente celular.
- 🟢 CONFIRMADO: Calcular métricas para papéis `entrada`, `balcao` e `salao`.
- 🟢 CONFIRMADO: Enviar eventos `vision.metrics.v1`, `vision.crossing.v1`, `vision.queue_state.v1`, `vision.zone_occupancy.v1`, `vision.checkout_proxy.v1` e `retail.event.v1`.
- 🟢 CONFIRMADO: Enfileirar eventos em outbox SQLite quando o backend estiver indisponível.
- 🟢 CONFIRMADO: Emitir alertas opcionais para ociosidade, fila longa e uso de celular.
- 🟢 CONFIRMADO: Expor HLS/snapshot local via Setup API e `StreamManager` para onboarding/visualização local.

## Regras de Negócio

- 🟢 CONFIRMADO: `VISION_ENABLED=0` impede execução do worker de visão.
- 🟢 CONFIRMADO: `VISION_SOURCE=video` usa MP4 local e desabilita camera sync por padrão quando `CAMERA_SYNC_ENABLED` não foi explicitamente definido.
- 🟢 CONFIRMADO: O worker limita processamento ao máximo de `VISION_MAX_CAMERAS`, padrão `10`.
- 🟢 CONFIRMADO: Buckets de métricas usam `VISION_BUCKET_SECONDS`, padrão `30`.
- 🟢 CONFIRMADO: Polling do worker usa `VISION_POLL_SECONDS`, padrão `5`.
- 🟢 CONFIRMADO: `VISION_FRAME_STRIDE` reduz frequência de inferência, processando apenas frames cujo índice respeita o stride.
- 🟢 CONFIRMADO: Câmera sem papel resolvido é ignorada no tick de visão.
- 🟢 CONFIRMADO: Câmera sem `rtsp_url` pode ser aceita se possuir `last_snapshot_url`.
- 🟢 CONFIRMADO: Para `entrada`, crossing de linha gera `entry` quando o ponto cruza de lado negativo para não-negativo, e `exit` quando cruza de positivo para não-positivo.
- 🟢 CONFIRMADO: Para `balcao`, zona `area_atendimento_fila` conta fila, `zona_funcionario_caixa` conta staff e `ponto_pagamento` alimenta proxy de checkout.
- 🟢 CONFIRMADO: Para `salao`, zona `area_consumo` conta ocupação e estima dwell por track.
- 🟢 CONFIRMADO: Eventos atômicos incluem `metric_type`, `ownership`, `zone_id`, `roi_entity_id`, `roi_version` e `confidence`.
- 🟢 CONFIRMADO: Evento agregado `vision.metrics.v1` inclui `ownership.mode=single_camera_owner`.
- 🟢 CONFIRMADO: `retail.event.v1` é emitido junto com crossing, queue, staff, zone dwell e checkout proxy quando `VISION_RETAIL_EVENT_V1_ENABLED=1`.
- 🟢 CONFIRMADO: Outbox usa `receipt_id` único e `INSERT OR IGNORE`, evitando duplicidade local.
- 🟢 CONFIRMADO: Backoff do outbox cresce exponencialmente e é limitado a 300 segundos.
- 🟢 CONFIRMADO: Após `VISION_OUTBOX_MAX_ATTEMPTS`, evento pendente pode ser descartado com log de erro.
- 🟢 CONFIRMADO: Thumbnail de alerta só é anexada quando `VISION_EMBED_THUMBNAIL=1`; se anexada, pode ser blurada.
- 🟡 INFERIDO: O pipeline atual é desenhado para métricas operacionais de varejo/restaurante, não para auditoria forense ou identificação biométrica.
- 🔴 LACUNA: Não há teste automatizado end-to-end que execute OpenCV + YOLO real + backend real com vídeo/RTSP.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟢 O runtime deve iniciar o `VisionWorker` em thread separada quando `VISION_ENABLED=1`. | Must | `main.py` instancia `VisionWorker`, chama `run_forever()` em thread daemon e mantém o loop principal do agente. |
| RF-02 | 🟢 O worker deve carregar `VisionConfig` a partir de variáveis `VISION_*`. | Must | `VisionConfig.from_env()` popula source, bucket, poll, thresholds, outbox, vídeo e ROI. |
| RF-03 | 🟢 O worker deve buscar câmeras por API edge quando `CAMERA_SYNC_ENABLED=1` e `VISION_REMOTE_CAMERA_SYNC_ENABLED=1`. | Must | `_fetch_cameras_from_edge()` tenta `/api/edge/cameras/` e `/api/edge/stores/{store_id}/cameras/`. |
| RF-04 | 🟢 O worker deve usar `CAMERAS_JSON` e cache como fallback quando API edge falha ou está desabilitada. | Must | `_fetch_cameras()` usa env, `.env`, `agent_config`, cache e flags local-only. |
| RF-05 | 🟢 O worker deve aceitar câmeras com RTSP ou apenas snapshot remoto. | Should | `_normalize_camera()` aceita `rtsp_url`/aliases ou `last_snapshot_url`/aliases. |
| RF-06 | 🟢 O worker deve carregar ROI local/remoto e preservar metadados de zona/linha. | Must | `_apply_roi_to_cameras()` e `_extract_roi()` preservam `zone_id`, `roi_entity_id`, `metric_type`, `ownership`. |
| RF-07 | 🟢 O worker deve processar frames por RTSP, snapshot ou vídeo local. | Must | `_fetch_rtsp_frame()`, `_fetch_snapshot_frame()` e `_run_video_forever()` cobrem as fontes. |
| RF-08 | 🟢 O worker deve executar YOLO tracking e calcular métricas por papel de câmera. | Must | `_process_frame()` trata papéis `entrada`, `balcao`, `salao`. |
| RF-09 | 🟢 O worker deve publicar eventos agregados `vision.metrics.v1` por bucket. | Must | `_build_payload()` e `_send_event()` geram envelope com receipt determinístico. |
| RF-10 | 🟢 O worker deve publicar eventos atômicos de crossing, queue, occupancy e checkout proxy. | Must | `_send_crossing_event()`, `_send_queue_state_event()`, `_send_zone_occupancy_event()`, `_send_checkout_proxy_event()`. |
| RF-11 | 🟢 O worker deve publicar `retail.event.v1` derivado dos eventos de visão quando habilitado. | Should | `_send_retail_event()` usa `compute_idempotency_key()` e `_send_or_enqueue()`. |
| RF-12 | 🟢 O worker deve enfileirar eventos quando envio falhar. | Must | `_send_or_enqueue()` grava no `VisionOutbox` quando `_send_now()` falha. |
| RF-13 | 🟢 O backend deve deduplicar e projetar eventos de visão. | Must | `apps/edge/views.py` usa receipts e chama `apply_vision_*`; `vision_atomic_events` possui `receipt_id UNIQUE`. |
| RF-14 | 🟢 O worker deve mascarar credenciais RTSP em logs diagnósticos de ffmpeg. | Must | `_log_ffmpeg_open_failed()` substitui URL por `mask_rtsp_url()` e `_redact_rtsp_secrets()`. |
| RF-15 | 🟢 A Setup API deve permitir streaming HLS e snapshot local para onboarding. | Should | `setup_api.py` integra `stream_manager` e `streaming.py` cria HLS/snapshot por ffmpeg. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Disponibilidade | Falha de envio de evento não deve perder o dado imediatamente. | `VisionOutbox` com SQLite, retry e backoff. | 🟢 |
| Disponibilidade | Falha no worker de visão não deve derrubar o heartbeat principal. | `main.py` executa worker em thread com try/except. | 🟢 |
| Operabilidade | Logs devem explicar tentativa RTSP, bucket, outbox e falhas YOLO. | Logs `[VISION] rtsp attempt`, `bucket`, `outbox flush`, `yolo failed`. | 🟢 |
| Segurança | Senhas RTSP devem ser mascaradas em logs de diagnóstico. | `mask_rtsp_url()` e `_redact_rtsp_secrets()`. | 🟢 |
| Privacidade | Thumbnail de alerta deve ser opcional e blurado por padrão quando gerado. | `VISION_EMBED_THUMBNAIL=0`, `VISION_BLUR_ENABLED=1`, `_build_thumbnail()`. | 🟢 |
| Performance | Stride e bucket devem reduzir custo computacional. | `VISION_FRAME_STRIDE`, `VISION_BUCKET_SECONDS`, `VISION_POLL_SECONDS`. | 🟢 |
| Resiliência | OpenCV/YOLO ausente deve degradar com logs, sem bloquear agente. | README e `_yolo_track()` capturam exceção e retornam `None`. | 🟢 |
| Idempotência | Eventos enviados devem ter `receipt_id`/`idempotency_key`. | `_send_event()`, eventos atômicos e `VisionOutbox.enqueue()`. | 🟢 |
| Integridade | Backend deve rejeitar contratos de visão inválidos. | `EdgeEventsIngestView` chama `_validate_vision_contract()` e retorna `vision_contract_invalid`. | 🟢 |

## Critérios de Aceitação

```gherkin
Dado um agente com VISION_ENABLED=1
Quando o runtime principal iniciar
Então deve criar um VisionWorker em thread separada
E o heartbeat principal deve continuar independente do resultado do worker
```

```gherkin
Dado CAMERA_SOURCE_MODE=api_first e API edge disponível
Quando o worker buscar câmeras
Então deve usar a lista retornada pelo backend
E deve salvar cache local de câmeras
```

```gherkin
Dado API edge indisponível e CAMERAS_JSON válido
Quando o worker buscar câmeras
Então deve usar as câmeras locais
E não deve fazer chamadas remotas quando camera sync estiver desabilitado
```

```gherkin
Dado uma câmera de entrada com linha ROI definida
Quando uma pessoa rastreada cruzar a linha no sentido de entrada
Então o worker deve incrementar entries e line_crossings_count
E deve emitir vision.crossing.v1 com direction=entry
```

```gherkin
Dado uma câmera de balcão com zona de fila
Quando pessoas forem detectadas na zona area_atendimento_fila
Então o worker deve emitir vision.queue_state.v1 com count_value igual ao tamanho da fila
E deve atualizar conversion.queue_avg_seconds no bucket agregado
```

```gherkin
Dado uma câmera de salão com zona area_consumo
Quando pessoas forem rastreadas dentro da zona
Então o worker deve emitir vision.zone_occupancy.v1
E deve estimar dwell_seconds_avg no payload agregado
```

```gherkin
Dado backend indisponível durante envio de evento
Quando _send_or_enqueue falhar no POST
Então o evento deve ser salvo no outbox SQLite
E deve ser reenviado quando _flush_outbox conseguir enviar novamente
```

```gherkin
Dado um evento de visão já recebido pelo backend
Quando o mesmo receipt_id for reenviado
Então o backend deve responder sucesso deduplicado
E não deve duplicar projeções de métricas
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Inicialização condicional por `VISION_ENABLED` | Must | Evita custo de CV quando a feature não está ativa. |
| Busca/normalização de câmeras | Must | Sem câmera válida não há processamento. |
| ROI e papéis de câmera | Must | Determinam significado dos eventos e projeções. |
| Eventos de visão com idempotência | Must | Contrato com backend e base das métricas. |
| Outbox SQLite | Must | Protege eventos em falha de rede. |
| Alertas operacionais | Should | Útil para operação, mas métricas continuam sem alertas. |
| Replay por vídeo local | Should | Essencial para validação/dev, não para runtime principal da loja. |
| HLS/snapshot local | Could | Ajuda onboarding, mas não é necessário para métricas. |
| Vision proxy sintético | Could | Existe como fallback/proxy no `main.py`, mas não representa inferência real. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `src/dalevision_edge_agent/main.py` | Inicialização do `VisionWorker`, `VISION_PROXY_ENABLED`, auto model path | 🟢 |
| `src/dalevision_edge_agent/vision/worker.py` | `VisionConfig`, `VisionWorker`, processamento, eventos e outbox | 🟢 |
| `src/dalevision_edge_agent/vision/outbox.py` | `VisionOutbox` SQLite | 🟢 |
| `src/dalevision_edge_agent/vision/geometry.py` | `point_in_polygon`, `line_side` | 🟢 |
| `src/dalevision_edge_agent/vision/logic/motion.py` | `AdaptiveMotionGate` | 🟢 |
| `src/dalevision_edge_agent/vision/sources/video.py` | `VideoFrameSource` | 🟢 |
| `src/dalevision_edge_agent/vision/roi_yaml.py` | `load_roi_yaml` | 🟢 |
| `src/dalevision_edge_agent/streaming.py` | `StreamManager` HLS/snapshot | 🟢 |
| `src/dalevision_edge_agent/cameras.py` | `send_vision_metrics_event`, `build_rtsp_candidates`, snapshot helpers | 🟢 |
| `C:\workspace\dale-vision\apps\edge\views.py` | `EdgeEventsIngestView` ingest/dedupe/projeção | 🟢 |
| `C:\workspace\dale-vision\apps\edge\vision_metrics.py` | `apply_vision_*`, `insert_vision_atomic_event_if_new` | 🟢 |
| `C:\workspace\dale-vision\apps\edge\migrations\0006_vision_atomic_events.py` | Tabela `vision_atomic_events` | 🟢 |
| `tests/test_vision_worker_cameras.py` | Câmeras, ROI remoto/local, papéis e indicadores | 🟢 |
| `tests/test_vision_worker_line_roi.py` | Crossing, queue, checkout, occupancy, retail event | 🟢 |
| `tests/test_vision_outbox.py` | Outbox e recovery de rede | 🟢 |
| `tests/test_vision_roi_yaml.py` | ROI YAML | 🟢 |
| `tests/test_vision_video_source.py` | Vídeo local ausente | 🟢 |

## Lacunas de Validação

- 🔴 Validar pipeline com OpenCV + ultralytics + vídeo real em CI ou harness controlado.
- 🔴 Validar uso de CPU/RAM em computador de cliente com múltiplas câmeras e `VISION_MAX_CAMERAS` alto.
- 🔴 Definir política de retenção/compactação do `vision_outbox.sqlite`.
- 🔴 Definir contratos formais versionados para todos os payloads `vision.*` e `retail.event.v1`.
- 🟡 Confirmar se `VISION_PROXY_ENABLED` deve permanecer como fallback de produto ou apenas modo legado/debug.
