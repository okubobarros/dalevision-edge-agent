# stores - Requirements

## Escopo

- 🟢 Esta unit cobre o app `apps.stores` do backend `C:\workspace\dale-vision`, com foco nas funcionalidades que orquestram lojas, ativação do edge, status operacional, credenciais, sincronização de câmeras, release/update e rollout.
- 🟢 `apps.stores.models` não define modelos próprios; a fonte de dados de lojas vem de `apps.core.models`, enquanto entidades edge vêm de `apps.edge.models`.
- 🟢 Endpoints do app são montados em `backend/urls.py` sob `/api/v1/`.
- 🟢 Esta unit complementa `edge`, `edge-agent-activation`, `edge-agent-update-installation` e `cameras`.

## Requisitos Funcionais

### RF-001 - Emitir token de ativação single-use

- 🟢 Usuário autenticado com papel de gestão da loja deve conseguir chamar `/api/v1/stores/{store_id}/activation-token/`.
- 🟢 O backend deve validar existência da store.
- 🟢 Deve validar papel por `require_store_role` com `ALLOWED_MANAGE_ROLES`.
- 🟢 Deve desativar tokens de ativação ativos anteriores da loja.
- 🟢 Deve gerar token URL-safe com 32+ caracteres.
- 🟢 Deve salvar apenas hash SHA-256 em `ActivationToken.token_hash` e hint final.
- 🟢 Token deve expirar em `EDGE_ACTIVATION_TOKEN_TTL_SECONDS` ou 24h.
- 🟢 Resposta deve incluir `activation_token`, `expires_at`, `expires_in_seconds`, `single_use=true` e método `store_activation_token_issue`.

### RF-002 - Ativar device edge

- 🟢 Endpoint público `/api/v1/stores/activate/` deve aceitar `token` ou `activation_token`.
- 🟢 Deve aceitar `device_key` ou `agent_id`, `installed_version` ou `version`, e `update_channel`.
- 🟢 Token ausente deve retornar `activation_token_required`.
- 🟢 Token inválido deve retornar `activation_token_invalid`.
- 🟢 Token já usado deve retornar `activation_token_already_used`.
- 🟢 Token inativo/expirado deve retornar erro específico.
- 🟢 Store edge-disabled deve retornar `activation_store_disabled`.
- 🟢 Device key ausente deve ser gerado como `edge-<hex>`.
- 🟢 Canal inválido deve normalizar para `stable`.
- 🟢 Device key associado a outra loja deve retornar `device_key_conflict`.
- 🟢 Device retired deve retornar `device_retired`.
- 🟢 Ativação bem-sucedida deve criar/atualizar `EdgeDevice`, marcar activation token usado/inativo e emitir novo `EdgeToken` ativo para a loja.

### RF-003 - Gerenciar credenciais edge da loja

- 🟢 `StoreViewSet.edge_token`, `edge_credentials` e `edge_setup` devem emitir ou reutilizar token edge ativo.
- 🟢 Acesso deve exigir owner/admin/manager conforme helpers de permissão.
- 🟢 `edge_credentials` e `edge_setup` devem retornar `cloud_base_url` e `agent_id_default`/`agent_id_suggested`.
- 🟢 `edge-token/rotate` deve desativar tokens ativos anteriores e emitir token novo.
- 🟢 `edge-token-hint` só deve funcionar com debug habilitado e staff/superuser.

### RF-004 - Baixar instalador do agente

- 🟢 `/api/v1/stores/{store_id}/download-agent/` deve gerar URL assinada temporária.
- 🟢 Link deve usar `EDGE_DOWNLOAD_LINK_TTL_SECONDS` ou 900 segundos.
- 🟢 Payload assinado deve conter `store_id`, `setup_url`, `filename` e `onboarding_ref`.
- 🟢 `/download-agent/file/` deve validar assinatura, expiração e store_id.
- 🟢 Download final redireciona para `setup_url`.
- 🟢 `setup_url` deve vir de `EDGE_WINDOWS_SETUP_URL`, release stable ativa ou `EDGE_RELEASE_STABLE_URL`.

### RF-005 - Controlar acesso edge da loja

- 🟢 `/edge-access/` GET deve retornar `status`, `blocked_reason` e `edge_enabled`.
- 🟢 POST suporta apenas desabilitar edge com `enabled=false`.
- 🟢 Desabilitar deve atualizar store, desativar EdgeTokens, desativar ActivationTokens e marcar EdgeDevices como retired.
- 🟢 Reativação por este endpoint não é suportada nesta fase.

### RF-006 - Revogar device edge

- 🟢 `/edge-devices/revoke/` deve exigir `device_key`.
- 🟢 Deve validar papel de gestão.
- 🟢 Deve marcar device como `retired`.
- 🟢 Device inexistente retorna `device_not_found`.

### RF-007 - Consultar status edge da loja

- 🟢 `/edge-status/` deve exigir usuário autenticado com papel de leitura.
- 🟢 Status deve combinar store, cameras, `CameraHealthLog`, `event_receipts` e `EdgeEventMinuteStats`.
- 🟢 Thresholds: online 120s, degraded 300s, edge online 180s, health recente 600s e camera sync recente 300s.
- 🟢 Payload deve manter contrato estável com `ok`, `online`, `connectivity_status`, `pipeline_status`, `store_status`, contadores de câmeras, `last_heartbeat_at`, `agent_id`, `version` e diagnósticos.
- 🟢 Se online, deve completar onboarding step `edge_connected`.

### RF-008 - Consultar status de ativação

- 🟢 `/activation-status/` deve exigir papel de leitura.
- 🟢 `StoreActivationStatusService` deve derivar `technical_status`, `value_status`, `activation_state`, `next_action`, bloqueios, device, câmeras, versão alvo e funil de onboarding.
- 🟢 Estados de ativação incluem `pending_download`, `pending_install`, `agent_seen`, `ready_for_cameras`, `activation_completed` e `activation_failed`.

### RF-009 - Sincronizar câmeras com o agente

- 🟢 `StoreViewSet.cameras` GET deve aceitar Edge Token explícito ou usuário autenticado.
- 🟢 Com Edge Token válido, deve retornar apenas câmeras ativas em formato operacional para o agente.
- 🟢 Deve montar RTSP a partir de `rtsp_url` ou fallback `ip/username/password`.
- 🟢 Deve incluir `rtsp_url_masked` além de `rtsp_url`.
- 🟢 Deve registrar `edge_camera_sync_pull` em `EdgeEventMinuteStats`.
- 🟢 Se Edge Token explícito for inválido, não deve cair silenciosamente para sessão de usuário.

### RF-010 - Gerenciar release edge

- 🟢 `/edge/releases/latest/` deve ser público e retornar release ativa por canal `stable` ou `canary`.
- 🟢 Canal inválido deve cair para `stable`.
- 🟢 Se não houver release ativa, deve usar fallback por settings `EDGE_RELEASE_*`.
- 🟢 `/edge/releases/` deve exigir staff/superuser.
- 🟢 Criar/atualizar release deve validar versão e URL.
- 🟢 Release ativa deve desativar releases anteriores do mesmo canal.

### RF-011 - Gerenciar policy/update por loja

- 🟢 `/edge-update-policy/` GET deve retornar policy ativa serializada.
- 🟢 PUT deve exigir papel de gestão e validar `target_version`, `package.url` e `package.sha256`.
- 🟢 Canal deve ser `stable` ou `canary`.
- 🟢 Defaults de rollout e health gate devem ser preservados quando ausentes.
- 🟢 `/edge/update/` deve criar/atualizar policy a partir da release ativa e registrar `edge_update_requested`.
- 🟢 Se device já estiver na versão alvo e `force_update=false`, deve retornar `already_up_to_date`.

### RF-012 - Observar update e rollout

- 🟢 `/edge-update-status/` deve calcular `version_gap`, `latest_update_event` e `rollout_health`.
- 🟢 `/edge-update-events/` deve listar eventos com filtros `status`, `agent_id` e `limit`.
- 🟢 `/edge-update-attempts/` deve agrupar eventos por tentativa lógica.
- 🟢 `/edge-update-runbook/` deve retornar runbook por `reason_code` ou pela falha mais recente.
- 🟢 `/edge-update-runbook/opened/` deve registrar evento `runbook_opened`.
- 🟢 Sumários de rede devem calcular saúde de rollout, métricas de tentativa, lojas críticas e decisão GO/NO-GO.

### RF-013 - Canary rollout

- 🟢 Endpoints canary devem exigir staff/superuser.
- 🟢 Batch tag deve selecionar percentual de lojas active/trial e aplicar release canary.
- 🟢 Health canary deve sumarizar lojas por `healthy`, `failed`, `in_progress` e `no_data`.
- 🟢 Rollback canary deve aplicar release stable sobre policies canary e registrar `canary_rollback_requested`.

## Requisitos Não Funcionais

- 🟢 Segurança: activation token e edge token devem ser emitidos como segredo; acesso deve ser restrito por papel.
- 🟢 Operabilidade: status edge deve retornar payload estável mesmo em falha parcial.
- 🟢 Compatibilidade: endpoints legados do `StoreViewSet` coexistem com views novas de activation/update.
- 🟢 Observabilidade: update management deve registrar eventos e runbooks acionáveis.
- 🟢 Privacidade: RTSP mascarado é retornado junto do RTSP operacional para debug; logs não devem expor segredos.

## Critérios de Aceitação

- 🟢 Dado gerente da loja, quando pedir activation token, então recebe token single-use com expiração.
- 🟢 Dado agente com activation token válido, quando ativar device, então recebe `edge_token`, `device_key`, `store_id` e device fica ativo.
- 🟢 Dado edge token válido, quando chamar câmeras da loja, então recebe apenas câmeras ativas com RTSP resolvido.
- 🟢 Dado loja com heartbeat recente e câmeras online, quando consultar status, então `store_status=online` e onboarding `edge_connected` é completado.
- 🟢 Dado release ativa e SHA configurado, quando disparar update, então policy é atualizada e evento `edge_update_requested` é criado.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_registry.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_management.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_attempts.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_network.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_canary.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views.py`.
