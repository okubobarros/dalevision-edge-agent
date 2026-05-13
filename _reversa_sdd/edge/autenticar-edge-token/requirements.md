# autenticar-edge-token - Requirements

## Escopo

- 🟢 Caso de uso de autenticação do agente edge no backend.
- 🟢 Fonte principal: `C:\workspace\dale-vision\apps\edge\auth.py`.

## Requisitos

- 🟢 Extrair token de `X-EDGE-TOKEN`, `X_EDGE_TOKEN`, `HTTP_X_EDGE_TOKEN`, `X-STORE-TOKEN`, `HTTP_X_STORE_TOKEN`, query `edge_token`, `Authorization: Bearer` ou `Authorization: Token`.
- 🟢 Priorizar `X-EDGE-TOKEN` quando coexistir com `Authorization`.
- 🟢 Calcular SHA-256 do token recebido.
- 🟢 Buscar `EdgeToken` ativo por `token_hash`.
- 🟢 Rejeitar token ausente/inválido com `401 edge_token_invalid`.
- 🟢 Rejeitar store mismatch com `403 edge_store_mismatch`.
- 🟢 Rejeitar store bloqueada/suspensa/edge-disabled com `403 edge_store_disabled`.
- 🟢 Atualizar `last_used_at` em token válido.
- 🟢 Preencher `request.edge_store_id` e `request.store`.
- 🟢 Não logar token em claro.

## Critérios de Aceitação

- 🟢 Dado request com `X-EDGE-TOKEN` válido, quando autenticar, então retorna `ok=true` e `store_id`.
- 🟢 Dado request com `X-EDGE-TOKEN` e `Authorization` divergentes, quando autenticar, então usa `X-EDGE-TOKEN`.
- 🟢 Dado token válido de outra store, quando `requested_store_id` for informado, então retorna `403 edge_store_mismatch`.
- 🟢 Dado store bloqueada, quando autenticar, então retorna `403 edge_store_disabled`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\auth.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\tests.py`.
