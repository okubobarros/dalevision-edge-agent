# Update Flow

Baseado em AUTO_UPDATE_V1:
1) Consulta de policy: `GET {CLOUD_BASE_URL}/api/edge/update-policy/`.
2) Se `target_version` > current:
   - baixa pacote; valida checksum; aplica update (fora de service mode); reinicia.
3) Reporta fases via `POST {CLOUD_BASE_URL}/api/edge/update-report/` com eventos `started`, `downloaded`, `verified`, `activated`, `healthy`, `failed`.
4) Fallback legado: usa `UPDATE_CHECK_URL` quando policy falha.

Variáveis
- `AUTO_UPDATE_ENABLED`, `UPDATE_INTERVAL_SECONDS`, `UPDATE_CHECK_URL` (fallback), `EDGE_TOKEN`, `STORE_ID`, `AGENT_ID`.

Regras
- Em `SERVICE_MODE`, não faz swap automático.
- Status `healthy` é enviado no boot após update concluído.
- Bloquear release que inclua assets proibidos (video/modelos/envs) conforme pipeline.
