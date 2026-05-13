# Analise de Codigo - DaleVision

Gerado em: 2026-05-06T19:58:05.001354Z

Escopo: C:\workspace\dalevision-edge-agent e C:\workspace\dale-vision.
Nivel: detalhado. Organizacao das specs: hybrid.

## Resumo executivo

CONFIRMADO - O sistema e composto por agente edge Windows/local, backend Django/DRF e frontend React/Vite. O contrato operacional mais sensivel cruza edge-agent -> apps.edge/apps.cameras/apps.stores -> frontend de onboarding/dashboard.

CONFIRMADO - O protocolo atual preserva compatibilidade por endpoints legados e novos: heartbeat usa evento edge_heartbeat; camera health usa /api/edge/events/ e endpoints de camera; update usa /api/edge/update-policy/ e /api/edge/update-report/; camera list aceita /api/edge/cameras/ e /api/edge/stores/{store_id}/cameras/.

CONFIRMADO - A arquitetura de dados backend usa modelos Django majoritariamente unmanaged espelhando tabelas existentes, com excecoes gerenciadas recentes como LGPD, edge devices/releases/update events, camera ROI/snapshot e copilot.

INFERIDO - O produto opera como SaaS multi-loja para varejo, com onboarding frictionless, edge agent local, pipelines de visao/retail events, dashboards de operacao e Copilot para acao/ROI.

## Fluxo macro ponta-a-ponta

1. Usuario acessa frontend, autentica via Supabase e sincroniza sessao com backend.
2. Usuario cria loja/onboarding e solicita configuracao de edge.
3. Backend gera activation token, edge token e download agent para loja.
4. Agente local ativa device, grava config local e passa a enviar heartbeat/camera health.
5. Backend autentica token edge, atualiza last_seen/status e deduplica eventos por receipt/idempotency.
6. Agente captura snapshot e/ou executa pipeline vision; backend persiste eventos canonicos, metricas e agregados.
7. Frontend consulta status, cameras, ROI, relatorios, Copilot e update management.
8. Politicas de update podem ser configuradas no backend; agente aplica pacote com health gate e reporta resultado.

## Modulos analisados

| Modulo | Proposito | Arquivos principais | Complexidade |
|---|---|---|---|
| edge-agent-runtime | Orquestra CLI, logging, setup API, heartbeat, camera health, watchdog, vision proxy e auto-update. | src/dalevision_edge_agent/main.py; env.py; setup_api.py | alta |
| edge-agent-activation | Bootstrap via activation token, agent_config e hidratacao segura de runtime. | activation.py; env.py | alta |
| edge-agent-heartbeat-camera-health | Publica presenca, camera health, snapshot e eventos de saude no backend. | heartbeat.py; heartbeat_client.py; cameras.py | alta |
| edge-agent-diagnostics | Doctor local, validacao rede/NVR/API/snapshot/config e pacote de suporte. | diagnostics.py; onboarding_error_codes.py; onboarding_readiness.py | alta |
| edge-agent-vision | Processa RTSP/snapshot, ROI/linha/zona, deteccao e metricas canonicas. | vision/worker.py; geometry.py; outbox.py | alta |
| edge-agent-update-installation | Instalacao Windows, policy update, checksum, health gate e rollback. | update.py; scripts/*.ps1 | alta |
| accounts | Auth Supabase/Knox, bootstrap, usuario atual e setup state. | apps/accounts/views.py; serializers.py; auth_supabase.py | alta |
| analytics | Eventos de onboarding/agente e metricas diarias. | apps/analytics/models.py; views.py | alta |
| billing | Planos, trial/paywall e limites. | apps/billing/views.py; utils.py | alta |
| cameras | CRUD cameras, ROI, health, snapshots e RTSP probe. | apps/cameras/views.py; models.py; services.py | alta |
| copilot | Insights, briefing, conversas, feed, actions e value ledger. | apps/copilot/models.py; views.py; services/*.py | alta |
| core | Modelos centrais, onboarding, relatorios, PDV, storage e calibracao. | apps/core/models.py; views_onboarding.py; views_report.py | alta |
| edge | Ingestao edge, auth token, devices/releases/update/snapshot/vision metrics. | apps/edge/views.py; views_update.py; vision_metrics.py | alta |
| stores | Lojas, funcionarios, ativacao edge, status, updates, canary e suporte. | apps/stores/views*.py; urls.py | alta |
| frontend-auth-onboarding | Login, sessao, rota pos-login, onboarding e setup edge. | auth.ts; Onboarding.tsx; EdgeSetupModal.tsx | alta |
| frontend-dashboard-operations | Dashboard, operacoes, stores, KPIs e status edge. | Dashboard.tsx; Stores.tsx; stores.ts; me.ts | alta |
| frontend-cameras-alerts | Cameras, ROI, readiness local, alert rules e eventos. | Cameras.tsx; CameraRoiEditor.tsx; alerts.ts | alta |
| frontend-copilot-reports-admin | Copilot, intelligence feed, reports, admin e resiliencia API. | Copilot.tsx; api.ts; AdminControlTower.tsx | alta |

## Algoritmos e regras relevantes

### Idempotencia de eventos edge

CONFIRMADO - O agente gera idempotency key/receipt para heartbeat usando bucket de 1 minuto. O backend recalcula ou aceita receipt para deduplicar eventos. Vision events usam bucket minuto; retail events usam bucket de 5 minutos para absorver retries.

### Autenticacao edge

CONFIRMADO - O agente envia X-EDGE-TOKEN e Authorization: Bearer. O backend valida token contra loja e retorna codigos curtos quando invalido. O agente limita falhas consecutivas de auth e pode sair com EXIT_AUTH_ERROR.

### Health gate de update

CONFIRMADO - Update policy contem janela local, versao minima suportada, pacote, sha256 e health gate. O agente baixa, valida checksum, aplica e grava pending payload. No boot pos-update verifica heartbeat/camera health dentro de prazos e reporta rollback/falha.

### Camera health e snapshot

CONFIRMADO - O agente tenta RTSP/OpenCV/ffmpeg, registra latencia/status/erro e faz upload de snapshot para backend. Backend salva snapshot em Supabase Storage e atualiza last_snapshot_url da camera.

### Vision metrics

CONFIRMADO - Backend valida contrato de eventos vision.*, cria evento canonico, persiste receipt/raw/atomic event e aplica projecoes especificas: traffic, crossing, queue state, checkout proxy e zone occupancy.

### Frontend API resilience

CONFIRMADO - Cliente Axios aplica timeouts por categoria, retry para GET 502/503/504/ERR_NETWORK, retry de timeout para GET, refresh de sessao Supabase em 401, eventos de trial expirado e suppress de toast em endpoints best-effort.

## Lacunas para proximos agentes

- LACUNA - Confirmar em execucao real quais tabelas sao Supabase/Neon managed e quais sao apenas legado local.
- LACUNA - Confirmar contratos finais de todos eventos vision.* contra docs/contracts e testes de ingestao.
- LACUNA - Confirmar politica atual de deploy Render/Vercel por ambiente e variaveis reais sem expor segredos.
