# dalevision-edge-agent

Edge Agent para manter a loja online no cloud e monitorar health de multiplas cameras (sem streaming realtime para cloud).

## Configuracao (.env)
Variaveis obrigatorias:
- `CLOUD_BASE_URL`
- `STORE_ID`
- `EDGE_TOKEN`

## Fluxo do agente
Em modo normal (`run.bat`), o agente executa continuamente:
1. envia `edge_heartbeat` para `/api/edge/events/`
2. sincroniza lista de cameras da store a cada ~60s
3. para cada camera ativa (limitado por `MAX_ACTIVE_CAMERAS`):
   - executa healthcheck leve de conectividade RTSP (socket TCP, timeout curto)
   - opcionalmente envia RTSP `DESCRIBE` (flag `RTSP_DESCRIBE_ENABLED`)
   - mede `latency_ms`
   - publica health em `/api/v1/cameras/:id/health/`
   - busca `roi/latest` por camera e cacheia localmente por `camera_id + version`
4. inclui no heartbeat:
   - `cameras_total`, `cameras_online`, `cameras_degraded`, `cameras_offline`, `cameras_unknown`
   - lista resumida `cameras` com `camera_id`, `status`, `roi_version`

Falha de uma camera nao derruba o processo inteiro.

## Endpoints usados
- `GET /api/v1/stores/:store_id/cameras/`
- `GET /api/v1/cameras/:id/roi/latest`
- `POST /api/v1/cameras/:id/health/`
- `POST /api/edge/events/` (heartbeat)

## Como cadastrar cameras no cloud e ver status no dashboard
1. Cadastre as cameras da loja no backend cloud (vinculadas ao `STORE_ID`).
2. Confirme que cada camera possui `camera_id` e URL RTSP.
3. Inicie o agente com o `.env` da loja.
4. No dashboard, acompanhe:
   - online/offline da loja (heartbeat)
   - status de cada camera (`camera.health`)
   - versao de ROI aplicada por camera

## Checklist de validacao ponta-a-ponta
1. Cadastrar camera no dashboard.
2. Agente sincroniza e manda health.
3. Dashboard mostra camera online.
4. Desenhar ROI e publicar.
5. Agente faz fetch ROI latest e inclui `roi_version` nos eventos.

## Logs
- `logs/agent.log`: logs estruturados do agente (heartbeat, sync de cameras, ROI, erros)
- `logs/stdout.log`: stdout/stderr do processo (via `run.bat`)
