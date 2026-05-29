# EDGE-SETUP-001 — Endpoint canônico `POST /onboarding/test-rtsp`

> Spec executável. Quebra o trabalho em alterações de arquivo, contrato de API e matriz de testes.

- **ID**: `EDGE-SETUP-001`
- **Prioridade**: P0 (desbloqueador de ativação de câmera)
- **Repo**: `dalevision-edge-agent`
- **Relacionado**: `FE-SETUP-001` (já implementado no frontend), `EDGE-SETUP-002`
- **Última atualização**: 2026-05-29

---

## 1. Problema

O wizard de ativação do frontend (`StoreActivationWizard.tsx`) já implementa o multi-probe de templates RTSP (`FE-SETUP-001`). Para cada template (`dahua`, `hikvision`, `generic`), ele chama:

```
POST http://127.0.0.1:8787/onboarding/test-rtsp
Body: { "rtsp_url": "rtsp://user:pass@ip:554/..." }
```

O edge agent **não tem esse endpoint**. Ao receber `404` ou `405`, o wizard cai no fallback legado (testa via `/onboarding/snapshot` sem saber o resultado por template). Isso impede:

- Diagnóstico por template (qual URL funcionou, por qual razão falhou)
- `reason_code` canônico por tentativa
- Telemetria de probe por marca/modelo/canal

### Gap atual

| Endpoint | Método | Status |
|----------|--------|--------|
| `/onboarding/test-camera` | GET query params | Existe — contrato diferente, só Intelbras/Dahua |
| `/onboarding/test-rtsp` | **POST body JSON** | **Ausente** |
| `/onboarding/snapshot?rtsp_url=` | GET | Existe mas ignora o param `rtsp_url` |

---

## 2. Contrato de API

### 2.1 `POST /onboarding/test-rtsp`

**Request**
```http
POST /onboarding/test-rtsp
Content-Type: application/json

{ "rtsp_url": "rtsp://admin:senha@192.168.15.10:554/cam/realmonitor?channel=1&subtype=0" }
```

Regras de segurança:
- Endpoint aceita apenas `rtsp://` e `rtsps://` — rejeitar outros esquemas com `400`.
- Nunca logar `rtsp_url` em texto plano; usar `mask_rtsp_url()` existente em `cameras.py`.

**Response — sucesso**
```json
{
  "ok": true,
  "method": "rtsp_probe",
  "latency_ms": 142
}
```

**Response — falha**
```json
{
  "ok": false,
  "reason_code": "auth_failed",
  "detail": "credencial invalida (HTTP 401)"
}
```

**Tabela de `reason_code`**

| `reason_code` | Condição | Mensagem interna mapeada |
|---------------|----------|--------------------------|
| `auth_failed` | `unauthorized` em `health.error` | "RTSP401 credencial invalida" |
| `timeout` | `timeout` em `health.error` | "RTSPTO timeout..." |
| `port_closed` | `connection refused` em `health.error` | — |
| `path_invalid` | path não respondeu mas porta aberta | — |
| `unknown` | qualquer outro erro | — |

**HTTP status codes**
- `200` sempre (sucesso ou falha lógica) — o `ok` no body indica o resultado
- `400` se `rtsp_url` ausente ou esquema inválido
- `404` se rota não reconhecida (padrão atual mantido)

---

### 2.2 `GET /onboarding/snapshot?rtsp_url=<encoded_url>`

O frontend envia `rtsp_url` como query param após um probe bem-sucedido. O endpoint atual ignora esse parâmetro e reconstrói URLs a partir de `ip/user/password/channel`.

**Mudança**: se `rtsp_url` estiver presente no query, usá-lo como primeira URL na lista de tentativas antes do fallback por `ip/channel`.

```python
rtsp_url_override = (query.get("rtsp_url") or [""])[0]
if rtsp_url_override:
    rtsp_urls = [rtsp_url_override, *rtsp_urls_from_params]
else:
    rtsp_urls = rtsp_urls_from_params
```

---

### 2.3 Atualização do `/health` — capabilities

Adicionar `test_rtsp: True` no bloco `capabilities` ao implementar o endpoint.

```json
{
  "capabilities": {
    "onboarding_blueprint": true,
    "onboarding_readiness": true,
    "onboarding_installation_check": true,
    "streaming_hls": true,
    "test_rtsp": true
  }
}
```

---

## 3. Implementação — alterações por arquivo

### 3.1 `src/dalevision_edge_agent/rtsp_test.py`

Adicionar função `test_rtsp_by_url` que aceita uma URL completa (sem construção de template).

```python
def test_rtsp_by_url(
    *,
    rtsp_url: str,
    timeout_seconds: int,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Testa conectividade RTSP dado um rtsp_url completo.
    
    Retorna contrato canônico:
      ok=True  → { ok, method, latency_ms }
      ok=False → { ok, reason_code, detail }
    """
    import time
    safe_url = mask_rtsp_url(rtsp_url)
    logger.info("RTSPTEST (by_url) tentando %s", safe_url)

    start = time.monotonic()
    health = check_camera_health(
        {"ip": rtsp_url},  # ip field usado apenas para log interno
        perform_describe=True,
        rtsp_url_override=rtsp_url,
        timeout_seconds=timeout_seconds,
    )
    # Retry sem describe para NVRs com Digest challenge
    error = str(health.get("error") or "")
    if health.get("status") not in {"online", "degraded"} and "unauthorized" in error:
        fallback = check_camera_health(
            {"ip": rtsp_url},
            perform_describe=False,
            rtsp_url_override=rtsp_url,
            timeout_seconds=timeout_seconds,
        )
        if fallback.get("status") in {"online", "degraded"}:
            health = fallback

    latency_ms = round((time.monotonic() - start) * 1000)

    if health.get("status") not in {"online", "degraded"}:
        reason_code = _classify_reason_code(str(health.get("error") or ""))
        logger.info("RTSPTEST (by_url) falhou: %s", reason_code)
        return {
            "ok": False,
            "reason_code": reason_code,
            "detail": _redact_detail(str(health.get("error") or "")),
        }

    logger.info("RTSPTEST (by_url) ok em %dms", latency_ms)
    return {
        "ok": True,
        "method": "rtsp_probe",
        "latency_ms": latency_ms,
    }


def _classify_reason_code(error: str) -> str:
    e = error.lower()
    if "unauthorized" in e or "401" in e or "auth" in e or "forbidden" in e:
        return "auth_failed"
    if "timeout" in e or "timed out" in e:
        return "timeout"
    if "connection refused" in e or "port" in e:
        return "port_closed"
    if "path" in e or "404" in e or "not found" in e:
        return "path_invalid"
    return "unknown"


def _redact_detail(error: str) -> str:
    return re.sub(r"(rtsp://[^:/\s]+:)[^@\s]+@", r"\1***@", error)
```

Importar `re` no topo do arquivo (já tem `ipaddress`, `logging`).

---

### 3.2 `src/dalevision_edge_agent/setup_api.py`

**Passo 1** — Adicionar rota POST no `build_setup_api_response`

A função `build_setup_api_response` atualmente não recebe `method` nem `body`. Precisamos suportar POST. Duas opções:

**Opção A (menor diff)**: adicionar parâmetros `method: str = "GET"` e `body: bytes | None = None` à assinatura de `build_setup_api_response` e tratar a rota POST dentro dela.

**Opção B**: separar em `build_setup_api_post_response` chamado pelo `do_POST`.

Recomendação: **Opção A** — menor superfície de mudança.

```python
def build_setup_api_response(
    *,
    path: str,
    discovery_provider: DiscoveryProvider,
    on_discovery_result: Optional[DiscoveryTelemetryHook] = None,
    method: str = "GET",
    body: Optional[bytes] = None,
) -> tuple[int, dict[str, Any]]:
    ...
    # Adicionar ANTES do bloco if route == "/health":
    if method == "POST" and route == "/onboarding/test-rtsp":
        import json as _json
        from .rtsp_test import test_rtsp_by_url
        try:
            payload_in = _json.loads(body or b"{}") if body else {}
        except Exception:
            payload_in = {}
        rtsp_url = str(payload_in.get("rtsp_url") or "").strip()
        if not rtsp_url or not rtsp_url.startswith(("rtsp://", "rtsps://")):
            return 400, {"ok": False, "error": "rtsp_url_required"}
        import logging as _logging
        _logger = _logging.getLogger("setup_api.test_rtsp")
        result = test_rtsp_by_url(
            rtsp_url=rtsp_url,
            timeout_seconds=6,
            logger=_logger,
        )
        return 200, result
```

**Passo 2** — Adicionar `do_POST` no `Handler`

```python
def do_POST(self):  # noqa: N802
    content_length = int(self.headers.get("Content-Length") or 0)
    body = self.rfile.read(content_length) if content_length > 0 else None
    code, payload = build_setup_api_response(
        path=self.path,
        discovery_provider=discovery_provider,
        on_discovery_result=on_discovery_result,
        method="POST",
        body=body,
    )
    self._write_json(code, payload)
```

**Passo 3** — Atualizar `/onboarding/snapshot` para aceitar `rtsp_url`

Na rota `/onboarding/snapshot` (linha ~343), antes de montar `rtsp_urls`:

```python
rtsp_url_override = (query.get("rtsp_url") or [""])[0].strip()
rtsp_urls_default = [
    f"rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=1",
    f"rtsp://{user}:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0",
]
rtsp_urls = ([rtsp_url_override] + rtsp_urls_default) if rtsp_url_override else rtsp_urls_default
```

**Passo 4** — Atualizar capabilities no `/health`

```python
"capabilities": {
    "onboarding_blueprint": True,
    "onboarding_readiness": True,
    "onboarding_installation_check": True,
    "streaming_hls": True,
    "test_rtsp": True,
},
```

---

## 4. Matriz de testes

Arquivo a criar: `tests/test_setup_api_test_rtsp.py`

### Cenários obrigatórios

| # | Cenário | Input | `ok` esperado | `reason_code` esperado |
|---|---------|-------|---------------|------------------------|
| T1 | RTSP válido respondendo | `rtsp://admin:pass@192.168.0.10:554/...` → health `online` | `True` | — |
| T2 | Credencial inválida (401) | health retorna `unauthorized` | `False` | `auth_failed` |
| T3 | Porta fechada | health retorna `connection refused` | `False` | `port_closed` |
| T4 | Timeout | health retorna `timeout` | `False` | `timeout` |
| T5 | Digest challenge + fallback | primeiro `perform_describe=True` → `unauthorized`, segundo `False` → `online` | `True` | — |
| T6 | Body ausente | body `{}` | `400` HTTP, `rtsp_url_required` | — |
| T7 | Esquema não-RTSP | `http://192.168.0.1` | `400` HTTP, `rtsp_url_required` | — |
| T8 | Credencial sanitizada no detail | error contém `rtsp://user:segredo@ip` | `False` | detail NÃO contém `segredo` |
| T9 | `GET /health` anuncia `test_rtsp: True` | — | `True` | — |
| T10 | `/onboarding/snapshot?rtsp_url=` usa URL fornecida primeiro | rtsp_url fornecida + ip/channel | — | snapshot chamado com rtsp_url |

### Padrão de mock (seguir `test_rtsp_test_fallback.py`)

```python
def test_post_test_rtsp_success(monkeypatch):
    def fake_health(*_args, **kwargs):
        return {"status": "online", "latency_ms": 80, "error": None}
    monkeypatch.setattr("dalevision_edge_agent.rtsp_test.check_camera_health", fake_health)
    monkeypatch.setattr("dalevision_edge_agent.rtsp_test.capture_snapshot_if_possible", lambda **_: {})

    code, payload = build_setup_api_response(
        path="/onboarding/test-rtsp",
        discovery_provider=lambda: [],
        method="POST",
        body=b'{"rtsp_url": "rtsp://admin:pass@192.168.0.10:554/cam/realmonitor?channel=1&subtype=0"}',
    )
    assert code == 200
    assert payload["ok"] is True
    assert payload["method"] == "rtsp_probe"
    assert "latency_ms" in payload
```

---

## 5. Definição de pronto (DoD)

- [ ] `test_rtsp_by_url` implementada em `rtsp_test.py`
- [ ] `do_POST` adicionado ao `Handler` em `setup_api.py`
- [ ] Rota `POST /onboarding/test-rtsp` retorna contrato canônico
- [ ] `/onboarding/snapshot` aceita `rtsp_url` como param primário
- [ ] `/health` anuncia `capabilities.test_rtsp: true`
- [ ] Todos os 10 cenários de teste passando
- [ ] Credenciais RTSP não aparecem em logs ou em `detail` da resposta
- [ ] Frontend cai no fluxo de sucesso por template (sem fallback legado 404/405)

---

## 6. Dependências e ordem de execução

```
rtsp_test.py (test_rtsp_by_url) → setup_api.py (rota POST + snapshot param) → testes
```

Pode ser implementado em 1 PR. Não há dependência de backend cloud.

---

## 7. Referências

- Frontend: `frontend/src/components/StoreActivationWizard.tsx` — `runManualRtspProbe()` (linha ~910)
- Frontend: `loadLocalPreview()` com `options.rtspUrl` (linha ~851)
- Spec produto: `docs/PRODUCT_BLUEPRINT_V1_PILOT_TO_10_CUSTOMERS.md` § 17.9 `EDGE-SETUP-001`
- Spec onboarding: `specs/EDGE-SYSTEM-003-onboarding-frictionless.md`
- Teste de referência: `tests/test_rtsp_test_fallback.py`
