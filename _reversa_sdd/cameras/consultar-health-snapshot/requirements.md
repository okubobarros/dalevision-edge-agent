# consultar-health-snapshot - Requirements

## Escopo

- 🟢 Caso de uso de health, teste RTSP e snapshots de câmera.

## Requisitos

- 🟢 Health deve aceitar usuário gestor ou Edge Token.
- 🟢 Health deve criar log e atualizar câmera.
- 🟢 Health online/degraded deve completar onboarding.
- 🟢 Teste RTSP deve ter hard timeout.
- 🟢 Snapshot backend deve usar Supabase Storage e URL assinada.
- 🟢 Snapshot edge deve validar store do token.
- 🟢 Consulta de snapshot deve retornar signed URL quando há storage_key.
- 🟢 Fallback por `last_snapshot_url` deve existir.

## Critérios de Aceitação

- 🟢 Edge Token válido registra health.
- 🟢 RTSP timeout retorna resposta controlada.
- 🟢 Upload JPEG/PNG retorna `snapshot_url` com expiração.
- 🟢 Snapshot inexistente retorna `SNAPSHOT_NOT_FOUND`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\services.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\views_snapshot.py`.
