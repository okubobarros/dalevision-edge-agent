# ativar-loja-edge - Tasks

- [ ] 🟢 Implementar emissão de activation token.
  - Fonte: `views_activation.py`.
  - Critério de pronto: resposta contém token, expiração e single_use.

- [ ] 🟢 Implementar armazenamento hash.
  - Fonte: `services\activation_registry.py`.
  - Critério de pronto: `ActivationToken.token_hash` recebe SHA-256 e hint final.

- [ ] 🟢 Implementar ativação de device.
  - Fonte: `services\activation_registry.py`.
  - Critério de pronto: device fica active e activation token fica usado/inativo.

- [ ] 🟢 Implementar emissão de Edge Token.
  - Fonte: `services\activation_registry.py`.
  - Critério de pronto: tokens anteriores são desativados e novo token é retornado.

- [ ] 🟡 Revisar persistência de token plaintext.
  - Fonte: `apps\edge\models.py`, `services\activation_registry.py`.
  - Critério de pronto: decisão formal sobre exibição única vs reexibição.
