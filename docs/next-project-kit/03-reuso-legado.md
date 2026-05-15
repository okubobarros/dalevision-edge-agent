# Reuso do Legado (Manter e Evoluir)

## Manter sem regressao
- Protocolo heartbeat/camera health atual.
- `doctor` com `--share` e artefatos de suporte remoto.
- Politica de snapshot best-effort (OpenCV/ffmpeg opcional).
- Sanitizacao de logs para token/senha.

## Reutilizar diretamente
- Validacoes e carga de ambiente: `src/dalevision_edge_agent/env.py`.
- Bootstrap de ativacao e hydration de env: `src/dalevision_edge_agent/activation.py`.
- Mapeamento inicial de codigos onboarding: `src/dalevision_edge_agent/onboarding_error_codes.py`.
- Readiness report: `src/dalevision_edge_agent/onboarding_readiness.py`.
- Especificacao de onboarding frictionless: `specs/EDGE-SYSTEM-003-onboarding-frictionless.md`.

## Refatorar no novo projeto
- Separar claramente:
  - `installer/bootstrap`
  - `runtime/heartbeat-health`
  - `camera-discovery-config`
  - `observability/diagnostics`
- Consolidar erros de onboarding em um catalogo unico versionado.
- Criar estado canonico de ativacao no backend como unica fonte de verdade.

## Evitar no novo ciclo
- Dependencia de edicao manual de `.env` para happy path.
- Confirmacoes manuais no frontend para etapas tecnicas.
- Mensagens de erro tecnicas sem traducao operacional.
