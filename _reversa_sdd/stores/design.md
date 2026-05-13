# stores - Design

## Visão Geral

- 🟢 `apps.stores` atua como camada operacional por loja: provisiona edge, expõe credenciais, entrega instalador, consulta status, gerencia update e fornece contratos para frontend/dashboard.
- 🟢 O app não tem models próprios; usa `apps.core.models.Store/Camera/CameraHealthLog/OnboardingProgress` e `apps.edge.models`.
- 🟢 O desenho separa views novas (`views_activation`, `views_edge_status`, `views_edge_update_*`) de ações legadas no `StoreViewSet`.

## Componentes

### Ativação

- 🟢 `StoreActivationTokenView` emite token temporário single-use.
- 🟢 `StoreActivateView` valida token e cria/reativa `EdgeDevice`.
- 🟢 `activation_registry.py` centraliza geração, hash, ativação, emissão de `EdgeToken`, revogação e touch de device.

### Download

- 🟢 `StoreDownloadAgentView` cria link assinado com `TimestampSigner`.
- 🟢 `StoreDownloadAgentFileView` valida token e redireciona para a URL do instalador.
- 🟢 URL de setup prioriza setting explícito, release stable ativa e fallback de settings.

### Status

- 🟢 `compute_store_edge_status_snapshot` combina dados de store, câmeras, health logs, receipts e minute stats.
- 🟢 `StoreActivationStatusService` deriva status técnico, status de valor e próxima ação de onboarding.

### Câmeras para Edge

- 🟢 `StoreViewSet.cameras` usa `EdgeAwareJWTAuthentication` e `TokenAuthentication`.
- 🟢 Com Edge Token válido, retorna payload operacional e registra pull.
- 🟢 Com usuário autenticado, retorna serialização DRF comum.

### Update/Release

- 🟢 `EdgeReleaseLatestView` e `EdgeReleaseManagementView` gerenciam releases por canal.
- 🟢 `StoreEdgeUpdatePolicyManagementView` gerencia policy por loja.
- 🟢 `StoreEdgeUpdateTriggerView` transforma release ativa em policy e registra solicitação.
- 🟢 Views de status, eventos, attempts, runbook e network summary dão observabilidade de rollout.

### Canary

- 🟢 `CanaryBatchTagView` aplica release canary em amostra percentual de lojas.
- 🟢 `CanaryHealthView` sumariza health das policies canary.
- 🟢 `CanaryRollbackView` reverte policies canary para release stable.

## Fluxos Principais

### Provisionamento moderno

1. 🟢 Usuário gestor solicita activation token.
2. 🟢 Backend invalida tokens anteriores e cria token novo com hash.
3. 🟢 Agente/instalador chama `/stores/activate/`.
4. 🟢 Backend valida token, store e device.
5. 🟢 Backend cria/atualiza `EdgeDevice`.
6. 🟢 Backend marca token usado e emite `EdgeToken`.
7. 🟢 Agente passa a usar `EdgeToken` nas chamadas edge.

### Status operacional

1. 🟢 Frontend consulta `/edge-status/`.
2. 🟢 Backend valida acesso.
3. 🟢 Snapshot lê câmeras ativas, latest health, latest receipt heartbeat e stats.
4. 🟢 Classifica câmera e loja por idade/health.
5. 🟢 Retorna contrato estável mesmo se houver fallback.
6. 🟢 Se online, completa onboarding `edge_connected`.

### Update por dashboard

1. 🟢 Usuário gestor chama `/edge/update/`.
2. 🟢 Backend seleciona device/policy/release/canal.
3. 🟢 Se release ou SHA ausente, retorna conflito acionável.
4. 🟢 Backend cria/atualiza `EdgeUpdatePolicy`.
5. 🟢 Se já atualizado e sem force, retorna `already_up_to_date`.
6. 🟢 Caso contrário, registra `edge_update_requested`.
7. 🟢 Agente consome policy no endpoint de `apps.edge`.

## Decisões

- 🟢 Tokens de ativação são single-use para reduzir risco de reutilização.
- 🟢 Só desabilitar edge é suportado em `edge-access`; reabilitação exige outro fluxo.
- 🟢 Status edge é tolerante a schema drift e indisponibilidade parcial, retornando fallback.
- 🟢 Canary é restrito a staff/superuser.
- 🟢 Release latest é público para permitir bootstrap/download.

## Riscos e Lacunas

- 🟡 `EdgeToken.token_plaintext` é persistido para permitir exibição/reuso de credenciais; exige proteção forte de acesso.
- 🟡 `StoreViewSet.edge_token` retorna campo `token`; `edge_credentials` retorna `edge_token`; contratos coexistem.
- 🟡 `StoreEdgeAccessControlView` não implementa reenable, então recuperação de store bloqueada depende de fluxo externo.
- 🟡 Status edge depende de SQL direto em `event_receipts`, tabela fora do app stores.
- 🟡 `StoreActivationStatusService` usa fallback `v1.0.22` quando não há release stable.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\urls.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_registry.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views.py`.
