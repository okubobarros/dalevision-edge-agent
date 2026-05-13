# gerenciar-release-edge - Design

## Release

- 🟢 `EdgeReleaseLatestView` lê release ativa por canal.
- 🟢 Fallback usa settings quando tabela está vazia.
- 🟢 `EdgeReleaseManagementView` faz `update_or_create` por canal/versão e desativa releases anteriores.

## Policy e Trigger

- 🟢 Policy é serializada por `_serialize_policy`.
- 🟢 PUT preserva defaults de rollout/health/rollback.
- 🟢 Trigger resolve device, canal, release e SHA.
- 🟢 Policy final é a fonte que o agente consome via app `edge`.
- 🟢 Evento queued/requested dá observabilidade ao dashboard.

## Observabilidade

- 🟢 Status calcula health por último evento.
- 🟢 Attempts agrupa por `(attempt,to_version,agent_id)`.
- 🟢 Runbook traduz reason_code para checklist acionável.
- 🟢 Network summary agrega por orgs do usuário e limita scan de eventos.

## Canary

- 🟢 Batch seleciona sample aleatória de lojas active/trial.
- 🟢 Health verifica policies canary ativas.
- 🟢 Rollback substitui policies canary por release stable.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_update_management.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_canary.py`.
