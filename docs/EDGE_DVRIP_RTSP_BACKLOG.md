# Edge Agent Backlog — DVRIP iCSee/XM + Fallback RTSP

## Objetivo
Incorporar o fluxo que funcionou em campo (DVRIP porta 34567) ao agente oficial, sem regressão do protocolo atual de heartbeat/camera health.

## Escopo técnico no repositório

### 1) Novo módulo DVRIP
- Criar `src/dalevision_edge_agent/dvrip_icsee.py`
- Responsabilidades:
  - `probe(config) -> result`
  - `capture_frame(config) -> frame_result`
  - normalização de erros DVRIP

### 2) Orquestração de teste canônico
- Evoluir `src/dalevision_edge_agent/setup_api.py`:
  - novo endpoint `POST /onboarding/test-stream`
  - mantém compatibilidade de endpoints legados
- Entrada exemplo:
```json
{
  "connection_type": "auto",
  "ip": "192.168.15.74",
  "username": "admin",
  "password": "***",
  "channel": 0,
  "stream_type": "main",
  "dvrip_port": 34567
}
```
- Saída exemplo:
```json
{
  "ok": true,
  "validated_protocol": "dvrip",
  "working_channel": 0,
  "working_stream": "main",
  "latency_ms": 732,
  "attempts": [
    {"protocol": "rtsp", "ok": false, "error": "RTSP_TIMEOUT"},
    {"protocol": "dvrip", "ok": true}
  ]
}
```

### 3) Capabilities e readiness
- Atualizar capabilities em `/health`:
  - `test_stream: true`
  - `dvrip_icsee: true`
- Atualizar readiness para considerar `camera_validated` quando protocolo vencedor for RTSP ou DVRIP.

### 4) Evidência e suporte remoto
- Persistir `last_frame.jpg` por câmera em `cache/snapshots`.
- Incluir diagnóstico em JSON com:
  - protocolo tentado
  - código de erro normalizado
  - tempos por tentativa
- Garantir sanitização de segredos no log.

## Backlog técnico (tickets)

`EDGE-DVRIP-01` Parser e handshake tolerante
- Aceitar variações de resposta de firmware iCSee/XM.
- AC: login e monitor funcional com replies não estritos.

`EDGE-DVRIP-02` Probe com retries curtos
- Timeout por tentativa + retries por rodada.
- AC: não bloquear thread principal e retornar erro canônico.

`EDGE-DVRIP-03` Captura de frame válida
- AC: gera `last_frame.jpg` quando sucesso.

`EDGE-DVRIP-04` Endpoint `test-stream`
- AC: modo `auto` tenta RTSP e fallback DVRIP automaticamente.

`EDGE-DVRIP-05` Atualizar `/health` capabilities
- AC: frontend consegue detectar suporte sem heurística frágil.

`EDGE-DVRIP-06` Testes automatizados
- AC: suíte cobre parser, probe, endpoint e sanitização.

## Plano de testes (edge)

### Unit tests
- `tests/test_dvrip_icsee_parser.py`
- `tests/test_dvrip_icsee_probe.py`
- `tests/test_setup_api_test_stream.py`

### Integration tests
- Mock RTSP fail + DVRIP success com asserts de `attempts[]`.
- Mock DVRIP auth fail com código `DVRIP_AUTH_FAIL`.

### Smoke em ambiente de campo
- Com câmera iCSee/XM real:
  - `connection_type=auto`
  - esperado: `validated_protocol=dvrip` e frame salvo.

## Critérios de saída para merge
- Sem regressão em testes existentes de onboarding/camera health.
- Logs sem credenciais expostas.
- Contrato `test-stream` estável e documentado.
