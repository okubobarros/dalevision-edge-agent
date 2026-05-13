# Reportar Camera Health, Requirements

## Visão Geral

🟢 CONFIRMADO: Caso de uso responsável por verificar saúde de cada câmera ativa e reportar status ao backend.

## Requisitos

| ID | Requisito | Prioridade | Critério |
|---|---|---|---|
| RF-CH-01 | 🟢 Extrair `camera_id` e RTSP da configuração da câmera. | Must | Aceita `camera_id`, `id` ou `uuid`. |
| RF-CH-02 | 🟢 Retornar erro controlado sem RTSP. | Must | `rtsp_url_missing` ou `rtsp_host_missing`. |
| RF-CH-03 | 🟢 Medir latência quando conexão funciona. | Should | `latency_ms` preenchido. |
| RF-CH-04 | 🟢 Enviar evento `camera_health` ao backend. | Must | `send_camera_health_event`. |
| RF-CH-05 | 🟢 Atualizar watchdog em sucesso. | Should | `last_camera_health_ok_at`. |

## Critérios

```gherkin
Dado uma câmera online
Quando reportar camera health
Então o backend deve receber status online e latency_ms
```
