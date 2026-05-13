# agregar-estatisticas-minuto - Requirements

## Escopo

- 🟢 Caso de uso de agregação leve por minuto dos eventos edge.
- 🟢 Fontes: `C:\workspace\dale-vision\apps\edge\views.py`, `apps\edge\models.py`, `apps\edge\management\commands\prune_edge_event_minute_stats.py`.

## Requisitos

- 🟢 Calcular `minute_bucket` truncando segundos e microssegundos do timestamp do evento.
- 🟢 Criar linha `EdgeEventMinuteStats` quando não existir.
- 🟢 Incrementar `count` quando a linha já existir.
- 🟢 Atualizar `last_event_at` e `updated_at`.
- 🟢 Limitar `event_name` a 64 caracteres.
- 🟢 Usar unicidade por `store_id`, `event_name`, `minute_bucket`.
- 🟢 Ignorar silenciosamente em `DatabaseOperationForbidden`.
- 🟢 Logar exceções sem falhar a ingestão.
- 🟢 Permitir pruning por comando com `--days` e `--dry-run`.
- 🟢 Retenção default deve ser `EDGE_EVENT_MINUTE_RETENTION_DAYS` ou 7 dias.

## Critérios de Aceitação

- 🟢 Dado evento novo no minuto, cria contador com `count=1`.
- 🟢 Dado segundo evento no mesmo minuto, incrementa contador.
- 🟢 Dado comando dry-run, reporta candidatos sem apagar.
- 🟢 Dado comando normal, apaga linhas anteriores ao cutoff.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\management\commands\prune_edge_event_minute_stats.py`.
