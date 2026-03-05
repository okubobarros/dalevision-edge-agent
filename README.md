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
- Cenário remoto (fora da rede da loja), opcional para evitar ruído de autenticação/sync:
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
```
Observações:
- `VISION_EMBED_THUMBNAIL=1` envia thumbnail blur (base64) no payload do alerta.
- Sem OpenCV/YOLO, o worker degrada com logs e segue sem bloquear o agente.

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
