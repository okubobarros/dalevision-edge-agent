# cameras - Design

## Visão Geral

- 🟢 `apps.cameras` fornece a API de gestão e diagnóstico de câmeras.
- 🟢 O modelo principal `Camera` é unmanaged em `apps.core.models` e espelha a tabela `cameras`.
- 🟢 Modelos específicos do app cameras (`CameraROIConfig`, `CameraHealth`, `CameraSnapshot`) também são unmanaged e espelham tabelas existentes.
- 🟢 O módulo integra permissões, billing/paywall, onboarding, journey events, Supabase Storage e Edge Token.

## Componentes

### CameraViewSet

- 🟢 CRUD principal de câmeras.
- 🟢 Actions: `test-snapshot`, `roi`, `roi/latest`, `health`, `test_connection`, `test-connection`, `snapshot/upload`, `snapshot`.
- 🟢 Usa `CameraSerializer` e permissões por store.

### Serializers

- 🟢 `CameraSerializer` expõe campos de câmera, health recente e RTSP mascarado.
- 🟢 `CameraROIConfigSerializer` expõe camera, version, config_json, updated_at e updated_by.
- 🟢 `CameraHealthLogSerializer` é read-only para logs.
- 🟢 `CameraHealthSerializer` cobre health agregado `camera_health`.

### Serviços

- 🟢 `rtsp_probe_with_hard_timeout` executa probe RTSP com processo separado por padrão.
- 🟢 `rtsp_snapshot` captura frame com OpenCV quando disponível.
- 🟢 `enforce_trial_camera_limit` aplica limite por plano.
- 🟢 Helpers em `roi.py` versionam e consultam ROI.

### Snapshot Edge

- 🟢 `EdgeSnapshotUploadView` recebe snapshot do agente via Edge Token.
- 🟢 Atualiza `last_snapshot_url` para o dashboard usar sem túnel P2P.

## Dados

### Camera

- 🟢 Campos incluem `store`, `zone`, `name`, `external_id`, `brand`, `model`, `ip`, `onvif`, `active`, `rtsp_url`, `username`, `password`, `indicators`, `status`, `last_seen_at`, `last_snapshot_url`, `last_error`, timestamps.

### CameraHealthLog

- 🟢 Guarda histórico por câmera com `checked_at`, `status`, `latency_ms`, `snapshot_url`, `error`.

### CameraROIConfig

- 🟢 Guarda versões de ROI por `(camera, version)` com `config_json`, `updated_by`, `updated_at`.

### CameraSnapshot

- 🟢 Guarda `snapshot_url`, `storage_key`, `captured_at`, `metadata`.

## Fluxos

- 🟢 Cadastro: validar store, role, entitlement, limite, serializer, salvar e logar jornada.
- 🟢 ROI: ler latest/published/history ou criar nova versão com workflow state.
- 🟢 Health: validar auth, normalizar status, criar log, atualizar câmera e onboarding.
- 🟢 Teste RTSP: rodar probe, atualizar câmera e criar health log.
- 🟢 Snapshot: subir arquivo, criar catálogo, atualizar `last_snapshot_url`.

## Decisões

- 🟢 `rtsp_url`, `username` e `password` são write-only na API pública de gestão.
- 🟢 `last_snapshot_url` é denormalizado na câmera para acesso rápido no dashboard.
- 🟢 ROI published exige validação da versão anterior quando já existe published.
- 🟢 Probe RTSP usa processo separado para reduzir risco de deadlock.
- 🟢 Health aceita Edge Token para permitir atualização pelo agente sem usuário.

## Riscos e Lacunas

- 🟡 `test-snapshot` salva caminho temporário local em `last_snapshot_url`, marcado como demo no código.
- 🟡 `CameraSnapshot` e `CameraROIConfig` são unmanaged; divergência de schema pode aparecer como `ProgrammingError`.
- 🟡 `EdgeSnapshotUploadView` usa `get_public_url`, enquanto backend snapshot usa signed URL. A política pública/privada de snapshots precisa estar alinhada.
- 🟡 `CameraSerializer.get_latency_ms` e `get_camera_health` fazem query por objeto, podendo gerar N+1 em listagens grandes.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\core\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\views_snapshot.py`.
