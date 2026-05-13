# ativar-loja-edge - Design

## Sequência

1. 🟢 `StoreActivationTokenView.post` valida store e papel.
2. 🟢 `issue_activation_token` desativa tokens ativos anteriores.
3. 🟢 Gera segredo URL-safe e salva SHA-256.
4. 🟢 Retorna segredo ao usuário.
5. 🟢 `StoreActivateView.post` recebe token do agente.
6. 🟢 `activate_edge_device` valida token, uso, estado, expiração e store.
7. 🟢 Resolve device key e canal.
8. 🟢 Cria/atualiza `EdgeDevice`.
9. 🟢 Marca token usado/inativo.
10. 🟢 Emite Edge Token da loja.

## Segurança

- 🟢 Activation token é salvo só como hash.
- 🟢 Edge Token é salvo com hash e plaintext para bootstrap.
- 🟡 Persistir plaintext simplifica suporte, mas aumenta sensibilidade do banco.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_registry.py`.
