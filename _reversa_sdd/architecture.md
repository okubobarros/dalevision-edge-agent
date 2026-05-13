# Arquitetura DaleVision

Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

## Escopo

🟢 CONFIRMADO: O DaleVision depende de dois repositorios analisados em conjunto.

| Repositorio | Papel | Evidencia |
|---|---|---|
| `C:\workspace\dalevision-edge-agent` | Agente Windows instalado no cliente. Coleta heartbeat, camera health, snapshots, diagnosticos, eventos de visao e auto-update. | `src/dalevision_edge_agent/*`, `tests/test_heartbeat_state.py`, scripts de release/install-service. |
| `C:\workspace\dale-vision` | Backend Django/DRF e frontend React/Vite. | `backend/urls.py`, `backend/settings.py`, `apps/*`, `frontend/*`, `vercel.json`. |

## Visao Executiva

🟢 CONFIRMADO: A arquitetura e hibrida cloud + edge. O frontend web roda em Vercel, o backend Django/DRF roda em Render, o banco principal e Postgres via `DATABASE_URL`, e o agente Windows roda dentro da rede do cliente para acessar NVR/cameras via RTSP/HTTP.

🟢 CONFIRMADO: O contrato edge atual inclui ativacao, `heartbeat`, `camera_health`, eventos de visao/retail e update report. O agente usa `STORE_ID`, `AGENT_ID`, `EDGE_TOKEN` e `CLOUD_BASE_URL`; o backend valida token hash, loja e bloqueios operacionais.

🟡 INFERIDO: O produto privilegia robustez operacional sobre consistencia estrita em tempo real: snapshots sao best-effort, OpenCV e opcional, ffmpeg e fallback, eventos sao idempotentes por `event_id`, status edge usa buckets/minutos e trial/paywall preserva whitelists para edge.

## Containers

| Container | Tecnologia | Responsabilidade | Confianca |
|---|---|---|---|
| Frontend SPA | React + Vite + TypeScript, Vercel | Onboarding, dashboards, cameras, alertas, billing, copilot/admin. | 🟢 CONFIRMADO |
| Backend API | Django + DRF, Render | API REST, RBAC, ingest edge, billing, analytics, copilot, stores. | 🟢 CONFIRMADO |
| Postgres | `DATABASE_URL` | Persistencia relacional. | 🟢 CONFIRMADO |
| Redis | `REDIS_URL`/`REDIS_TLS_URL` | Cache/coordernacao quando configurado. | 🟢 CONFIRMADO como dependencia |
| Supabase | Auth/JWT/Storage | Identidade e armazenamento. | 🟢 CONFIRMADO |
| Edge Agent Windows | Python + PyInstaller | Coleta local, diagnostico, snapshot, heartbeat e update. | 🟢 CONFIRMADO |
| NVR/Cameras | RTSP/HTTP local | Fonte de video e health. | 🟢 CONFIRMADO |
| LLM/Google/Meta | HTTPS | Copilot, relatorios e mensageria inferida. | 🟡 INFERIDO |

## Componentes Backend

| App | Responsabilidade | Rotas/Dados | Confianca |
|---|---|---|---|
| `accounts` | Setup state, autenticacao e onboarding. | `/api/accounts/`, `/api/v1/accounts/`, setup-state. | 🟢 CONFIRMADO |
| `core` | Dominio central. | Organization, Store, Camera, DetectionEvent, Subscription, AuditLog. | 🟢 CONFIRMADO |
| `stores` | Lojas, ativacao, download agent, edge status, releases, grants. | ActivationToken, EdgeRelease, StoreEdgeStatus. | 🟢 CONFIRMADO |
| `edge` | Auth edge, ingest eventos, stats por minuto, update events. | `/api/edge/`, `/api/v1/ingest/events/`. | 🟢 CONFIRMADO |
| `cameras` | Camera CRUD/config, ROI, health, snapshots e permissoes. | CameraROIConfig, CameraHealth, CameraSnapshot. | 🟢 CONFIRMADO |
| `analytics` | Metricas, onboarding e agent events. | StoreDailyMetrics, OnboardingEvent, AgentEvent. | 🟢 CONFIRMADO |
| `billing` | Trial, planos, assinaturas e entitlements. | TrialEnforcementMiddleware, Subscription/BillingCustomer. | 🟢 CONFIRMADO |
| `copilot` | Contexto, insights, conversas, reports, outcomes. | Copilot* models, ActionOutcome, ValueLedgerDaily. | 🟢 CONFIRMADO |

## Componentes Edge

| Componente | Responsabilidade | Confianca |
|---|---|---|
| `ConfigManager` | Carrega/salva env e estado local. | 🟢 CONFIRMADO |
| `StateMachine` | Estados `NEEDS_ACTIVATION`, `ACTIVE`, `DEGRADED`, `ERROR`. | 🟢 CONFIRMADO |
| `ActivationClient` | Troca activation token por credenciais persistentes. | 🟢 CONFIRMADO |
| Heartbeat loop | Envia heartbeat e muda estado por sucesso/rede/auth. | 🟢 CONFIRMADO |
| Camera health | Verifica cameras/NVR e publica saude. | 🟢 CONFIRMADO |
| Snapshot | OpenCV opcional, ffmpeg fallback, falha clara sem interromper agente. | 🟢 CONFIRMADO |
| Doctor | Gera `diagnostics.json` e `diagnostics.txt` para suporte remoto. | 🟢 CONFIRMADO |
| Auto-update | Release policy, health gate, rollback e `update.log`. | 🟢 CONFIRMADO |

## Fluxos Criticos

### Ativacao

1. Backend gera activation token por loja.
2. Agente recebe token, `CLOUD_BASE_URL`, `STORE_ID` e `AGENT_ID`.
3. Backend valida TTL e uso unico.
4. Agente persiste `EDGE_TOKEN` e remove activation token apos sucesso.
5. Heartbeats passam a usar `X-EDGE-TOKEN` ou Authorization, com precedencia de `X-EDGE-TOKEN`.

### Heartbeat e Camera Health

1. Agente coleta estado local, cameras e versao.
2. Backend valida token hash, loja ativa e bloqueios (`edge_disabled`, `subscription_inactive`, `store_suspended`, `security_revoked`).
3. Backend grava buckets por minuto e calcula online/degraded/offline.
4. Frontend consulta status para operacao e suporte.

### Eventos de Visao

1. Edge/vision normaliza `vision.*` e `retail.event.v1`.
2. Backend ingere eventos edge.
3. Idempotencia por `event_id` evita duplicidade.
4. Dados alimentam analytics, copilot, alertas e dashboards.

### Trial/Entitlements

1. Middleware bloqueia APIs com trial expirado usando `402 TRIAL_EXPIRED`.
2. Rotas edge, health, setup-state, billing plans, docs e reports sao whitelisted.
3. Staff tem bypass; schema drift e audit log sao tratados defensivamente.

## Permissoes

🟢 CONFIRMADO: Roles `owner`, `admin`, `manager`, `viewer`. Cameras permitem leitura para viewer e gerenciamento para owner/admin/manager. Staff/superuser tem privilegio. `SupportAccessGrant` pode elevar viewer ou usuario sem membership para manager.

🔴 LACUNA: Validar todos os endpoints extensos de `stores/views.py` e ViewSets longos para fechar a matriz RBAC sem excecoes.

## Dividas Tecnicas

| Severidade | Item | Impacto |
|---|---|---|
| HIGH | Views extensas e responsabilidades misturadas. | Dificulta auditoria RBAC, testes e evolucao. |
| HIGH | Contratos edge/vision precisam regressao forte. | Pequena quebra pode derrubar agentes instalados. |
| HIGH | `CORS_ALLOW_ALL_ORIGINS = True`. | Risco de exposicao se auth/CSRF forem mal configurados. |
| MEDIUM | Auth hibrida Supabase/Knox/EdgeToken. | Maior superficie de inconsistencias. |
| MEDIUM | Schema drift tratado no codigo. | Banco precisa contrato operacional mais explicito. |
| MEDIUM | Instalador/update Windows complexo. | Exige testes em VM Windows e logs claros. |
| MEDIUM | Rotas `/api/` e `/api/v1/` coexistem. | Aumenta matriz de compatibilidade frontend/backend. |

## Lacunas

| Lacuna | Motivo |
|---|---|
| SLA exato online/degraded/offline. | Thresholds existem, mas podem variar por config/prod. |
| RBAC completa de todos os endpoints. | Views extensas podem conter excecoes. |
| Provedor Postgres efetivo. | `DATABASE_URL` confirma Postgres; envs indicam Supabase/Neon, mas deploy real nao foi acessado. |
| Fluxos WhatsApp/Meta e Google. | Dependencias/envs indicam integracoes; fluxo completo requer leitura dirigida. |

_Gerado pelo Reversa Architect em 2026-05-06T20:31:14.659066+00:00._
