# Índice Executivo DaleVision SDD

## Escopo

🟢 CONFIRMADO: Esta documentação cobre o produto DaleVision como um sistema único formado por dois repositórios:

| Repositório | Papel |
|---|---|
| `C:\workspace\dalevision-edge-agent` | Executável/agente local Windows instalado no computador dos clientes. |
| `C:\workspace\dale-vision` | Backend Django/DRF, frontend React/Vite e infraestrutura cloud do produto. |

## Como Navegar

Use este índice como ponto de entrada. Não é necessário revisar todos os arquivos um por um.

1. Leia os artefatos globais para visão completa.
2. Revise primeiro as units críticas.
3. Use as units de apoio apenas quando precisar de detalhe daquele domínio.
4. Consulte `questions.md` onde houver lacunas vermelhas.

## Artefatos Globais

| Arquivo | Uso |
|---|---|
| `architecture.md` | Visão arquitetural integrada dos dois repositórios. |
| `c4-context.md` | Diagrama C4 de contexto. |
| `c4-containers.md` | Diagrama C4 de containers. |
| `c4-components.md` | Diagrama C4 de componentes. |
| `erd-complete.md` | ERD operacional consolidado. |
| `deployment.md` | Infraestrutura, deploy cloud e release Windows. |
| `traceability/spec-impact-matrix.md` | Impacto por capacidade/componente. |
| `traceability/code-spec-matrix.md` | Mapa código legado -> spec, gerado ao final. |

## Units Críticas, Detalhadas

| Unit | Por que é crítica | Status |
|---|---|---|
| `edge-agent-runtime/` | Orquestra o executável local, CLI, logs, paths, loop, heartbeat, setup API e update. | Em andamento |
| `edge-agent-activation/` | Ativação em campo, token de uso único e persistência de credenciais. | Pendente |
| `edge-agent-heartbeat-camera-health/` | Protocolo mais sensível instalado em clientes: heartbeat e health de cameras. | Pendente |
| `edge-agent-update-installation/` | Release Windows, autostart, auto-update, health gate e rollback. | Pendente |
| `edge/` | Backend de autenticação/ingest do agente. | Pendente |
| `stores/` | Lojas, ativação edge, status operacional, downloads e releases. | Pendente |
| `cameras/` | Cameras, ROI, snapshots, health e permissões. | Pendente |
| `billing/` | Trial/paywall e whitelist que não pode bloquear edge. | Pendente |

## Units de Apoio, Resumidas

| Unit | Cobertura |
|---|---|
| `edge-agent-diagnostics/` | Doctor, diagnóstico local e pacote de suporte. |
| `edge-agent-vision/` | Snapshot, fallback OpenCV/ffmpeg e eventos de visão. |
| `accounts/` | Auth, setup-state e onboarding. |
| `analytics/` | Métricas diárias, onboarding events e agent events. |
| `copilot/` | Insights, conversas, relatórios e outcomes. |
| `core/` | Entidades centrais: org, loja, camera, eventos e auditoria. |
| `frontend-auth-onboarding/` | Login e onboarding no React/Vite. |
| `frontend-dashboard-operations/` | Dashboard operacional e metas/alertas. |
| `frontend-cameras-alerts/` | UI de cameras, health, snapshots e alertas. |
| `frontend-copilot-reports-admin/` | UI de copilot, relatórios, admin e billing. |

## Modo de Geração

🟢 CONFIRMADO: O Redator está em modo otimizado por pacote:

- Specs detalhadas para units críticas.
- Specs resumidas para apoio.
- Checkpoint salvo por arquivo para retomada segura.
- Sem confirmação arquivo a arquivo, conforme solicitado.

## Lacunas Globais

| Lacuna | Impacto |
|---|---|
| 🔴 SLA final online/degraded/offline por ambiente | Afeta heartbeat, status edge/camera e alertas. |
| 🔴 RBAC completo em todos os ViewSets extensos | Afeta segurança de stores/cameras/support grant. |
| 🔴 Validação Windows real do autostart/update | Afeta operação em clientes. |
| 🔴 Provedor Postgres final e constraints reais | Afeta migração/reimplementação de dados. |
