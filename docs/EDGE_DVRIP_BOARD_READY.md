# Edge Execution Board — DVRIP + RTSP Fallback

Baseado em: `docs/EDGE_DVRIP_RTSP_BACKLOG.md`

## Sprint A (Edge core)

| ID | Título | Owner | Priority | Points | Dependências | Done when |
|---|---|---|---|---:|---|---|
| EDGE-DVRIP-01 | Parser e handshake tolerante iCSee/XM | Edge | P0 | 8 | - | Login/monitor funcionam com variações de firmware |
| EDGE-DVRIP-02 | Probe com retries curtos e timeout por tentativa | Edge | P0 | 5 | EDGE-DVRIP-01 | `probe()` retorna `ok/protocol/channel/stream/error` |
| EDGE-DVRIP-03 | Captura de frame válida com evidência local | Edge | P1 | 5 | EDGE-DVRIP-02 | `last_frame.jpg` persistido e reutilizável |

## Sprint B (Edge onboarding API)

| ID | Título | Owner | Priority | Points | Dependências | Done when |
|---|---|---|---|---:|---|---|
| EDGE-DVRIP-04 | Endpoint canônico `POST /onboarding/test-stream` | Edge | P0 | 8 | EDGE-DVRIP-03 | aceita `auto|rtsp|dvrip` e retorna `attempts[]` |
| EDGE-DVRIP-05 | Atualizar `/health` capabilities (`test_stream`,`dvrip_icsee`) | Edge | P1 | 2 | EDGE-DVRIP-04 | frontend detecta suporte por capability |
| EDGE-DVRIP-06 | Suíte de testes (parser/probe/api/sanitização) | Edge + QA | P0 | 5 | EDGE-DVRIP-04 | cobertura mínima dos fluxos críticos |

## Quality gates
- Não quebrar endpoints legados: `/onboarding/test-camera`, `/onboarding/test-rtsp`, `/onboarding/snapshot`.
- Não logar senha nem URL com segredo.
- Compatibilidade intacta de heartbeat/camera_health.

## Test checklist por ticket
- EDGE-DVRIP-01: `tests/test_dvrip_icsee_parser.py`
- EDGE-DVRIP-02: `tests/test_dvrip_icsee_probe.py`
- EDGE-DVRIP-04: `tests/test_setup_api_test_stream.py`
- EDGE-DVRIP-06: execução de regressão dos testes existentes de setup/onboarding

## Sequência recomendada de PRs
1. PR-1: EDGE-DVRIP-01 + EDGE-DVRIP-02
2. PR-2: EDGE-DVRIP-03
3. PR-3: EDGE-DVRIP-04 + EDGE-DVRIP-05
4. PR-4: EDGE-DVRIP-06 + docs/runbook
