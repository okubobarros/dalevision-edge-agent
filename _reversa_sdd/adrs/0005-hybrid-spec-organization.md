# ADR 0005-hybrid-spec-organization: Organizar specs por estrutura hibrida

Data: 2026-05-06T20:09:09.572994Z

## Status

Aceita retroativamente.

## Contexto

O produto cruza dominios Django, endpoints API, frontend SPA e agente local.

Evidencias: historico Git, code-analysis.md, domain.md e arquivos de runtime/backend/frontend.

## Decisao

Gerar specs hibridas: modulos/capacidades na raiz e contratos/casos de uso aninhados quando necessario.

## Alternativas consideradas

- Por modulo puro
- Por endpoint puro
- Por feature solta

## Consequencias

- Preserva contexto tecnico e comportamento ponta-a-ponta
- Exige disciplina no Writer
- Facilita rastrear edge/frontend/backend juntos

## Confianca

🟡 INFERIDO para motivacao historica; 🟢 CONFIRMADO para a decisao implementada no codigo.
