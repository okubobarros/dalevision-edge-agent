# Ativar Agente, Tasks

- [ ] T-ATV-01, Montar request de ativação.
  - Origem: `src/dalevision_edge_agent/activation.py` `ActivationClient.activate`
  - Critério: body contém token, device_key, installed_version e update_channel.
  - Confiança: 🟢

- [ ] T-ATV-02, Tratar resposta de sucesso.
  - Origem: `bootstrap_activation`
  - Critério: credenciais persistidas e estado `active`.
  - Confiança: 🟢

- [ ] T-ATV-03, Tratar erros por categoria.
  - Origem: `bootstrap_activation`
  - Critério: rede retryable, 401/403/409 fatal.
  - Confiança: 🟢

- [ ] T-ATV-04, Testar token single-use.
  - Origem: `StoreActivationTokenView`, `StoreActivateView`
  - Critério: segunda ativação com mesmo token falha.
  - Confiança: 🟡
