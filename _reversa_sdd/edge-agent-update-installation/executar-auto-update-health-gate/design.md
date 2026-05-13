# executar-auto-update-health-gate - Design

## Visão Geral

- 🟢 O auto-update é executado pelo loop principal do agente, não por um serviço separado documentado nesta unit.
- 🟢 A decisão vem da policy cloud; a segurança operacional vem de lock, checksum, backup e health gate.
- 🟢 Reports estruturados permitem acompanhar progresso e falhas no backend.

## Sequência Operacional

1. 🟢 `main.py` chama `check_for_update`.
2. 🟢 `update.py` resolve endpoint `/api/edge/update-policy/` ou fallback.
3. 🟢 A policy é validada.
4. 🟢 O agente decide se update está bloqueado ou disponível.
5. 🟢 `main.py` adquire lock com `acquire_update_lock`.
6. 🟢 `main.py` chama `send_update_report` para `started`.
7. 🟢 `main.py` chama `download_update`.
8. 🟢 `download_update` valida SHA-256 e pacote.
9. 🟢 `main.py` reporta `downloaded` e `verified`.
10. 🟢 `main.py` chama `apply_update_if_possible`.
11. 🟢 `main.py` executa `_run_post_update_health_gate`.
12. 🟢 Sucesso reporta `activated`.
13. 🟢 Falha chama `_rollback_update_if_needed` e reporta `failed`.
14. 🟢 `main.py` libera lock.

## Health Gate

- 🟢 Defaults: boot máximo 120 segundos, heartbeat obrigatório em 180 segundos, camera health count 3.
- 🟢 Heartbeat é o sinal confirmado para aprovação ou falha.
- 🟡 Camera health count aparece na policy e no contrato, mas a análise indica tratamento como pendência/observabilidade, não necessariamente bloqueio rígido.

## Idempotência

- 🟢 A chave de idempotência é construída sem timestamp.
- 🟢 A mesma fase/status/versão deve gerar chave estável.
- 🟢 O backend impõe unicidade por constraint em `EdgeUpdateEvent`.

## Erros e Recuperação

- 🟢 Erros antes de ativação não devem alterar executável atual.
- 🟢 Erro de checksum remove artefato baixado.
- 🟢 Erro pós-ativação tenta rollback quando backup existe.
- 🟢 Falha de report não deve vazar segredo em log.

## Rastreabilidade

- 🟢 `src/dalevision_edge_agent/main.py`.
- 🟢 `src/dalevision_edge_agent/update.py`.
- 🟢 `_reversa_sdd/adrs/0003-edge-update-policy-health-gate.md`.
