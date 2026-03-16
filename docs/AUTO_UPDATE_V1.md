# Auto Update v1 (Edge Agent)

## Objetivo
Permitir atualização remota segura do agente com telemetria para operação.

## Fluxo principal (novo)
1. Agent consulta policy:
- `GET {CLOUD_BASE_URL}/api/edge/update-policy/`
2. Se houver `target_version` maior:
- baixa pacote;
- valida checksum;
- aplica update (fora de service mode);
- reinicia.
3. Agent reporta fases:
- `POST {CLOUD_BASE_URL}/api/edge/update-report/`
- eventos: `started`, `downloaded`, `verified`, `activated`, `healthy`, `failed`.

## Fallback legado
Se policy falhar ou não existir, o agente tenta `UPDATE_CHECK_URL` (quando configurado).

## Variáveis relevantes
- `CLOUD_BASE_URL`
- `EDGE_TOKEN`
- `STORE_ID`
- `AGENT_ID`
- `AUTO_UPDATE_ENABLED` (ou `ENABLE_AUTO_UPDATE`)
- `UPDATE_INTERVAL_SECONDS`
- `UPDATE_CHECK_URL` (legado/fallback)

## Observações
- Em `SERVICE_MODE`, o agente não aplica swap local automático.
- O status `healthy` é enviado no boot após atualização concluída.
