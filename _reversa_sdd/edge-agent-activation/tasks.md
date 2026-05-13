# Edge Agent Activation, Tasks

## Tarefas

- [ ] T-ACT-01, Implementar emissão backend de activation token.
  - Origem no legado: `C:\workspace\dale-vision\apps\stores\views_activation.py` `StoreActivationTokenView`
  - Critério de pronto: resposta 201 contém token, TTL, `single_use=True` e store_id.
  - Confiança: 🟢

- [ ] T-ACT-02, Implementar cliente local de ativação.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `ActivationClient.activate`
  - Critério de pronto: POST envia token, device_key, versão e canal; retorna `ActivationResult`.
  - Confiança: 🟢

- [ ] T-ACT-03, Implementar bootstrap local.
  - Origem no legado: `activation.py` `bootstrap_activation`
  - Critério de pronto: cobre device existente, token ausente, cloud ausente, sucesso, rede e 401/403/409.
  - Confiança: 🟢

- [ ] T-ACT-04, Implementar persistência pós-sucesso.
  - Origem no legado: `bootstrap_activation`
  - Critério de pronto: salva `device_key`, `store_id`, `edge_token`, `edge_device_id`, `update_channel`, `installed_version`; remove `activation_token`.
  - Confiança: 🟢

- [ ] T-ACT-05, Implementar hidratação de `.env`.
  - Origem no legado: `hydrate_runtime_env_from_activation_config`
  - Critério de pronto: grava cloud/store/token/agent sem logar segredo.
  - Confiança: 🟢

- [ ] T-ACT-06, Implementar validação backend de edge token após ativação.
  - Origem no legado: `C:\workspace\dale-vision\apps\edge\auth.py`
  - Critério de pronto: `X-EDGE-TOKEN` autentica por hash ativo e store match.
  - Confiança: 🟢

## Testes

- [ ] TT-ACT-01, Token emitido retorna `single_use=True`.
- [ ] TT-ACT-02, Device já provisionado não chama backend.
- [ ] TT-ACT-03, Sucesso limpa `activation_token`.
- [ ] TT-ACT-04, Rede mantém estado `activating`.
- [ ] TT-ACT-05, 401/403/409 vira `error`.
- [ ] TT-ACT-06, `.env` hidratado não expõe token em logs.

## Lacunas

- 🔴 Mapear todos os códigos de erro do service `activate_edge_device`.
