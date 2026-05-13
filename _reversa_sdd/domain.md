# Dominio - DaleVision

Gerado em: 2026-05-06T20:09:09.572994Z

## Glossario

| Termo | Definicao | Confianca |
|---|---|---|
| DaleVision | Plataforma SaaS de operacao/visao para varejo, com agente local, backend cloud e frontend web. | 🟡 INFERIDO |
| Edge Agent | Executavel/servico Windows instalado no computador do cliente para integrar NVR/cameras com a cloud. | 🟢 CONFIRMADO |
| Store | Loja/unidade operacional monitorada. | 🟢 CONFIRMADO |
| Organization | Tenant/organizacao dona de lojas e usuarios. | 🟢 CONFIRMADO |
| Edge Token | Credencial por loja usada pelo agente local para autenticar endpoints /api/edge. | 🟢 CONFIRMADO |
| Activation Token | Token temporario e single-use usado para ativar um device edge. | 🟢 CONFIRMADO |
| Edge Device | Registro backend da instalacao local, identificado por device_key e status. | 🟢 CONFIRMADO |
| Camera Health | Sinal periodico por camera com status, latencia, erro e snapshot. | 🟢 CONFIRMADO |
| ROI | Configuracao de regioes/linhas para interpretar metricas de visao por camera. | 🟢 CONFIRMADO |
| Copilot | Modulo de insights/acoes/briefings e value ledger operacional. | 🟢 CONFIRMADO |
| Value Ledger | Agregado diario de valor recuperado/em risco e acoes executadas. | 🟢 CONFIRMADO |
| Trial | Estado comercial que permite uso limitado ate expirar ou converter para assinatura. | 🟢 CONFIRMADO |
| Canary | Canal de release/update usado para rollout controlado. | 🟢 CONFIRMADO |

## Regras de negocio implicitas

1. 🟢 CONFIRMADO - O protocolo edge deve preservar compatibilidade. Evidencia: commits de hardening, endpoints legados /api/edge/cameras/ e /api/edge/stores/{store_id}/cameras/, e instrucoes locais de nao quebrar heartbeat/camera health.
2. 🟢 CONFIRMADO - Edge token explicito tem precedencia sobre Authorization JWT quando X-EDGE-TOKEN esta presente. Evidencia: apps/edge/auth.py.
3. 🟢 CONFIRMADO - Staff/superuser bypassam trial/paywall e RBAC de loja. Evidencia: backend/middleware.py, backend/utils/entitlements.py e apps/cameras/permissions.py.
4. 🟢 CONFIRMADO - Viewer pode ganhar permissao operacional temporaria via SupportAccessGrant, elevando acesso a manager enquanto o grant estiver ativo. Evidencia: apps/cameras/permissions.py.
5. 🟢 CONFIRMADO - Activation token e single-use e deve virar edge_token/device identity; apos sucesso, activation_token e removido da config local. Evidencia: StoreActivationTokenView e bootstrap_activation.
6. 🟢 CONFIRMADO - Loja bloqueada ou blocked_reason edge_disabled/subscription_inactive/store_suspended/security_revoked deve impedir acesso edge. Evidencia: apps/edge/auth.py.
7. 🟢 CONFIRMADO - Trial expirado retorna HTTP 402 com code TRIAL_EXPIRED, exceto endpoints whitelisted e usuarios internos. Evidencia: TrialEnforcementMiddleware.
8. 🟢 CONFIRMADO - Status edge/camera usa thresholds: online recente, degraded stale, offline expirado; camera health aceita fallback operacional por sinais recentes. Evidencia: apps/stores/views_edge_status.py.
9. 🟢 CONFIRMADO - Camera readiness/onboarding nao deve concluir sem ROI completo. Evidencia: commit d7aca4b e fluxo de onboarding/cameras.
10. 🟢 CONFIRMADO - Snapshot deve ser best-effort: usa OpenCV quando possivel, cai para ffmpeg, e se ambos falham segue sem snapshot com log claro. Evidencia: AGENTS.md e src/dalevision_edge_agent/cameras.py.
11. 🟢 CONFIRMADO - Update do edge usa rollout window, min-supported, lock, idempotency key e health gate com rollback. Evidencia: commits a05f152, 2bf37c4, views_update.py e update.py.
12. 🟢 CONFIRMADO - Eventos edge e vision devem ser idempotentes para absorver retries. Evidencia: compute_receipt_id, event_receipts e commits sobre idempotency_key.
13. 🟢 CONFIRMADO - Contrato de visao exige camera_id, ts, metric_type, ownership e roi_entity_id para eventos vision.*. Evidencia: apps/edge/views.py.
14. 🟡 INFERIDO - O modelo operacional assume cameras com papeis entrada, balcao e salao, usados para footfall, fila/conversao e ocupacao/engajamento. Evidencia: vision worker/store_runner.
15. 🟡 INFERIDO - O produto prioriza onboarding de campo sem suporte tecnico: wizard, local setup API, diagnosticos compartilhaveis e mensagens para leigo aparecem em commits e docs.

## Eventos de negocio monitorados

- edge_heartbeat
- camera_health
- vision.*
- retail.event.v1
- store_status_changed
- camera_status_changed
- edge_update_started / healthy / failed / rolled_back
- trial_expired_shown / trial_expired_blocked
- onboarding eventos e setup-state
- action outcomes e WhatsApp dispatch

## Lacunas

- 🔴 LACUNA - Confirmar com operacao se roles viewer com support grant devem sempre equivaler a manager ou apenas em endpoints especificos.
- 🔴 LACUNA - Confirmar o SLA real de online/degraded/offline por ambiente piloto versus producao.
- 🔴 LACUNA - Confirmar se assinatura ativa deve desbloquear automaticamente lojas com status blocked/trial_expired.
