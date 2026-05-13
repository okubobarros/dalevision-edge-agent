# Enviar Heartbeat, Design Técnico

## Fluxo

```mermaid
flowchart TD
    A[Receber settings e camera_fields] --> B[Criar HeartbeatPayload]
    B --> C[Mesclar extra_data]
    C --> D[send_heartbeat]
    D --> E{HTTP 2xx?}
    E -- sim --> F[ok true]
    E -- não --> G[ok false status detail]
    D --> H{RequestException?}
    H -- sim --> I[ok false status none error]
```

## Evidência

| Arquivo | Símbolo | Confiança |
|---|---|---|
| `heartbeat.py` | `send_heartbeat` | 🟢 |
| `heartbeat_client.py` | `HeartbeatPayload`, `HeartbeatClient.send` | 🟢 |
| `main.py` | chamada no loop | 🟢 |
