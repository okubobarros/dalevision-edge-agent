# Maquinas de Estado - DaleVision

Gerado em: 2026-05-06T20:09:09.572994Z

## AgentState

Valores: unprovisioned, activating, active, degraded, error.

```mermaid
stateDiagram-v2
  [*] --> unprovisioned
  unprovisioned --> activating: activation_token presente
  unprovisioned --> unprovisioned: token ausente
  activating --> active: activation_success
  activating --> activating: network_error ou erro retryable
  activating --> error: 401/403/409 ou cloud ausente
  active --> degraded: heartbeat falha por rede
  degraded --> active: heartbeat ok
  active --> error: heartbeat 401/403
  degraded --> error: heartbeat 401/403
```

Confianca: 🟢 CONFIRMADO por activation.py e tests/test_heartbeat_state.py.

## EdgeDevice

Valores: registered, active, retired.

```mermaid
stateDiagram-v2
  [*] --> registered: device criado/registrado
  registered --> active: primeiro uso/ativacao bem-sucedida
  active --> active: heartbeat/update de last_seen
  active --> retired: revoke device
  registered --> retired: revoke antes de uso
  retired --> [*]
```

Confianca: 🟢 CONFIRMADO por EdgeDevice e StoreEdgeDeviceRevokeView; 🟡 INFERIDO para transicao registered->active quando touch/activation registry atualiza status.

## ActivationToken

Valores derivados: active_unused, used, expired, inactive.

```mermaid
stateDiagram-v2
  [*] --> active_unused: issue_activation_token
  active_unused --> used: activate_edge_device ok
  active_unused --> expired: now > expires_at
  active_unused --> inactive: revogacao/rotacao
  used --> [*]
  expired --> [*]
  inactive --> [*]
```

Confianca: 🟢 CONFIRMADO por StoreActivationTokenView e modelos; 🟡 INFERIDO para inactive por rotacao/revogacao.

## Store

Valores: active, inactive, trial, blocked.

```mermaid
stateDiagram-v2
  [*] --> trial: criacao inicial/piloto
  trial --> active: assinatura/conversao
  trial --> blocked: trial_expired ou bloqueio operacional
  active --> blocked: subscription_inactive, edge_disabled, store_suspended, security_revoked
  blocked --> active: desbloqueio administrativo
  active --> inactive: desativacao operacional
  inactive --> active: reativacao
```

Confianca: 🟢 CONFIRMADO para valores e bloqueios; 🟡 INFERIDO para transicoes comerciais completas.

## Camera

Valores: online, degraded, offline, unknown, error.

```mermaid
stateDiagram-v2
  [*] --> unknown
  unknown --> online: health recente ok
  unknown --> offline: sem sinal/erro
  online --> degraded: latencia alta ou stale heartbeat
  degraded --> online: health ok recente
  online --> offline: health expirado ou falha RTSP
  degraded --> offline: health expirado
  offline --> online: novo health ok
  offline --> error: erro de validacao/probe
  error --> online: teste posterior ok
```

Confianca: 🟢 CONFIRMADO por CAMERA_STATUS, cameras.py e views_edge_status.py.

## DetectionEvent

Valores: open, resolved, ignored.

```mermaid
stateDiagram-v2
  [*] --> open: evento detectado
  open --> resolved: resolve()
  open --> ignored: ignore()
  resolved --> [*]
  ignored --> [*]
```

Confianca: 🟢 CONFIRMADO por EVENT_STATUS e apps/alerts/views.py.

## Subscription

Valores: trialing, active, past_due, canceled, incomplete, blocked.

```mermaid
stateDiagram-v2
  [*] --> trialing
  trialing --> active: pagamento/assinatura ativa
  active --> past_due: falha de cobranca
  past_due --> active: pagamento recuperado
  active --> canceled: cancelamento
  active --> blocked: bloqueio administrativo
  incomplete --> active: checkout concluido
```

Confianca: 🟢 CONFIRMADO para valores; 🟡 INFERIDO para gatilhos.

## ActionOutcome

Valores: dispatched, completed, failed, canceled. Resultado: resolved, partial, not_resolved.

```mermaid
stateDiagram-v2
  [*] --> dispatched
  dispatched --> completed: callback/outcome positivo
  dispatched --> failed: erro entrega/execucao
  dispatched --> canceled: cancelamento
  completed --> resolved
  completed --> partial
  completed --> not_resolved
```

Confianca: 🟢 CONFIRMADO por apps/copilot/models.py; 🟡 INFERIDO para gatilhos exatos.

## EdgeUpdateEvent

Valores de status aparecem como started/healthy/failed/rolled_back e fases como policy/download/apply/health_check.

```mermaid
stateDiagram-v2
  [*] --> started: update iniciado
  started --> healthy: health gate passou
  started --> failed: download/apply/health gate falhou
  failed --> rolled_back: rollback executado
  healthy --> [*]
  rolled_back --> [*]
```

Confianca: 🟢 CONFIRMADO por update.py, views_update.py e commits; 🟡 INFERIDO para taxonomia completa de status/fase.
