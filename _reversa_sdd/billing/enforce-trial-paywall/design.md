# enforce-trial-paywall - Design

## Camadas

- 🟢 `billing.utils`: paywall por quantidade de stores no trial.
- 🟢 `cameras.limits`: paywall por quantidade de câmeras conforme plano.
- 🟢 `backend.utils.entitlements`: bloqueio por trial expirado.

## Semântica de Erros

- 🟢 Quantidade excedida usa `PAYWALL_TRIAL_LIMIT`.
- 🟢 Trial vencido usa `TRIAL_EXPIRED`.
- 🟢 Ambos usam HTTP 402.

## Auditoria

- 🟢 `paywall_blocked` registra entity, limit e code.
- 🟢 `trial_expired_blocked` registra action e endpoint.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\billing\utils.py`.
- 🟢 `C:\workspace\dale-vision\backend\utils\entitlements.py`.
