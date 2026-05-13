# edge - Edge Cases

## Autenticação

- 🟢 Ausência de token retorna `401 edge_token_invalid`.
- 🟢 `X-EDGE-TOKEN` deve vencer sobre `Authorization` mesmo se Authorization parecer JWT.
- 🟢 Token inválido é logado apenas como hash mascarado.
- 🟢 Token válido de outra store retorna `403 edge_store_mismatch`.
- 🟢 Store bloqueada ou com `blocked_reason` edge-disabled retorna `403 edge_store_disabled`.
- 🟢 Device retired retorna `403 edge_device_retired`.

## Envelope

- 🟢 `event_name` ausente retorna `400`.
- 🟢 `store_id` ausente pode ser preenchido pela store do token.
- 🟢 `store_id` não UUID retorna `400`.
- 🟢 `trace_id` ausente usa `receipt_id`.
- 🟡 Payload com `data` não-dict pode passar pelo serializer? O design assume `DictField`, então deve falhar validação.

## Deduplicação

- 🟢 Retry dentro de 60 segundos pode bater no Redis e retornar `cache_hit=true`.
- 🟢 Retry após expirar Redis ainda deve deduplicar por `event_receipts`.
- 🟢 `vision.*` no mesmo minuto com mesmos campos principais gera mesmo receipt.
- 🟢 `retail.event.v1` no mesmo bucket de 5 minutos gera mesmo receipt.
- 🟡 Dedupe Redis é feito antes de todas as validações; evento inválido com receipt estável pode influenciar retry imediato.

## Contratos

- 🟢 `vision.*` sem `metric_type`, `ownership` ou `roi_entity_id` retorna `vision_contract_invalid`.
- 🟢 Canônico de visão sem campos obrigatórios retorna `vision_canonical_contract_invalid`.
- 🟢 `retail.event.v1` com `confidence` não numérico retorna erro de confidence.
- 🟢 `retail.event.v1` com `event_type` fora da lista retorna `unsupported_event_type`.

## Câmeras

- 🟢 Evento dependente de câmera com `camera_id` inexistente retorna `camera_not_found`.
- 🟢 `camera_health` sem câmera encontrada retorna `camera_not_found` e marca receipt failed.
- 🟢 Heartbeat com câmera nova deve respeitar limite de trial.
- 🟢 Snapshot URL muito grande é descartada.
- 🔴 Fluxo de heartbeat contém busca por `name` aparentemente indefinida quando `external_id` não resolve.

## Persistência e projeção

- 🟢 Falha em `event_receipts` retorna `db_write_failed`.
- 🟢 Falha em `EdgeEventRaw` apenas loga warning e não bloqueia fluxo.
- 🟢 Falha em projeção vision marca receipt failed e retorna `500`.
- 🟢 Falha ao atualizar minute stats é logada e não bloqueia fluxo.

## MVP legado

- 🟢 Token ausente retorna `401`.
- 🟢 Campos obrigatórios ausentes retornam `400`.
- 🟢 Store mismatch retorna `403`.
- 🟢 Reenvio do mesmo `event_id` não duplica por `ON CONFLICT`.
- 🟡 Testes legados parecem defasados em relação ao modelo atual de `EdgeToken`.
