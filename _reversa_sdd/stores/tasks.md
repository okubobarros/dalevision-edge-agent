# stores - Tasks

- [ ] 🟢 Implementar emissão de activation token.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`, `services\activation_registry.py`.
  - Critério de pronto: token single-use, TTL e invalidação de tokens anteriores funcionam.

- [ ] 🟢 Implementar ativação pública de device.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`, `services\activation_registry.py`.
  - Critério de pronto: token válido cria/ativa device e retorna edge token.

- [ ] 🟢 Implementar desabilitação de edge por loja.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`, `services\activation_registry.py`.
  - Critério de pronto: tokens são desativados e devices viram retired.

- [ ] 🟢 Implementar revogação de device.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
  - Critério de pronto: `device_key` válido altera status para retired.

- [ ] 🟢 Implementar download assinado do instalador.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
  - Critério de pronto: link expira, valida store e redireciona para setup URL.

- [ ] 🟢 Implementar credenciais edge no StoreViewSet.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views.py`.
  - Critério de pronto: edge token é emitido/reutilizado e rotação desativa tokens anteriores.

- [ ] 🟢 Implementar serialização de câmeras para edge.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views.py`.
  - Critério de pronto: payload contém RTSP resolvido, RTSP mascarado e somente câmeras ativas para Edge Token.

- [ ] 🟢 Implementar snapshot de status edge.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_edge_status.py`.
  - Critério de pronto: contrato estável retorna status de loja/câmeras e fallback em erro.

- [ ] 🟢 Implementar status de ativação.
  - Fonte: `C:\workspace\dale-vision\apps\stores\services\activation_status.py`.
  - Critério de pronto: deriva activation_state, next_action, device, câmeras, ROI e funil.

- [ ] 🟢 Implementar gerenciamento de release.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
  - Critério de pronto: latest público e upsert admin por canal funcionam.

- [ ] 🟢 Implementar policy de update por loja.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_edge_update_management.py`.
  - Critério de pronto: GET/PUT serializa e valida policy com package SHA.

- [ ] 🟢 Implementar trigger de update.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_edge_update_management.py`.
  - Critério de pronto: cria policy a partir de release ativa e registra `edge_update_requested`.

- [ ] 🟢 Implementar observabilidade de update.
  - Fonte: `views_edge_update_status.py`, `views_edge_update_attempts.py`, `views_edge_update_management.py`.
  - Critério de pronto: status, events, attempts e runbook respondem com contratos documentados.

- [ ] 🟢 Implementar sumários de rede.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_edge_update_network.py`.
  - Critério de pronto: rollout summary e validation summary respeitam orgs do usuário.

- [ ] 🟢 Implementar canary rollout.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_canary.py`.
  - Critério de pronto: batch-tag, health e rollback exigem staff/superuser.

- [ ] 🟡 Unificar nomenclatura de credenciais edge.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views.py`.
  - Critério de pronto: contratos documentam ou padronizam `token` vs `edge_token`.
