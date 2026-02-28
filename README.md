# DaleVision Edge Agent

Agente local para manter a loja online no cloud e monitorar a saúde das câmeras (sem streaming em tempo real para o cloud).

## Quick Start (Windows)
1. Baixe o ZIP oficial e extraia.
2. Edite o `.env` com `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID`.
3. Teste: execute `01_TESTE_RAPIDO.bat` e aguarde `status=201`.
4. Produção: execute `02_INSTALAR_AUTOSTART.bat` (admin) e reinicie o PC.
5. Verifique: execute `03_VERIFICAR_STATUS.bat`.
6. Para remover: execute `04_REMOVER_AUTOSTART.bat`.

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

## Diagnóstico
- `Diagnose.bat` gera um ZIP de diagnóstico para suporte.
- Logs principais ficam em `logs\` no bundle (ou em `%PROGRAMDATA%\DaleVision\EdgeAgent\logs\` quando instalado).

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
