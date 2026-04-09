# EDGE-SYSTEM-002 — Edge Update Flow

> Protocolo de automação de ciclo de vida do agente para garantir paridade com a nuvem e segurança de deployment.

## Meta
- Título / ID: `EDGE-SYSTEM-002 - Update Flow`
- Objetivo: Prover mecanismo de atualização segura, atômica e auditável para o Edge Agent.
- Estado: `approved`
- Última atualização: `2026-04-05`

## 1. Escopo
- **Dentro**: Consulta de políticas (Policy Pull), Download de pacotes (HTTP), Verificação de Integridade (SHA256), Swap Atômico, Report de Fases.
- **Fora**: Decisão de qual versão disparar (Backend-driven), Orquestração de canary em nível de rede (Layer Cloud).

## 2. Compatibilidade
- Agente versão `>= 1.0.0`.
- Protocolo `AUTO_UPDATE_V1`.
- API Cloud: `/api/edge/update-policy/`, `/api/edge/update-report/`.

## 3. Fluxo e Estados
1.  **Check**: Consulta `GET /api/edge/update-policy/` com `current_version`.
2.  **Downloading**: Se `target_version` > atual, inicia download.
3.  **Verifying**: Calcula checksum e compara com `package.sha256`.
4.  **Activating**: Substitui binários (apenas fora de `SERVICE_MODE`).
5.  **Healthy/Failed**: Reinicia e envia report final de sucesso ou falha.

## 4. APIs / Contratos
- `GET /api/edge/update-policy/`: Retorna `target_version`, `channel`, `rollout_window`, `package_url`, `sha256`.
- `POST /api/edge/update-report/`: Envia `event_id`, `status` (`started`, `downloaded`, `verified`, `activated`, `healthy`, `failed`).

## 5. Configurações / Flags
- `AUTO_UPDATE_ENABLED`: Habilita/desabilita o fluxo.
- `UPDATE_INTERVAL_SECONDS`: Periodicidade da checagem (Default 3600s).
- `SERVICE_MODE`: Se `True`, bloqueia o swap automático (Modo Manual/Debug).

## 6. Observabilidade
- **Eventos**: Logs detalhados em `logs/update.log`.
- **Métricas**: `agent.update.success`, `agent.update.failed`, `agent.update.duration`.

## 7. Operação em campo
- **Rollback**: Mantém backup da versão anterior; se falhar no boot, volta automático.
- **Evidências**: `doctor --share` inclui o histórico de updates.

## 8. Riscos e Fallback
- **Disco Cheio**: Cancela download e limpa `/tmp/` de updates.
- **Rede Instável**: Suporte a downloads parciais/retries no próximo ciclo.

## 9. Critérios de Pronto
- Agente atualiza com sucesso em teste de laboratório.
- Checksum falho gera erro e impede ativação.
- Report de fases chega corretamente no backend.
