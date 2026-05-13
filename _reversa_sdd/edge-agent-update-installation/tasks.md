# edge-agent-update-installation - Tasks

## Tarefas de Reconstrução

- [ ] 🟢 Implementar cliente de policy de update.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: consulta `/api/edge/update-policy/` com fallback legado, parseia `target_version`, URL, SHA-256, canal, janela e health gate.

- [ ] 🟢 Implementar comparação de versão mínima.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: versão atual abaixo de `current_min_supported` bloqueia update em `policy_check` e registra `UPD015`.

- [ ] 🟢 Implementar validação de rollout window.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: fora da janela registra `UPD016`; janela inválida falha aberta.

- [ ] 🟢 Implementar flag `AUTO_UPDATE_ENABLED`.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: `AUTO_UPDATE_ENABLED=0` registra `UPD011` e impede aplicação automática.

- [ ] 🟢 Implementar lock local de update.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: cria `updates/update.lock`, bloqueia concorrência com `UPDATE_LOCKED`, expira lock stale por TTL e libera lock ao final.

- [ ] 🟢 Implementar download com checksum.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: baixa para `updates/update-<version>`, timeout de 15 segundos, valida SHA-256, remove arquivo inválido e registra `UPD021` em mismatch.

- [ ] 🟢 Implementar validação de pacote ZIP/EXE.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: ZIP sem EXE registra `UPD022 zip sem exe`; download válido registra `UPD022 download ok`.

- [ ] 🟢 Implementar ativação com backup.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: só aplica em `.exe`, preserva `.exe.bak` e retorna status/fase apropriados.

- [ ] 🟢 Integrar update ao loop operacional.
  - Fonte: `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: loop encadeia policy, lock, report started, download, checksum, ativação, health gate, report final e release do lock.

- [ ] 🟢 Implementar health gate pós-update.
  - Fonte: `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: heartbeat exigido dentro do prazo; defaults `120/180/3`; falha registra `UPD041`.

- [ ] 🟢 Implementar rollback.
  - Fonte: `src/dalevision_edge_agent/main.py`.
  - Critério de pronto: restaura `.exe.bak` quando health gate falha; sucesso loga `UPD050 rollback aplicado`; falha loga `UPD051 rollback falhou`.

- [ ] 🟢 Implementar envio de update report idempotente.
  - Fonte: `src/dalevision_edge_agent/update.py`.
  - Critério de pronto: posta em `/api/edge/update-report/`, inclui idempotency key estável sem timestamp e loga `UPD050` em falha.

- [ ] 🟢 Implementar modelos cloud de update.
  - Fonte: `C:\workspace\dale-vision\apps\edge\models.py`.
  - Critério de pronto: `EdgeUpdatePolicy`, `EdgeUpdateEvent`, `EdgeDevice` e `EdgeRelease` persistem policy, eventos, versão instalada, canal e releases ativos.

- [ ] 🟢 Implementar release latest público.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
  - Critério de pronto: endpoint retorna release ativo por canal e fallback por settings quando não houver release ativo.

- [ ] 🟢 Implementar gerenciamento autenticado de release.
  - Fonte: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
  - Critério de pronto: valida versão, URL e canal; faz `update_or_create`; desativa releases anteriores do mesmo canal.

- [ ] 🟢 Implementar script de release Windows.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: gera `dalevision-edge-agent-windows.zip` com EXE, scripts, `.env`, modelo, aliases e build info com hashes.

- [ ] 🟡 Criar teste de VM Windows para update/rollback.
  - Fonte: lacuna operacional detectada na análise.
  - Critério de pronto: teste simula policy válida, checksum inválido, health gate falho e rollback com logs esperados.

## Critérios Globais de Pronto

- 🟢 Nenhum segredo aparece em logs.
- 🟢 Eventos duplicados não criam duplicidade lógica no backend por idempotency key.
- 🟢 Update inválido nunca substitui o executável atual.
- 🟢 Falha de health gate tenta rollback.
- 🟢 ZIP de release contém artefatos necessários para instalação por cliente leigo.
