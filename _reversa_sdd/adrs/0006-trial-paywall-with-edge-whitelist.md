# ADR 0006-trial-paywall-with-edge-whitelist: Trial/paywall com whitelist operacional edge

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

Assinatura deve bloquear uso comercial, mas nao pode impedir ingestao/health que suporte diagnostico e retomada.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Middleware bloqueia endpoints /api com 402 quando trial expirado, mas whitelista /api/edge e health/setup/status essenciais.

## Alternativas consideradas

- Bloquear tudo apos trial
- Nao bloquear nada no backend
- Bloquear somente frontend

## Consequencias

- Evita perder sinais tecnicos do cliente
- UI recebe codigo TRIAL_EXPIRED consistente
- Requer cuidado para nao deixar funcionalidades pagas expostas pela whitelist

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
