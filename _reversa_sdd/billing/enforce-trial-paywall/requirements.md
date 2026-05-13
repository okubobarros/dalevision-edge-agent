# enforce-trial-paywall - Requirements

## Escopo

- 🟢 Caso de uso de enforcement de trial/paywall em stores, cameras e produto.

## Requisitos

- 🟢 Trial expirado deve bloquear ações protegidas com `TRIAL_EXPIRED`.
- 🟢 Limite de store trial deve bloquear a segunda loja.
- 🟢 Limite de câmera deve bloquear acima do limite do plano.
- 🟢 Bloqueios devem criar audit logs.
- 🟢 Staff/superuser devem bypassar.
- 🟢 Falhas de schema trial devem ser toleradas.
- 🟢 Câmera inativa não deve consumir limite.

## Critérios de Aceitação

- 🟢 Org trial com uma store não consegue criar outra store.
- 🟢 Org start com 3 câmeras ativas não consegue criar quarta ativa.
- 🟢 Org com subscription ativa não é bloqueada por trial expirado.
- 🟢 Staff consegue executar ações mesmo em trial expirado.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\utils.py`.
- 🟢 `C:\workspace\dale-vision\backend\utils\entitlements.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\limits.py`.
