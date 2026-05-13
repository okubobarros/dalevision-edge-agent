# Dicionario de Dados - DaleVision

Gerado em: 2026-05-06T19:58:05.001354Z

| Entidade | Origem | Campos principais | Observacoes |
|---|---|---|---|
| Organization | apps/core/models.py | id, name, segment, country, timezone, trial_ends_at | CONFIRMADO multi-tenant org. |
| OrgMember | apps/core/models.py | org, user_id, role | CONFIRMADO roles owner/admin/manager/viewer. |
| Store | apps/core/models.py | org, name, business_type, pos_system, avg_ticket, status, last_seen_at | CONFIRMADO loja monitorada. |
| StoreZone | apps/core/models.py | store, name, zone_type, is_critical | CONFIRMADO zonas para cameras/eventos. |
| Camera | apps/core/models.py | store, zone, external_id, ip, rtsp_url, username, password, indicators, status, last_snapshot_url | CONFIRMADO senha deve ser mascarada. |
| CameraHealthLog | apps/core/models.py | camera, checked_at, status, latency_ms, snapshot_url, error | CONFIRMADO historico de health. |
| CameraROIConfig | apps/cameras/models.py | camera, version, config_json, updated_at, updated_by | CONFIRMADO ROI versionado. |
| CameraSnapshot | apps/cameras/models.py | camera, snapshot_url, storage_key, captured_at, metadata | CONFIRMADO snapshot UI/ROI. |
| Employee | apps/core/models.py | store, full_name, email, whatsapp, role, active | CONFIRMADO equipe. |
| DetectionEvent | apps/core/models.py | org, store, camera, zone, type, severity, status, occurred_at, metadata | CONFIRMADO evento/alerta. |
| AlertRule | apps/core/models.py | store, zone, type, threshold, cooldown_minutes, channels | CONFIRMADO regra alerta. |
| NotificationLog | apps/core/models.py | org, store, event, channel, status, sent_at | CONFIRMADO auditoria notificacao. |
| OnboardingProgress | apps/core/models.py | org, store, step, completed, status, progress_percent, meta | CONFIRMADO progresso setup. |
| LgpdAcceptance | apps/core/models.py | org, store, user, term_version, legal_basis_ack, operator_role_ack, permitted_use_ack | CONFIRMADO aceite LGPD. |
| Subscription | apps/core/models.py | org, plan_code, status, current_period_* | CONFIRMADO billing/paywall. |
| EdgeDevice | apps/edge/models.py | store_id, device_key, installed_version, update_channel, status, last_seen_at | CONFIRMADO identidade agente. |
| ActivationToken | apps/edge/models.py | store_id, token_hash, token_hint, edge_device, expires_at, used_at, is_active | CONFIRMADO bootstrap edge. |
| EdgeRelease | apps/edge/models.py | channel, current_version, minimum_supported_version, download_url, package_sha256 | CONFIRMADO release. |
| EdgeUpdatePolicy | apps/edge/models.py | store_id, target_version, rollout_window, package, health_gate, rollback | CONFIRMADO update policy. |
| EdgeUpdateEvent | apps/edge/models.py | store_id, agent_id, from_version, to_version, status, phase, event, attempt, idempotency_key | CONFIRMADO update report. |
| EdgeEventRaw | apps/edge/models.py | event_id, event_type, global_id, store_id, camera_id, occurred_at, payload | CONFIRMADO evento bruto. |
| StoreDailyMetrics | apps/analytics/models.py | store, date, footfall_in, queue_avg_wait_min, staff_idle_minutes, revenue_estimated | CONFIRMADO agregado diario. |
| OnboardingEvent | apps/analytics/models.py | store, event_type, step, technical_status, session_id, metadata | CONFIRMADO telemetria onboarding. |
| AgentEvent | apps/analytics/models.py | store, device, event_type, from_version, to_version, metadata | CONFIRMADO telemetria agente. |
| CopilotOperationalInsight | apps/copilot/models.py | org_id, store_id, category, severity, evidence_json, actions_json, confidence | CONFIRMADO insight. |
| OperationalWindowHourly | apps/copilot/models.py | org_id, store_id, ts_bucket, metrics_json, confidence_score | CONFIRMADO janela horaria. |
| ActionOutcome | apps/copilot/models.py | org_id, store_id, insight_id, action_type, status, outcome_json, impact_* | CONFIRMADO resultado acao. |
| ValueLedgerDaily | apps/copilot/models.py | org_id, store_id, ledger_date, value_recovered_brl, value_at_risk_brl | CONFIRMADO ledger valor. |

## Payloads principais

| Payload | Origem | Campos | Observacoes |
|---|---|---|---|
| HeartbeatPayload | edge-agent heartbeat_client.py | device_key, installed_version, update_channel, status, uptime_seconds, cameras_connected, inference_fps | Enviado como extra_data de edge_heartbeat. |
| Camera health event | edge-agent cameras.py | camera_id, store_id, agent_id, status, latency_ms, error, snapshot_* | Publicado como camera_health. |
| Update policy | apps/edge/views_update.py | target_version, current_min_supported, rollout_window, package, health_gate, rollback_policy | Consumido pelo agente. |
| Update report | apps/edge/serializers.py + views_update.py | event, status, phase, attempt, versions, reason_code, idempotency_key | Deduplicado por loja/chave. |
| Frontend API config | frontend/src/services/api.ts | timeoutCategory, noRetry, auth header, retry counters | Controla resiliencia client-side. |
