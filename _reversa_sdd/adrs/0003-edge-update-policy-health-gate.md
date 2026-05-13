# ADR 0003-edge-update-policy-health-gate: Auto-update com policy, health gate e rollback

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

Agente em campo precisa atualizar sem operador tecnico e sem quebrar operacao da loja.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Backend publica update-policy; agente valida janela, versao minima, checksum, lock, health gate e reporta resultado.

## Alternativas consideradas

- GitHub releases direto no agente
- Atualizacao manual por suporte
- Update sempre imediato sem janela

## Consequencias

- Mais seguro para lojas em horario comercial
- Aumenta complexidade de estado
- Permite observabilidade de rollout e rollback

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
