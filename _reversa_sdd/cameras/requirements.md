# cameras - Requirements

## Escopo

- 🟢 Esta unit cobre o app `apps.cameras` do backend `C:\workspace\dale-vision` e os contratos de câmera definidos em `apps.core.models`.
- 🟢 Inclui CRUD de câmeras, permissões por loja, limite de câmeras por plano/trial, ROI versionado, health logs, teste RTSP, snapshot por backend e snapshot enviado pelo edge.
- 🟢 A sincronização de câmeras para o agente é coberta em `stores`, mas depende dos mesmos modelos `Camera` e campos RTSP.

## Requisitos Funcionais

### RF-001 - Gerenciar cadastro de câmera

- 🟢 O backend deve expor `CameraViewSet` em `/api/cameras/cameras/` e `/api/v1/cameras/`.
- 🟢 Listagem deve filtrar por `store_id` quando informado.
- 🟢 Usuários não privilegiados só devem ver câmeras de organizações às quais pertencem.
- 🟢 `retrieve` deve exigir papel de leitura na store.
- 🟢 `create` deve exigir `store_id`/`store`, store existente e papel de gestão.
- 🟢 `create` deve aplicar entitlement/trial antes de persistir.
- 🟢 `perform_create` deve aplicar limite de câmeras ativas por plano.
- 🟢 `perform_update` deve exigir papel de gestão e revalidar limite quando uma câmera inativa é ativada.
- 🟢 `perform_destroy` deve remover snapshots catalogados, health, health logs, ROI configs e a câmera em transação.
- 🟢 Exclusão deve tentar remover arquivos do Supabase Storage quando houver `storage_key`.

### RF-002 - Proteger segredos de câmera em API

- 🟢 `CameraSerializer` deve mascarar `rtsp_url` via `rtsp_url_masked`.
- 🟢 `rtsp_url`, `username` e `password` devem ser write-only no serializer público.
- 🟢 Payloads de erro/log de criação devem sanitizar senha e RTSP.
- 🟡 O endpoint operacional de sincronização para edge retorna RTSP e senha completos e é documentado em `stores`.

### RF-003 - Validar permissões por loja

- 🟢 Papéis de gestão: `owner`, `admin`, `manager`.
- 🟢 Papéis de leitura: `owner`, `admin`, `manager`, `viewer`.
- 🟢 Staff/superuser deve ter acesso privilegiado.
- 🟢 Support grant ativo pode promover viewer para manager.
- 🟢 Sem associação ou grant, queryset deve ficar vazio ou operação deve retornar `PERMISSION_DENIED`.

### RF-004 - Aplicar limite de câmeras por plano

- 🟢 Trial/start deve limitar câmeras ativas a 3.
- 🟢 Pro deve limitar câmeras a 12 e stores a 3.
- 🟢 Growth/enterprise não devem ter limite explícito.
- 🟢 Aliases de plano como `free`, `basic`, `starter`, `paid` e `entreprise` devem ser normalizados.
- 🟢 Staff/superuser devem bypassar limite.
- 🟢 Câmera inativa não deve contar para limite.
- 🟢 Bloqueio deve lançar `PaywallError` e responder `LIMIT_CAMERAS_REACHED` ou `PAYWALL_TRIAL_LIMIT`.

### RF-005 - Configurar ROI versionado

- 🟢 `GET /cameras/{id}/roi/` deve retornar latest, active/published e histórico.
- 🟢 Sem ROI deve retornar versão `0` e `config_json=null`.
- 🟢 `PUT /cameras/{id}/roi/` deve exigir papel de gestão.
- 🟢 `config_json` pode ser lista, convertida para `{"zones": [...]}`.
- 🟢 Status permitido: `draft`, `validated`, `published`, `archived`.
- 🟢 Para publicar, deve existir ao menos uma zona ou linha.
- 🟢 Publicar nova versão quando já há versão publicada exige validação aprovada/validated em `StoreCalibrationRun`.
- 🟢 Publicação incrementa `roi_version`.
- 🟢 Draft/validated/archived preservam `roi_version` atual.
- 🟢 Config deve preencher `metrics_enabled`, `image` e `meta`.
- 🟢 Deve registrar `roi_saved` e completar onboarding `roi_published` quando status é `published`.

### RF-006 - Consultar ROI published para edge/cliente

- 🟢 `GET /cameras/{id}/roi/latest/` deve aceitar usuário autenticado com leitura ou Edge Token da store.
- 🟢 Deve retornar apenas ROI published mais recente.
- 🟢 Se não houver published, deve retornar versão `0` e `config_json=null`.

### RF-007 - Registrar health de câmera

- 🟢 `POST /cameras/{id}/health/` deve aceitar usuário gestor ou Edge Token da store.
- 🟢 Status deve normalizar `error`, `failed`, `down`, `unreachable` para `offline`.
- 🟢 Status desconhecido textual deve retornar `400 status inválido`.
- 🟢 Deve criar `CameraHealthLog` com `checked_at`, `status`, `latency_ms`, `snapshot_url` e `error`.
- 🟢 Deve atualizar `Camera.last_seen_at`, `last_error`, `status`, `updated_at` e `last_snapshot_url` quando enviado.
- 🟢 Status `online` ou `degraded` deve completar onboarding `camera_health_ok`.
- 🟢 Primeira validação ou transição de offline/unknown deve registrar jornada `camera_validated`.

### RF-008 - Testar conexão RTSP

- 🟢 `POST /cameras/{id}/test_connection/` deve exigir papel de gestão.
- 🟢 Câmera sem `rtsp_url` deve retornar `CAMERA_RTSP_MISSING`.
- 🟢 Probe deve usar timeout lógico de 4 segundos e hard timeout de 6 segundos.
- 🟢 Por padrão, probe deve executar em processo separado para evitar bloqueio OpenCV/FFmpeg.
- 🟢 Sem OpenCV, probe deve cair para TCP connect no host/porta RTSP.
- 🟢 Sucesso deve marcar câmera online e criar health log.
- 🟢 Falha deve marcar câmera offline, gravar erro e criar health log.
- 🟢 Timeout deve retornar `status=timeout`, `detail=rtsp_probe_timeout` e `reason=rtsp_timeout`.

### RF-009 - Gerenciar snapshots

- 🟢 `POST /cameras/{id}/snapshot/upload/` deve aceitar multipart `file` ou `snapshot`.
- 🟢 Deve exigir staff/superuser ou papel de gestão.
- 🟢 Storage Supabase não configurado deve retornar `STORAGE_NOT_CONFIGURED`.
- 🟢 Org ausente deve retornar `ORG_NOT_FOUND`.
- 🟢 Conteúdo aceito: `image/jpeg` e `image/png`.
- 🟢 Upload deve usar path `stores/{store_id}/cameras/{camera_id}/snapshots/YYYY/MM/DD/timestamp.ext`.
- 🟢 Deve criar URL assinada por 600 segundos.
- 🟢 Deve criar `CameraSnapshot` quando catálogo disponível.
- 🟢 Deve atualizar `Camera.last_snapshot_url`.
- 🟢 `GET /cameras/{id}/snapshot/` deve retornar URL assinada mais recente, fallback por `last_snapshot_url` ou `SNAPSHOT_NOT_FOUND`.

### RF-010 - Receber snapshot do edge

- 🟢 `POST /api/edge/cameras/{camera_id}/snapshot/` deve autenticar Edge Token.
- 🟢 A câmera deve pertencer à store do token.
- 🟢 Deve exigir arquivo multipart `snapshot`.
- 🟢 Deve subir arquivo para Supabase e atualizar `Camera.last_snapshot_url`.
- 🟢 Falhas de storage devem retornar erro explícito.

## Requisitos Não Funcionais

- 🟢 Segurança: RTSP/senha não devem aparecer em serializer público nem logs.
- 🟢 Confiabilidade: probe RTSP deve ter hard timeout para não prender worker.
- 🟢 Operabilidade: health e snapshot devem atualizar campos denormalizados para dashboard rápido.
- 🟢 Compatibilidade: endpoints `test_connection` e `test-connection` coexistem.
- 🟢 Auditoria: ações de staff em câmera/ROI devem criar `AuditLog`.

## Critérios de Aceitação

- 🟢 Dado usuário manager, quando cria câmera válida dentro do limite, então recebe `201` e jornada `camera_added` é registrada.
- 🟢 Dado trial com 3 câmeras ativas, quando tenta ativar/criar outra câmera ativa, então recebe `LIMIT_CAMERAS_REACHED`.
- 🟢 Dado ROI published existente sem validação, quando tenta publicar nova versão, então recebe `ROI_VALIDATION_REQUIRED`.
- 🟢 Dado Edge Token válido, quando envia health online, então câmera fica online e onboarding `camera_health_ok` é completado.
- 🟢 Dado RTSP que trava, quando testa conexão, então resposta retorna timeout sem bloquear indefinidamente.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\serializers.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\permissions.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\limits.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\roi.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\services.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\views_snapshot.py`.
