# Edge Agent Vision, Fluxos

## Fluxo 1: Inicialização do Worker

```mermaid
sequenceDiagram
    participant Runtime as main.py
    participant Worker as VisionWorker
    participant Thread as Thread daemon

    Runtime->>Runtime: Verifica VISION_ENABLED
    alt VISION_ENABLED=1
        Runtime->>Worker: VisionWorker(cloud_base_url, store_id, edge_token)
        Worker->>Worker: VisionConfig.from_env()
        Runtime->>Thread: start run_forever()
        Thread->>Worker: run_forever()
        Worker->>Worker: log startup
    else VISION_ENABLED!=1
        Runtime->>Runtime: Não inicia processamento de visão
    end
```

## Fluxo 2: Busca de Câmeras

```mermaid
flowchart TD
    A[tick_once] --> B{VISION_SOURCE=video?}
    B -- yes --> C[Retorna lista vazia no fluxo RTSP]
    B -- no --> D[Resolver CAMERA_SOURCE_MODE]
    D --> E{api_first e sync remoto habilitado?}
    E -- yes --> F[GET /api/edge/cameras/]
    F --> G{Câmeras válidas?}
    G -- yes --> H[Aplicar ROI e salvar cache]
    G -- no --> I[Tentar fallback local]
    E -- no --> I
    I --> J[CAMERAS_JSON env]
    J --> K{Vazio?}
    K -- yes --> L[Ler .env]
    L --> M{Vazio?}
    M -- yes --> N[Ler agent_config]
    N --> O{Vazio?}
    O -- yes --> P{local_only?}
    P -- yes --> Q[Retornar vazio]
    P -- no --> R[Ler cache]
    K -- no --> S[Normalizar câmeras]
    M -- no --> S
    O -- no --> S
    R --> S
    S --> H
```

## Fluxo 3: Processamento RTSP/Snapshot

```mermaid
flowchart TD
    A[Câmera normalizada] --> B[Resolver role]
    B --> C{Role existe?}
    C -- no --> D[Ignorar câmera]
    C -- yes --> E[Inicializar estado]
    E --> F[Tentar _fetch_rtsp_frame]
    F --> G{Frame RTSP ok?}
    G -- yes --> H[Processar frame]
    G -- no --> I[Tentar _fetch_snapshot_frame]
    I --> J{Snapshot ok?}
    J -- no --> K[Log snapshot missing]
    J -- yes --> H
    H --> L[Extrair ROI]
    L --> M[YOLO track]
    M --> N[Aplicar regra por role]
    N --> O[Enviar eventos atômicos]
    O --> P{Bucket mudou?}
    P -- yes --> Q[Enviar vision.metrics.v1]
    P -- no --> R[Continuar]
```

## Fluxo 4: Entrada, Line Crossing

```mermaid
flowchart TD
    A[Frame role=entrada] --> B[YOLO boxes]
    B --> C[Filtrar pessoa com track_id]
    C --> D[Calcular ponto do pé]
    D --> E[Calcular lado da linha]
    E --> F{Houve troca de lado?}
    F -- no --> G[Atualizar lado]
    F -- sim --> H{Cooldown >= 4s?}
    H -- no --> G
    H -- yes --> I{Direção}
    I -- negativo para positivo --> J[entries += 1]
    I -- positivo para negativo --> K[exits += 1]
    J --> L[Emitir vision.crossing.v1]
    K --> L
    L --> M[Emitir retail.event.v1 person_enter/person_exit]
```

## Fluxo 5: Balcão, Fila e Checkout Proxy

```mermaid
flowchart TD
    A[Frame role=balcao] --> B[YOLO boxes]
    B --> C[Pessoa em area_atendimento_fila]
    B --> D[Pessoa em zona_funcionario_caixa]
    B --> E[Pessoa em ponto_pagamento]
    C --> F[queue_length]
    D --> G[staff_active_est]
    E --> H[clients_at_pay]
    F --> I[Emitir vision.queue_state.v1]
    G --> I
    H --> J{Ciclo de pagamento terminou?}
    J -- sim --> K[Emitir vision.checkout_proxy.v1]
    K --> L[Emitir retail.event.v1 sale_completed]
    J -- no --> M[Manter ciclo]
    I --> N{Alertas habilitados?}
    N -- yes --> O[Avaliar fila longa, ociosidade e celular]
    N -- no --> P[Sem alertas]
```

## Fluxo 6: Salão, Ocupação e Dwell

```mermaid
flowchart TD
    A[Frame role=salao] --> B[YOLO pessoas]
    B --> C[Filtrar dentro de area_consumo]
    C --> D[Atualizar room_track_enter_ts]
    D --> E[Calcular dwell por track ativo]
    E --> F[Atualizar consumo_max e dwell samples]
    F --> G[Emitir vision.zone_occupancy.v1]
    G --> H[Emitir retail.event.v1 zone_dwell]
    H --> I[Remover tracks obsoletos]
```

## Fluxo 7: Envio e Outbox

```mermaid
sequenceDiagram
    participant Worker as VisionWorker
    participant Backend as /api/edge/events/
    participant Outbox as vision_outbox.sqlite

    Worker->>Worker: Monta envelope com receipt_id
    Worker->>Backend: POST envelope
    alt HTTP 2xx
        Backend-->>Worker: ok
        Worker->>Worker: log sent
    else falha HTTP/rede
        Backend-->>Worker: erro ou timeout
        Worker->>Outbox: enqueue(receipt_id, payload)
        Worker->>Worker: log queued
    end
    Worker->>Outbox: peek_batch()
    loop flush
        Worker->>Backend: POST payload pendente
        alt ok
            Worker->>Outbox: mark_sent()
        else falha abaixo do limite
            Worker->>Outbox: mark_failed(backoff)
        else max attempts
            Worker->>Outbox: mark_sent()
            Worker->>Worker: log drop
        end
    end
```

## Fluxo 8: Ingest Backend

```mermaid
flowchart TD
    A[POST /api/edge/events/] --> B[Validar serializer]
    B --> C[Extrair store_id e receipt_id]
    C --> D[Fast dedupe cache]
    D --> E{Cache hit?}
    E -- yes --> F[Responder deduped]
    E -- no --> G[Autenticar edge token]
    G --> H[Validar contrato vision/retail]
    H --> I[Validar câmera se aplicável]
    I --> J[Inserir event_receipt]
    J --> K{Já existia?}
    K -- yes --> L[Responder deduped]
    K -- no --> M[Persistir EdgeEventRaw]
    M --> N{event_name}
    N -- vision.metrics.v1 --> O[apply_vision_metrics]
    N -- vision.crossing.v1 --> P[insert atomic + apply crossing]
    N -- vision.queue_state.v1 --> Q[insert atomic + apply queue]
    N -- vision.checkout_proxy.v1 --> R[insert atomic + apply checkout]
    N -- vision.zone_occupancy.v1 --> S[insert atomic + apply occupancy]
    O --> T[mark receipt processed]
    P --> T
    Q --> T
    R --> T
    S --> T
```

## Fluxo 9: Replay por Vídeo

```mermaid
flowchart TD
    A[VISION_SOURCE=video] --> B[Validar VISION_VIDEO_PATH]
    B --> C[Construir câmera sintética]
    C --> D[Carregar ROI por VISION_ROI_PATH ou ProgramData]
    D --> E[VideoFrameSource.frames]
    E --> F{realtime?}
    F -- yes --> G[Sincronizar timestamps com sleep]
    F -- no --> H[Processar o mais rápido possível]
    G --> I[_process_frame]
    H --> I
    I --> J[Eventos e buckets iguais ao modo RTSP]
```

## Contratos de Saída

| Campo | Evento | Obrigatoriedade | Confiança |
|---|---|---|---|
| `event_name` | Todos | Obrigatório no envelope. | 🟢 |
| `source=edge` | Todos | Obrigatório para ingest edge. | 🟢 |
| `receipt_id` | Todos | Obrigatório para outbox/dedupe efetivo. | 🟢 |
| `idempotency_key` | Todos | Igual ao receipt nos eventos do worker. | 🟢 |
| `data.store_id` | Todos de visão | Obrigatório para projeção. | 🟢 |
| `data.camera_id` | Eventos por câmera | Necessário para validar câmera e presença. | 🟢 |
| `data.metric_type` | Eventos atômicos | Obrigatório no backend. | 🟢 |
| `data.bucket` | `vision.metrics.v1` | Obrigatório para bucket agregado. | 🟢 |
| `data.roi_entity_id` | Eventos com ROI | Usado nas projeções e dedupe semântico. | 🟢 |

## Pontos de Controle

- 🟢 CONFIRMADO: Sem câmera válida, o tick retorna sem erro fatal.
- 🟢 CONFIRMADO: Sem frame válido, a câmera é ignorada naquele tick.
- 🟢 CONFIRMADO: Sem ROI, `_process_frame()` retorna `None`.
- 🟢 CONFIRMADO: Falha YOLO retorna `None` e loga warning.
- 🟢 CONFIRMADO: Falha de envio vai para outbox quando habilitado.
- 🟢 CONFIRMADO: Backend rejeita contrato inválido antes de projeção.
- 🔴 LACUNA: Falta health metric específico para worker de visão no heartbeat principal.
