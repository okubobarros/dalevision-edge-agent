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
   - tenta capturar snapshot minimo (OpenCV; fallback ffmpeg se disponivel)
4. inclui no heartbeat:
   - `cameras_total`, `cameras_online`, `cameras_degraded`, `cameras_offline`, `cameras_unknown`
   - lista resumida `cameras` com `camera_id`, `status`, `roi_version`

Falha de uma camera nao derruba o processo inteiro.

## Endpoints usados
- `GET /api/v1/stores/:store_id/cameras/`
- `GET /api/v1/cameras/:id/roi/latest`
- `POST /api/v1/cameras/:id/health/`
- `POST /api/edge/events/` (heartbeat)

## Como o dono instala (passo a passo)
1. Baixe o ZIP oficial e extraia.
2. Edite o `.env` com os dados do suporte.
3. Clique em `02_TESTE_RAPIDO.bat` e aguarde `status=201`.
4. Clique em `01_INICIAR_DALEVISION.bat` e deixe rodando.
5. Se precisar de diagnostico, rode `03_DIAGNOSTICO_E_SUPORTE.bat` e envie o ZIP via WhatsApp.

## Comandos de suporte
Diagnostico completo:
```
dalevision-edge-agent.exe doctor --share
```

Scan de NVRs na rede:
```
dalevision-edge-agent.exe scan --mode nvr --range auto
```

Teste RTSP Intelbras:
```
dalevision-edge-agent.exe test-rtsp --ip 192.168.1.10 --user admin --pass 1234 --channel 1 --subtype 1
dalevision-edge-agent.exe test-rtsp --ip 192.168.1.10 --user admin --pass 1234 --scan-channels
```

## Snapshot (opcional)
O snapshot e opcional e nao deve quebrar o agente.
- Primeiro tenta OpenCV (se empacotado).
- Se nao houver OpenCV, tenta `ffmpeg` no PATH.
- Se ambos falharem, loga e segue sem snapshot.
Snapshots sao salvos em `cache/snapshots/<camera_id>/<timestamp>.jpg`.

## Logs
- Logs do agente em `%PROGRAMDATA%\\DaleVision\\EdgeAgent\\logs\\agent.log` (ou `logs/` se `PROGRAMDATA` nao existir).
- Diagnosticos salvos em `%PROGRAMDATA%\\DaleVision\\EdgeAgent\\logs\\diagnostics-*.json` e `.txt`.

## Rodar 24/7 (Windows)
Instalar como tarefa agendada:
```
powershell -ExecutionPolicy Bypass -File "04 - Instalar como Serviço (Admin).ps1"
```

## Auto-update (MVP)
Configurar no `.env`:
- `UPDATE_CHECK_URL`
- `ENABLE_AUTO_UPDATE=1`
- `UPDATE_INTERVAL_SECONDS=21600`

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

## Testes locais
Unit tests (pytest):
```
python -m pytest -k run_once
```

Pester (install-service):
```
Invoke-Pester tests/pester/install-service.Tests.ps1
```
