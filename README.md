# DaleVision Edge Agent

Agente local para manter a loja online no cloud e monitorar a saúde das câmeras (sem streaming em tempo real para o cloud).

## Quick Start (Windows)
1. Baixe o ZIP oficial e extraia.
2. Edite o `.env` com `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID`.
3. Teste: execute `01_TESTE_RAPIDO.bat` e aguarde `status=201`.
4. Produção: execute `02_INSTALAR_AUTOSTART.bat` (admin) e reinicie o PC.
5. Verifique: execute `03_VERIFICAR_STATUS.bat`.
6. Para remover: execute `04_REMOVER_AUTOSTART.bat`.

## Configuração recomendada (produção)
- Manter heartbeat sempre ativo mesmo com falhas temporárias de câmeras:
```
CAMERA_SYNC_FATAL=0
```
- Fonte de verdade de câmeras (recomendado para produto):
```
CAMERA_SOURCE_MODE=api_first
CAMERA_SYNC_ENABLED=1
VISION_REMOTE_CAMERA_SYNC_ENABLED=1
CAMERAS_JSON=[]
```
- Fallback de contingência (piloto/local):
```
CAMERA_SOURCE_MODE=local_only
CAMERA_SYNC_ENABLED=0
VISION_REMOTE_CAMERA_SYNC_ENABLED=0
CAMERAS_JSON=[...]
```
- Cenário remoto de diagnóstico (fora da rede da loja), opcional para reduzir ruído:
```
CAMERA_SYNC_ENABLED=0
```

## Vision (detecções CV)
Ative o pipeline mínimo (ocioso, fila, celular) por env:
```
VISION_ENABLED=1
VISION_ALERTS_ENABLED=1
VISION_POLL_SECONDS=5
VISION_BUCKET_SECONDS=30
VISION_QUEUE_SIZE_THRESHOLD=3
VISION_QUEUE_WAIT_SECONDS=60
VISION_QUEUE_COOLDOWN_SECONDS=180
VISION_INACTIVITY_SECONDS=120
VISION_INACTIVITY_COOLDOWN_SECONDS=300
VISION_PHONE_ENABLED=1
VISION_PHONE_SECONDS=30
VISION_PHONE_COOLDOWN_SECONDS=300
VISION_PHONE_CLASS_ID=67
VISION_BLUR_ENABLED=1
VISION_BLUR_STRENGTH=41
VISION_EMBED_THUMBNAIL=0
VISION_THUMBNAIL_WIDTH=320
VISION_OUTBOX_ENABLED=1
VISION_OUTBOX_PATH=.\cache\vision_outbox.sqlite
VISION_OUTBOX_BATCH_SIZE=50
VISION_OUTBOX_MAX_ATTEMPTS=8
```
Observações:
- `VISION_EMBED_THUMBNAIL=1` envia thumbnail blur (base64) no payload do alerta.
- Eventos de visão usam outbox SQLite offline-first quando `VISION_OUTBOX_ENABLED=1`.
- Sem OpenCV/YOLO, o worker degrada com logs e segue sem bloquear o agente.
- ROI remoto v2 aceita `zones + lines + ownership`.
- Para `entry_exit`, a linha e direcional: a ordem dos dois pontos define o sentido de `entry` vs `exit`.
- O payload `vision.metrics.v1` carrega `zone_id`, `roi_entity_id`, `metric_type` e `ownership.mode=single_camera_owner`.

## Replay Mode (dev only)
Use MP4 local como fonte para validar ROI e métricas antes de ir para a loja.

Envs principais:
```
VISION_ENABLED=1
VISION_SOURCE=video
VISION_VIDEO_PATH=.\videos\cam01_balcao.mp4
VISION_ROI_PATH=.\tools\dev_configs\cam01.yaml
VISION_BUCKET_SECONDS=10
VISION_VIDEO_REALTIME=0
VISION_VIDEO_LOOP=0
VISION_CAMERA_ID=cam01-demo
VISION_ROLE=balcao
```

Exemplo (PowerShell, 1 camera):
```powershell
$env:VISION_ENABLED="1"
$env:VISION_SOURCE="video"
$env:VISION_VIDEO_PATH=".\videos\cam01_balcao.mp4"
$env:VISION_ROI_PATH=".\tools\dev_configs\cam01.yaml"
$env:VISION_BUCKET_SECONDS="10"
$env:VISION_VIDEO_REALTIME="0"
python -m dalevision_edge_agent.main
```

Notas:
- Para rodar 3 cameras, abra 3 terminais e troque `VISION_VIDEO_PATH`/`VISION_ROI_PATH`.
- Os logs por bucket mostram `fila_max`, `consumo_max`, `staff_active_est` e `queue_avg_seconds`.

## Diagnóstico
- `Diagnose.bat` gera um ZIP de diagnóstico para suporte.
- Logs principais ficam em `logs\` no bundle (ou em `%PROGRAMDATA%\DaleVision\EdgeAgent\logs\` quando instalado).

## Release safety checks
O script de release bloqueia qualquer pacote que contenha:
- `tools/`, `outputs/`
- `configs/*.yaml`
- vídeos (`*.mp4`, `*.avi`, `*.mov`, `*.mkv`)
- pesos de modelo (`yolov8*.pt` e qualquer `*.pt`)
- arquivos sensíveis: `.env`, `*.env`, `*.log`

Runtime canonico:
- O entrypoint oficial do agente e `dalevision_edge_agent.main:main` (definido no `pyproject.toml`).
- Trilha `edge-agent/src` e legada para referencia/historico e nao deve ser usada como runtime de release.

Se qualquer um desses arquivos aparecer na pasta de staging ou no ZIP, o release falha e lista os caminhos encontrados.

## Suporte (CLI)
Diagnóstico completo:
```bash
dalevision-edge-agent.exe doctor --share
```

Scan de NVRs:
```bash
dalevision-edge-agent.exe scan --mode nvr --range auto
```

## Documentação
Documentação detalhada, specs e runbooks ficam no repositório interno do time.

Release e atualização
- `git push` comum não publica release nem atualiza `edge_releases`.
- O fluxo automático de release + registro em `edge_releases` acontece em `git tag vX.Y.Z && git push origin vX.Y.Z`.
- Runbook: `docs/field-ops/release-runbook.md`.
