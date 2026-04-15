# Harness Engineering - DaleVision Edge Agent

Este diretorio organiza o minimo essencial do harness para reduzir mudancas aleatorias e manter contexto centralizado.

## Estrutura
- `README.md`: politica de documentacao e ownership.
- `progress.md`: memoria de evolucao continua e friccoes recorrentes.
- `sensors.md`: sinais minimos de feedback (eventos, erros, gates).

## Politica de documentacao (centralizacao)
1. Poucos documentos, com atualizacao continua.
2. Specs principais vivem em `specs/EDGE-SYSTEM-00X-*.md`.
3. Este repositorio documenta apenas o que e do executavel/edge agent.
4. Itens de backend/frontend/banco devem ser documentados no repositorio `C:\workspace\dale-vision`.
5. Evitar criar documentos paralelos quando uma secao em spec existente resolve.

## Regra de uso
1. Toda mudanca relevante deve referenciar uma `EDGE-SYSTEM-00X`.
2. Atualizar `progress.md` semanalmente com status real e proximos passos.
3. Antes de merge/release rodar `scripts/harness_check.ps1`.

## Nao regressao obrigatoria
- Nao quebrar compatibilidade do protocolo atual de heartbeat/camera health.
- Nao logar senha, token ou segredo.
- Manter diagnostico legivel para operador de loja.
