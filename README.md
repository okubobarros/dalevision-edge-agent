# DaleVision Edge Agent

Agente local para manter a loja online no cloud e monitorar a saúde das câmeras (sem streaming em tempo real para o cloud).

## Quick Start (Windows)
1. Baixe o ZIP oficial e extraia.
2. Edite o `.env` com `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN` e `AGENT_ID`.
3. Teste: execute `01_TESTE_RAPIDO.bat` e aguarde `status=201`.
4. Produção: execute `02_INSTALAR_AUTOSTART.bat` (admin) e reinicie o PC.
5. Verifique: execute `03_VERIFICAR_STATUS.bat`.
6. Para remover: execute `04_REMOVER_AUTOSTART.bat`.

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
