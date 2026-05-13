# Inventario de Reconhecimento - DaleVision

Gerado em: 2026-05-06T19:44:13.1241613Z

## Escopo analisado

- C:\workspace\dalevision-edge-agent - agente local/Windows que roda no computador dos clientes, empacotado como executavel, responsavel por ativacao, heartbeat, camera health, diagnosticos, snapshots, visao computacional local e auto-update.
- C:\workspace\dale-vision - repositorio principal do app DaleVision, contendo backend Django/DRF, frontend React/Vite, contratos, specs, docs operacionais e scripts de deploy/operacao.

## Visao de produto inferida

O DaleVision e um sistema de visao/operacao para varejo com tres superficies principais:

- Agente edge instalado no cliente, conectado a NVR/cameras, emitindo heartbeat, camera health, eventos de visao e relatorios de update.
- Backend Django/DRF que centraliza autenticacao, lojas, cameras, edge devices, ingestao de eventos, copilot, billing, analytics, relatorios e operacao.
- Frontend React/Vite que oferece onboarding, dashboard, operacoes, cameras, alertas, copilot, relatorios, calibracao, billing e administracao.

## Repositorio dalevision-edge-agent

### Estrutura principal

- src/dalevision_edge_agent/ - pacote principal do agente.
- src/dalevision_edge_agent/vision/ - pipeline local de visao, fontes de video, ROI, worker e outbox.
- tests/ - testes pytest do runtime, diagnosticos, camera health, heartbeat, instalacao, update e visao.
- scripts/ - automacao Windows: release, instalacao, autostart, update, verificacao e suporte.
- release/ - artefatos e scripts de distribuicao para cliente.
- docs/runtime/ - arquitetura de runtime, protocolo heartbeat/camera health, update flow e instalacao.
- docs/field-ops/ - runbooks de instalacao, diagnostico, release e troubleshooting.
- specs/ - specs do sistema edge.

### Linguagens e arquivos relevantes

- Python: 73 arquivos.
- Markdown: 89 arquivos.
- PowerShell: 11 arquivos.
- Batch: 2 arquivos.
- YAML: 4 arquivos.

### Modulos identificados

- activation - bootstrap por token, hidratacao de ambiente e identidade do device.
- env - validacao de configuracao local e aliases de variaveis.
- heartbeat / heartbeat_client - protocolo de presenca do agente.
- cameras / camera_config / rtsp_test - descoberta, health check, snapshot e upload.
- diagnostics - doctor, diagnosticos legiveis e pacote para suporte.
- setup_api - API local de setup/onboarding.
- update / release_registry - politica, download, lock, relatorio e aplicacao de update.
- vision - worker, ROI, geometria, deteccao/movimento e outbox de eventos.
- install_service / installation_check / scripts Windows - instalacao/autostart no cliente.

### Entry points e comandos

- src/dalevision_edge_agent/main.py - entry point principal do agente e comandos CLI.
- pyproject.toml define script dalevision-edge-agent = dalevision_edge_agent.main:main.
- python -m dalevision_edge_agent.main - execucao local indicada no AGENTS.md.
- python -m dalevision_edge_agent.main doctor --nvr-ip <IP_DO_NVR> --share - diagnostico.
- src/run_agent.py e src/mvp_agent.py - entry points auxiliares/legados.
- scripts/release_windows.ps1 - empacotamento zip release.
- scripts/install-service.ps1, scripts/install-user.ps1, scripts/update.ps1 - operacao Windows.

### Configuracoes e CI/CD

- pyproject.toml - packaging Python, dependencias e scripts.
- pytest.ini - configuracao de testes.
- .github/ presente no repositorio.
- .env existe, mas nao foi lido para evitar segredos.

### Banco de dados e persistencia

- Nao ha schema relacional proprio no agente.
- Persistencia local aparece por arquivos/configuracoes, cache de snapshots, logs e diretorio de updates.
- A integracao persistente principal acontece via API cloud.

### Testes

- Framework: pytest; tambem ha testes Pester para script Windows.
- Testes cobrem ativacao, camera config, camera health, env, heartbeat, instalacao, diagnostico, scanner, update, vision outbox/ROI/video source/worker e fluxo run-once.

## Repositorio dale-vision

### Estrutura principal

- backend/ - configuracao Django: settings, urls, ASGI/WSGI, middleware e views de health.
- apps/ - apps Django por dominio.
- frontend/ - SPA React/Vite/TypeScript.
- docs/ - contratos, arquitetura, plataforma, operacao, incidentes e runbooks.
- specs/ - specs existentes por modulo/jornada e ADRs.
- scripts/ e bin/ - automacao de deploy, jobs Render, validacoes, smoke tests e snapshots.
- db.sqlite3 - banco local de desenvolvimento detectado.

### Linguagens e arquivos relevantes

- Python: 308 arquivos.
- Markdown: 111 arquivos.
- TSX: 86 arquivos.
- TypeScript: 52 arquivos.
- SQL: 15 arquivos.
- JavaScript/CJS/MJS: 15 arquivos.
- Shell/PowerShell: 20 arquivos.

### Backend Django/DRF

Apps Django identificados: accounts, analytics, billing, cameras, copilot, core, edge e stores.

Arquivos de roteamento principais:

- backend/urls.py - monta rotas admin, swagger/redoc, health e inclui apps.
- apps/*/urls.py - endpoints por dominio.
- Uso de APIView, ViewSet, DefaultRouter e rotas api/v1.

### Frontend React/Vite

- frontend/src/main.tsx - bootstrap React com BrowserRouter.
- frontend/src/App.tsx - roteamento central com Routes/Route.
- frontend/src/pages/ - Home, Login, Register/Activate, Onboarding, Dashboard, Operations, Stores, Cameras, Alerts, Copilot, Reports, Calibration, Admin, Billing, Settings, Profile, EdgeHelp, Privacy/Terms.
- frontend/src/services/ - clientes de API por dominio: auth, stores, cameras, alerts, copilot, analytics, onboarding, support, sales, journey etc.
- frontend/src/components/ - layout, wizard de ativacao, ROI editor, edge setup modal, guards, charts e componentes de dashboard.

### Dependencias e frameworks

- Backend: Django 4.2.11, Django REST Framework 3.14.0, django-cors-headers, django-filter, django-rest-knox, drf-yasg, gunicorn, whitenoise, psycopg2, supabase, boto3, Redis, OpenCV, numpy, pandas, torch/ultralytics no requirements completo.
- Frontend: React 19.2, React DOM 19.2, React Router 7.12, TanStack Query 5.90, Supabase JS 2.50, Axios, Recharts, Vite 7.2, TypeScript 5.9, Vitest 3.2, Tailwind 3.4.
- Gerenciadores: pip/requirements para backend; pnpm declarado no frontend.

### Entry points e deploy

- manage.py - entry point Django.
- backend/wsgi.py e backend/asgi.py - runtime Django.
- bin/render_start.sh e bin/render_build.sh - deploy Render.
- vercel.json raiz aponta rootDirectory frontend.
- frontend/vercel.json contem redirects de dominio e rewrite SPA.
- frontend/package.json scripts: dev, build, lint, preview, test, test:run, test:edge-setup.

### Banco de dados e modelos

Sinais superficiais encontrados:

- db.sqlite3 local.
- Migrations Django em apps/*/migrations/.
- SQL historico/operacional em docs/archive/supabase-sql/ e scripts/sql/.
- Modelos Django em apps/*/models.py.
- Integracao Supabase em apps/core/integrations/supabase_storage.py, apps/accounts/auth_supabase.py e frontend/src/lib/supabase.ts.

### Testes

- Backend: testes Django/unittest/APITestCase distribuidos por apps e arquivos tests*.py.
- Frontend: Vitest + Testing Library, arquivos .test.tsx e .test.ts.
- Contratos e smoke tests em scripts PowerShell/Python e docs/contracts.

## Integracoes externas detectadas

- Supabase/Auth/Storage.
- Render para backend/jobs.
- Vercel para frontend.
- WhatsApp/Meta webhook no modulo Copilot.
- Google APIs.
- OpenRouter para Copilot/LLM.
- Redis/cache.
- PostgreSQL/Neon/Supabase conforme docs e dependencias.
- NVR/cameras via RTSP no agente.
- ffmpeg/OpenCV/Ultralytics/Torch para snapshot/visao.

## Sinais de organizacao das specs

Ha dois sinais fortes coexistindo:

- Pastas por dominio: apps/accounts, apps/stores, apps/edge, frontend/src/pages/*, src/dalevision_edge_agent/*.
- Roteamento centralizado/backend e frontend: backend/urls.py, apps/*/urls.py, frontend/src/App.tsx.

Sugestao do Scout: organizacao hibrida, separando por dominios/capacidades e preservando contratos de endpoints quando o comportamento depende de API.
