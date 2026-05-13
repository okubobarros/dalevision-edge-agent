# Enviar Heartbeat, Requirements

## Visão Geral

🟢 CONFIRMADO: Caso de uso responsável por publicar presença do agente local no backend como evento `edge_heartbeat`.

## Requisitos

| ID | Requisito | Prioridade | Critério |
|---|---|---|---|
| RF-EH-01 | 🟢 Montar payload `edge_heartbeat`. | Must | `event_name=edge_heartbeat`, `source=edge`. |
| RF-EH-02 | 🟢 Enviar com edge token. | Must | Request usa token para autenticação edge. |
| RF-EH-03 | 🟢 Retornar status/erro de forma estruturada. | Must | `(ok,status,error)`. |
| RF-EH-04 | 🟢 Tratar timeout/rede como status `None`. | Must | RequestException retorna `False,None,error`. |

## Critérios

```gherkin
Dado settings válidos
Quando enviar heartbeat
Então o backend deve receber edge_heartbeat
E resposta 2xx deve retornar ok true
```
