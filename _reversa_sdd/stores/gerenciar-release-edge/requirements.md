# gerenciar-release-edge - Requirements

## Escopo

- 🟢 Caso de uso de release, policy, trigger, observabilidade e canary de update edge.
- 🟢 Fontes: `views_activation.py`, `views_edge_update_*`, `views_canary.py`.

## Requisitos

- 🟢 Latest release deve ser público por canal.
- 🟢 Management de release deve exigir staff/superuser.
- 🟢 Release ativa deve desativar anteriores do mesmo canal.
- 🟢 Policy por loja deve exigir versão alvo, URL e SHA.
- 🟢 Trigger deve escolher release por canal e criar/atualizar policy.
- 🟢 Trigger deve registrar evento `edge_update_requested`.
- 🟢 Status deve calcular version gap e update health.
- 🟢 Events list deve filtrar por status/agent/limit.
- 🟢 Attempts deve agrupar eventos por tentativa.
- 🟢 Runbook deve mapear reason_code para ações.
- 🟢 Network summary deve restringir lojas pelas orgs do usuário.
- 🟢 Canary deve selecionar percentual, medir saúde e permitir rollback para stable.

## Critérios de Aceitação

- 🟢 Staff cria release e latest retorna a versão.
- 🟢 Gestor aplica policy com SHA e agente passa a receber target version.
- 🟢 Trigger sem SHA retorna `package_sha256_missing`.
- 🟢 Rollout summary mostra lojas críticas quando há failed/rollback/in_progress.
- 🟢 Canary rollback cria eventos `canary_rollback_requested`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_management.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_attempts.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_network.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_canary.py`.
