# edge-agent-update-installation - Contracts

## Endpoint: GET /api/edge/update-policy/

### Consumidor

- 🟢 `src/dalevision_edge_agent/update.py` no agente local.

### Autenticação

- 🟢 Usa `edge_token` configurado localmente.
- 🟡 O formato exato do header pertence à camada de cliente edge já documentada em units de runtime/activation.

### Resposta esperada

```json
{
  "target_version": "vX.Y.Z",
  "channel": "stable",
  "current_min_supported": "vA.B.C",
  "package": {
    "url": "https://example.com/dalevision-edge-agent-windows.zip",
    "sha256": "hex-sha256"
  },
  "rollout_window": {
    "start_local": "02:00",
    "end_local": "05:00",
    "timezone": "America/Sao_Paulo"
  },
  "health_gate": {
    "max_boot_seconds": 120,
    "require_heartbeat_seconds": 180,
    "require_camera_health_count": 3
  }
}
```

### Compatibilidade de campos

- 🟢 `target_version` pode ser substituído por `version`.
- 🟢 `package.url` pode ser substituído por `url`.
- 🟢 `package.sha256` pode ser substituído por `sha256`.
- 🟢 `channel` ausente assume `stable`.

### Erros tratados localmente

- 🟢 Payload inválido: `UPD002`.
- 🟢 Versão atual abaixo do mínimo: `UPD015`.
- 🟢 Fora da janela de rollout: `UPD016`.
- 🟢 Auto-update desabilitado: `UPD011`.

## Endpoint: POST /api/edge/update-report/

### Consumidor

- 🟢 `send_update_report` em `src/dalevision_edge_agent/update.py`.

### Semântica

- 🟢 O endpoint recebe eventos de update em fases.
- 🟢 O agente deve enviar idempotency key estável.
- 🟢 O backend persiste em `EdgeUpdateEvent` com constraint única para deduplicação.

### Payload lógico

```json
{
  "event": "edge_update_verified",
  "phase": "checksum",
  "status": "verified",
  "target_version": "vX.Y.Z",
  "current_version": "vA.B.C",
  "idempotency_key": "stable-key-without-timestamp",
  "message": "optional diagnostic text"
}
```

### Fases conhecidas

- 🟢 `policy_check`.
- 🟢 `download`.
- 🟢 `checksum`.
- 🟢 `activation`.

### Status conhecidos

- 🟢 `started`.
- 🟢 `downloaded`.
- 🟢 `verified`.
- 🟢 `activated`.
- 🟢 `failed`.

### Eventos conhecidos

- 🟢 `edge_update_started`.
- 🟢 `edge_update_downloaded`.
- 🟢 `edge_update_verified`.
- 🟢 `edge_update_activated`.
- 🟢 `edge_update_failed`.

## Modelo: EdgeUpdatePolicy

- 🟢 `store_id`: único por loja.
- 🟢 `channel`: `stable` ou `canary`.
- 🟢 `target_version`.
- 🟢 `current_min_supported`.
- 🟢 `rollout_start_local`: default `02:00`.
- 🟢 `rollout_end_local`: default `05:00`.
- 🟢 `health_max_boot_seconds`: default `120`.
- 🟢 `health_require_heartbeat_seconds`: default `180`.
- 🟢 `health_require_camera_health_count`: default `3`.
- 🟢 `rollback_enabled`.
- 🟢 `rollback_max_failed_attempts`.
- 🟢 `active`.
- 🟢 Tabela: `edge_update_policies`.

## Modelo: EdgeUpdateEvent

- 🟢 Tabela: `edge_update_events`.
- 🟢 Índice por store/timestamp.
- 🟢 Constraint única: `edge_update_event_store_idemp_uniq`.
- 🟢 Função: deduplicar reports por idempotency key.

## Modelo: EdgeRelease

- 🟢 `channel`: `stable` ou `canary`.
- 🟢 `current_version`.
- 🟢 `minimum_supported_version`.
- 🟢 `download_url`.
- 🟢 `package_sha256`.
- 🟢 `package_size_bytes`.
- 🟢 `release_notes`.
- 🟢 `is_active`.
- 🟢 Tabela: `edge_releases`.

## Endpoint: Edge Release Latest

- 🟢 View: `EdgeReleaseLatestView`.
- 🟢 Público, sem autenticação.
- 🟢 Canal aceito: `stable` ou `canary`, com fallback para `stable`.
- 🟢 Retorna método `edge_release_latest` quando vem do banco.
- 🟢 Retorna método `v1-fallback` quando vem de settings.

## Endpoint: Edge Release Management

- 🟢 View: `EdgeReleaseManagementView`.
- 🟢 Requer autenticação.
- 🟢 Valida `version`.
- 🟢 Valida `download_url`.
- 🟢 Valida canal `stable`/`canary`.
- 🟢 Usa `update_or_create`.
- 🟢 Desativa releases anteriores ativos do mesmo canal.
- 🟢 Retorna método `edge_release_upsert`.

## Contrato do ZIP Windows

- 🟢 Nome final: `dalevision-edge-agent-windows.zip`.
- 🟢 Raiz staging: `release/win`.
- 🟢 Deve conter `dalevision-edge-agent.exe`.
- 🟢 Deve conter `yolov8n.pt`.
- 🟢 Deve conter `.env` derivado de `.env.template`.
- 🟢 Deve conter `Start_DaleVision_Agent.bat` e `Start_DaleVision_Agent.ps1`.
- 🟢 Deve conter scripts de instalar, verificar, diagnosticar, parar, atualizar e remover autostart.
