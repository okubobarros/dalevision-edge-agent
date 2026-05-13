# agregar-estatisticas-minuto - Design

## Algoritmo

1. 🟢 `_floor_minute` recebe timestamp.
2. 🟢 Remove segundos e microssegundos.
3. 🟢 `_bump_event_minute` chama `EdgeEventMinuteStats.objects.get_or_create`.
4. 🟢 Se criou, grava `count=1`.
5. 🟢 Se já existia, atualiza com `F("count") + 1`.
6. 🟢 Atualiza `last_event_at` e `updated_at`.

## Posição no Pipeline

- 🟢 A agregação roda após o receipt.
- 🟢 Também roda em evento deduplicado, em bloco best-effort.
- 🟢 Falha na agregação não muda resposta da ingestão.

## Retenção

- 🟢 Comando `prune_edge_event_minute_stats` calcula cutoff por dias.
- 🟢 Default vem de settings/env `EDGE_EVENT_MINUTE_RETENTION_DAYS` ou `7`.
- 🟢 Valor é limitado entre 1 e 365.
- 🟢 `--dry-run` apenas informa quantidade.

## Trade-offs

- 🟢 `get_or_create` é simples e correto para baixa/média frequência.
- 🟡 Comentário no código reconhece custo de `get_or_create` em alta frequência.
- 🟡 Agregação local no agente é citada como possível futuro, mas não implementada.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\management\commands\prune_edge_event_minute_stats.py`.
