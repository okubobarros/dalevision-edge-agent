# Edge Agent Vision, Tasks

## Status da Unit

🟢 CONFIRMADO: A implementação principal do pipeline de visão já existe no legado, com testes para câmera, ROI, line crossing, queue, checkout proxy, occupancy, retail event, outbox, YAML e vídeo local.

## Tarefas Funcionais Documentadas

| ID | Tarefa | Status | Evidência | Critério de Pronto | Confiança |
|----|--------|--------|-----------|--------------------|-----------|
| T-01 | Documentar inicialização condicional do VisionWorker. | [X] | `src/dalevision_edge_agent/main.py` | Spec descreve `VISION_ENABLED` e thread daemon. | 🟢 |
| T-02 | Documentar `VisionConfig.from_env()`. | [X] | `src/dalevision_edge_agent/vision/worker.py` | Variáveis `VISION_*` principais listadas. | 🟢 |
| T-03 | Documentar busca de câmeras por API/env/cache. | [X] | `_fetch_cameras()`, `_fetch_cameras_from_edge()` | Ordem de fallback descrita. | 🟢 |
| T-04 | Documentar normalização de câmera e aliases RTSP/snapshot. | [X] | `_normalize_camera()`; `tests/test_vision_worker_line_roi.py` | Campos canônicos listados. | 🟢 |
| T-05 | Documentar ROI local/remoto/YAML. | [X] | `_apply_roi_to_cameras()`, `_extract_roi()`, `load_roi_yaml()` | Metadados de ROI preservados na spec. | 🟢 |
| T-06 | Documentar aquisição de frame RTSP/snapshot/video. | [X] | `_fetch_rtsp_frame()`, `_fetch_snapshot_frame()`, `VideoFrameSource` | Fluxos alternativos descritos. | 🟢 |
| T-07 | Documentar processamento por papel `entrada`. | [X] | `_process_frame()`; `test_process_frame_counts_line_crossing...` | Crossing entry/exit e cooldown descritos. | 🟢 |
| T-08 | Documentar processamento por papel `balcao`. | [X] | `_process_frame()`, `_track_checkout_cycle()` | Fila, staff, checkout e alertas descritos. | 🟢 |
| T-09 | Documentar processamento por papel `salao`. | [X] | `_process_frame()` | Ocupação e dwell descritos. | 🟢 |
| T-10 | Documentar contratos de eventos `vision.*`. | [X] | `_send_event()`, `_send_*_event()` | Tabela de eventos incluída. | 🟢 |
| T-11 | Documentar `retail.event.v1` derivado. | [X] | `_send_retail_event()`; teste de contrato v1 | Evento e idempotência descritos. | 🟢 |
| T-12 | Documentar outbox SQLite. | [X] | `vision/outbox.py`; `tests/test_vision_outbox.py` | Retry, dedupe local e backoff descritos. | 🟢 |
| T-13 | Documentar ingest/projeção no backend. | [X] | `C:\workspace\dale-vision\apps\edge\views.py`, `vision_metrics.py` | Dedupe/projeção/tabela atômica descritos. | 🟢 |
| T-14 | Documentar streaming HLS/snapshot local. | [X] | `streaming.py`, `setup_api.py` | Uso em onboarding descrito. | 🟢 |

## Tarefas de Validação Recomendadas

| ID | Tarefa | Status | Justificativa | Prioridade |
|----|--------|--------|---------------|------------|
| V-01 | Criar teste/harness com vídeo real curto, OpenCV e ultralytics. | [ ] | Garante que `_yolo_track()` e ROI funcionam fora de mocks. | Must |
| V-02 | Criar contrato JSON Schema para `vision.metrics.v1`. | [ ] | Backend exige campos como `metric_type`; schema evita regressão. | Must |
| V-03 | Criar contrato JSON Schema para eventos atômicos `vision.crossing`, `queue_state`, `zone_occupancy`, `checkout_proxy`. | [ ] | Eventos têm projeções diferentes e campos obrigatórios diferentes. | Must |
| V-04 | Criar teste integrado edge -> backend para dedupe por receipt. | [ ] | Confirma equivalência entre receipt gerado no edge e dedupe backend. | Must |
| V-05 | Medir CPU/RAM/FPS por hardware de cliente com 1, 3 e 10 câmeras. | [ ] | `VISION_MAX_CAMERAS=10` pode ser alto para máquinas modestas. | Should |
| V-06 | Definir retenção e vacuum do `vision_outbox.sqlite`. | [ ] | Evita crescimento indefinido em loja offline. | Should |
| V-07 | Separar `VisionWorker` em módulos menores. | [ ] | Arquivo atual concentra responsabilidades e aumenta risco de regressão. | Could |
| V-08 | Revisar exposição de HLS/snapshot local quando host não for loopback. | [ ] | Setup API tem CORS aberto e pode expor imagens localmente. | Should |
| V-09 | Decidir destino do `VISION_PROXY_ENABLED`. | [ ] | Proxy sintético pode confundir métricas reais se usado em produção. | Should |

## Testes Existentes

| Teste | Cobertura | Confiança |
|-------|-----------|-----------|
| `tests/test_vision_worker_cameras.py::test_fetch_cameras_uses_cameras_json_without_v1_calls` | Modo local por `CAMERAS_JSON`. | 🟢 |
| `tests/test_vision_worker_cameras.py::test_fetch_cameras_prefers_api_when_source_mode_api_first` | Preferência por API edge. | 🟢 |
| `tests/test_vision_worker_cameras.py::test_fetch_cameras_uses_env_file_fallback_when_process_env_is_empty` | Fallback `.env`. | 🟢 |
| `tests/test_vision_worker_cameras.py::test_fetch_cameras_enriches_local_cameras_with_remote_roi` | Enriquecimento ROI remoto. | 🟢 |
| `tests/test_vision_worker_cameras.py::test_resolve_role_maps_caixa_name_to_balcao` | Inferência de papel por nome. | 🟢 |
| `tests/test_vision_worker_line_roi.py::test_process_frame_counts_line_crossing_and_builds_context_payload` | Line crossing e payload de entrada. | 🟢 |
| `tests/test_vision_worker_line_roi.py::test_process_frame_emits_queue_state_with_queue_roi_context` | Fila e staff no balcão. | 🟢 |
| `tests/test_vision_worker_line_roi.py::test_process_frame_emits_checkout_proxy_when_payment_cycle_finishes` | Proxy de checkout. | 🟢 |
| `tests/test_vision_worker_line_roi.py::test_process_frame_emits_zone_occupancy_with_room_roi_context` | Ocupação e dwell no salão. | 🟢 |
| `tests/test_vision_worker_line_roi.py::test_send_retail_event_uses_contract_v1` | Contrato `retail.event.v1`. | 🟢 |
| `tests/test_vision_outbox.py` | Enqueue, flush, recovery e entrada canônica. | 🟢 |
| `tests/test_vision_roi_yaml.py` | Parse de YAML ROI. | 🟢 |
| `tests/test_vision_video_source.py` | Erro para vídeo ausente. | 🟢 |
| `C:\workspace\dale-vision\apps\edge\tests.py` | Ingest `/api/edge/events/`, receipt e contratos retail/vision. | 🟢 |

## Checklist de Reimplementação

- [ ] Preservar `VISION_ENABLED` como feature flag principal.
- [ ] Preservar `VisionConfig.from_env()` e defaults atuais.
- [ ] Preservar ordem de fallback de câmeras: API, env, `.env`, config, cache.
- [ ] Preservar aliases `rtsp_url`, `stream_url`, `rtsp`, `url`.
- [ ] Preservar aliases `last_snapshot_url`, `snapshot_url`, `snapshot`.
- [ ] Preservar canonicalização de ROI para fila, caixa, consumo e entrada.
- [ ] Preservar papéis `entrada`, `balcao`, `salao`.
- [ ] Preservar eventos `vision.*` e `retail.event.v1`.
- [ ] Preservar `receipt_id`/`idempotency_key` determinísticos.
- [ ] Preservar outbox SQLite offline-first.
- [ ] Preservar redaction de credenciais RTSP em logs.
- [ ] Preservar contrato backend de `/api/edge/events/`.

## Ordem Recomendada de Migração

1. Extrair schemas de eventos e testes de contrato edge/backend.
2. Isolar aquisição de câmeras em módulo próprio.
3. Isolar ROI e geometria em módulo próprio.
4. Isolar detectores/regras por papel de câmera.
5. Isolar envio/outbox com interface testável.
6. Implementar replay por vídeo como harness de validação.
7. Validar integração com backend em ambiente de staging.
