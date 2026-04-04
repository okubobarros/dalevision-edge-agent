# Troubleshooting Runbook

Sintomas comuns e ações
- Sem heartbeat: checar rede/firewall, EDGE_TOKEN, relógio; verificar `logs/agent.log`.
- Câmera offline: testar credenciais/cabos; rodar `scan --mode nvr`; revisar `CAMERA_SOURCE_MODE`.
- ROI não aplica: verificar `roi_version` enviada; revalidar calibração local; checar erros no edge.
- Auto-update falhou: consultar `logs/update.log`; verificar `AUTO_UPDATE_ENABLED`, `SERVICE_MODE`; tentar fallback manual.
- Snapshot falhou: confirmar OpenCV/ffmpeg; avaliar iluminação.

Escalação
- Anexar `diagnostics.zip` gerado pelo `doctor --share` em contato com suporte.
