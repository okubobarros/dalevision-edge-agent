# edge-agent-update-installation - Edge Cases

## Policy e rollout

- 🟢 Payload de policy sem versão ou URL deve registrar `UPD002` e não iniciar update.
- 🟢 `current_min_supported` maior que versão atual deve bloquear update em `policy_check` e registrar `UPD015`.
- 🟢 Horário fora de `rollout_window` deve bloquear update e registrar `UPD016`.
- 🟢 Janela de rollout inválida deve falhar aberta para evitar travar updates.
- 🟢 Canal ausente deve assumir `stable`.
- 🟢 `AUTO_UPDATE_ENABLED=0` deve bloquear aplicação automática e registrar `UPD011`.

## Lock e concorrência

- 🟢 Lock ativo em `updates/update.lock` deve retornar `UPDATE_LOCKED`.
- 🟢 Lock stale deve ser substituído após TTL.
- 🟡 Se o processo morrer antes de liberar lock, a próxima execução depende do TTL para recuperar.
- 🟡 Se dois processos criarem lock simultaneamente em filesystem não atômico, pode haver corrida residual; não há evidência de mutex Windows nativo.

## Download e pacote

- 🟢 Timeout de download deve abortar sem substituir executável.
- 🟢 Checksum divergente deve apagar o artefato baixado e registrar `UPD021`.
- 🟢 ZIP sem `.exe` deve registrar `UPD022 zip sem exe`.
- 🟢 Download válido deve registrar `UPD022 download ok`.
- 🟡 URL indisponível, proxy corporativo ou TLS interceptado devem aparecer como falha de download/report, mas o código exato pode variar.

## Ativação e rollback

- 🟢 Processo não `.exe` não deve aplicar update.
- 🟢 Falha de health gate por heartbeat deve registrar `UPD041` e acionar rollback quando houver backup.
- 🟢 Rollback bem-sucedido deve registrar `UPD050 rollback aplicado`.
- 🟢 Rollback falho deve registrar `UPD051 rollback falhou`.
- 🟡 Falta de permissão de escrita no diretório do EXE pode impedir ativação e rollback.
- 🟡 Antivírus ou EDR pode bloquear substituição do EXE; comportamento final depende do Windows do cliente.

## Reports

- 🟢 Falha ao enviar report deve registrar `UPD050`.
- 🟢 Idempotency key não deve incluir timestamp, evitando eventos duplicados em retries.
- 🟢 Constraint única de `EdgeUpdateEvent` deve impedir duplicação por chave.
- 🟡 Se o backend estiver fora do ar, o update local pode prosseguir sem observabilidade completa, dependendo da fase da falha.

## Release Windows

- 🟢 Artefato obrigatório ausente deve impedir ZIP final.
- 🟢 O bundle deve incluir scripts de instalação, verificação, diagnóstico, update e remoção.
- 🟢 `.env.template` deve ser copiado como `.env`.
- 🟡 `nssm.exe` é tratado como opcional no script de release.
- 🟡 Build com PyInstaller fora do pipeline esperado pode quebrar o caminho `dist\dalevision-edge-agent.exe`.

## Backend

- 🟢 Canal inválido no gerenciamento de release deve ser rejeitado.
- 🟢 `download_url` ausente ou inválida deve ser rejeitada no gerenciamento.
- 🟢 Novo release ativo deve desativar releases anteriores do mesmo canal.
- 🟢 Sem `EdgeRelease` ativo, latest deve cair para settings `EDGE_RELEASE_*`.
- 🟡 Policy por loja com `store_id` único restringe uma política ativa por loja; múltiplas políticas segmentadas exigiriam novo desenho.
