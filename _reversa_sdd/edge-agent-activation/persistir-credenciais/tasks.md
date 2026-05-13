# Persistir Credenciais, Tasks

- [ ] T-PC-01, Salvar credenciais retornadas pelo backend.
  - Origem: `src/dalevision_edge_agent/activation.py` `bootstrap_activation`
  - Critério: config contém store, token, device e canal.
  - Confiança: 🟢

- [ ] T-PC-02, Remover activation token após sucesso.
  - Origem: `bootstrap_activation`
  - Critério: `activation_token` fica `None`.
  - Confiança: 🟢

- [ ] T-PC-03, Hidratar runtime env.
  - Origem: `hydrate_runtime_env_from_activation_config`
  - Critério: `os.environ` recebe CLOUD_BASE_URL, STORE_ID, EDGE_TOKEN e aliases.
  - Confiança: 🟢

- [ ] T-PC-04, Atualizar `.env` preservando linhas existentes.
  - Origem: `hydrate_runtime_env_from_activation_config`
  - Critério: chaves existentes são substituídas e demais linhas preservadas.
  - Confiança: 🟢

- [ ] T-PC-05, Testar ausência de token em logs.
  - Origem: logs de hidratação
  - Critério: log contém `edge_token_len`, não token literal.
  - Confiança: 🟢
