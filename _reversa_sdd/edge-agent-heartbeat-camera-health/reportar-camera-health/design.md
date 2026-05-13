# Reportar Camera Health, Design Técnico

## Fluxo

```mermaid
flowchart TD
    A[Camera config] --> B[Extrair id e RTSP]
    B --> C{RTSP válido?}
    C -- não --> D[Retornar status error]
    C -- sim --> E[Testar conexão socket/RTSP]
    E --> F[Calcular latency_ms]
    F --> G[Snapshot/ROI se habilitado]
    G --> H[send_camera_health_event]
    H --> I[Atualizar watchdog se OK]
```

## Campos

| Campo | Uso | Confiança |
|---|---|---|
| `camera_id` | Identidade da camera. | 🟢 |
| `status` | Status operacional. | 🟢 |
| `latency_ms` | Sinal de qualidade. | 🟢 |
| `checked_at` | Timestamp de coleta. | 🟢 |
| `error` | Diagnóstico de falha. | 🟢 |
| `roi_version` | Contexto de configuração. | 🟢 |
