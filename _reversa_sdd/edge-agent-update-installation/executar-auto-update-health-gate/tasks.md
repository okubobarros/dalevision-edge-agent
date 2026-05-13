# executar-auto-update-health-gate - Tasks

- [ ] 🟢 Integrar policy ao loop.
  - Fonte: `src/dalevision_edge_agent/main.py`, `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: loop chama `check_for_update` e interpreta bloqueios/updates disponíveis.

- [ ] 🟢 Implementar reports por fase.
  - Fonte: `src/dalevision_edge_agent/main.py`, `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: reports incluem `started`, `downloaded`, `verified`, `activated` e `failed` conforme o resultado.

- [ ] 🟢 Implementar lock em torno do update.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: nenhum download/ativação ocorre sem lock; lock é liberado em sucesso ou falha.

- [ ] 🟢 Implementar validação de policy.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: payload inválido, versão mínima, janela e flag geram bloqueios corretos.

- [ ] 🟢 Implementar download e checksum.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: artefato inválido não segue para ativação.

- [ ] 🟢 Implementar ativação segura.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: aplica somente em `.exe` e cria backup `.exe.bak`.

- [ ] 🟢 Implementar health gate por heartbeat.
  - Fonte: `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: falha de heartbeat no prazo registra `UPD041`.

- [ ] 🟢 Implementar rollback.
  - Fonte: `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: backup é restaurado quando health gate falha; logs diferenciam sucesso e falha.

- [ ] 🟡 Fortalecer validação de camera health no gate.
  - Fonte: lacuna detectada em `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: decidir se `require_camera_health_count` deve ser bloqueante ou apenas observável e documentar ADR.

- [ ] 🟡 Criar testes automatizados de falha por fase.
  - Fonte: lacuna de cobertura.
  - Critério de pronto: testes cobrem policy inválida, checksum inválido, lock ativo, health gate falho e rollback.
