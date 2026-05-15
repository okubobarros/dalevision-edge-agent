# CI-CD.md - Template

## Pipeline
1. Lint + type checks
2. Unit tests
3. Contract tests (heartbeat/camera health)
4. E2E onboarding harness
5. Build release artifacts
6. Publish gated release

## Gates obrigatorios
- Regressao onboarding bloqueia merge.
- Falha em contrato legado bloqueia merge.
- Cobertura minima dos modulos criticos.
