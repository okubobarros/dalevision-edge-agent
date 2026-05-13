# autenticar-edge-token - Tasks

- [ ] 🟢 Implementar extração de token.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`.
  - Critério de pronto: todos os headers/query/schemes documentados são aceitos.

- [ ] 🟢 Implementar prioridade de `X-EDGE-TOKEN`.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`, `apps\edge\tests.py`.
  - Critério de pronto: teste confirma que header edge vence Authorization.

- [ ] 🟢 Implementar autenticação por hash.
  - Fonte: `C:\workspace\dale-vision\apps\edge\models.py`.
  - Critério de pronto: token claro nunca é comparado diretamente com banco, apenas SHA-256.

- [ ] 🟢 Implementar rejeição por mismatch.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`.
  - Critério de pronto: resposta `403 edge_store_mismatch`.

- [ ] 🟢 Implementar kill switch de store.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`, `apps\edge\tests.py`.
  - Critério de pronto: store bloqueada ou edge-disabled retorna `403 edge_store_disabled`.

- [ ] 🟢 Implementar logs sem segredo.
  - Fonte: `C:\workspace\dale-vision\apps\edge\auth.py`.
  - Critério de pronto: logs mostram apenas hash mascarado.
