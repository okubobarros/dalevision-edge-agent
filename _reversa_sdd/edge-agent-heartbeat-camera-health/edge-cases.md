# Edge Agent Heartbeat e Camera Health, Edge Cases

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-HB-01 | Backend indisponível | Heartbeat retorna status `None`, estado `degraded`. | `heartbeat.py`, teste | 🟢 |
| EC-HB-02 | Backend retorna 500 | Falha registrada; estado não deve virar auth error. | `heartbeat.py`, `main.py` | 🟢 |
| EC-HB-03 | Backend retorna 401/403 | Estado `error`; falhas consecutivas podem encerrar. | `main.py`, teste | 🟢 |
| EC-HB-04 | Camera sem RTSP | Health retorna `error=rtsp_url_missing`. | `cameras.py` | 🟢 |
| EC-HB-05 | RTSP sem host | Health retorna `error=rtsp_host_missing`. | `cameras.py` | 🟢 |
| EC-HB-06 | Snapshot falha | Log claro; health/heartbeat continuam sem snapshot. | `domain.md`, `cameras.py` | 🟢 |
| EC-HB-07 | ROI fetch auth falha | Auth tracker registra; pode se tornar fatal conforme config. | `cameras.py`, `main.py` | 🟢 |
| EC-HB-08 | Camera event auth falha | Pode retornar `EXIT_AUTH_ERROR` se fatal. | `main.py` | 🟢 |
| EC-HB-09 | Camera sync desabilitado | Log periódico e heartbeat continua. | `main.py` | 🟢 |
| EC-HB-10 | Status stale no backend | Deve virar degraded/offline conforme thresholds. | `views_edge_status.py`, `domain.md` | 🟢 |

## Cenários

```gherkin
Dado uma câmera sem RTSP configurado
Quando executar camera health
Então o payload deve ter status error
E error igual a rtsp_url_missing
```

```gherkin
Dado rede indisponível para o backend
Quando enviar heartbeat
Então o estado local deve virar degraded
E o agente deve continuar tentando
```

```gherkin
Dado token edge inválido
Quando heartbeat ou camera event responder 401
Então o erro deve ser classificado como autenticação
```
