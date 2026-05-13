# ADR 0002-token-activation-single-use: Ativacao por token single-use

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

Clientes precisam instalar agente sem editar .env manualmente e sem expor edge token diretamente no wizard.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Emitir activation_token temporario/single-use que o agente troca por edge_token e device identity.

## Alternativas consideradas

- Entregar edge_token diretamente no frontend
- Provisionamento manual via .env
- OAuth device flow

## Consequencias

- Reduz exposicao de segredo persistente
- Exige backend de ativacao robusto
- Permite revogar device/token por loja

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
