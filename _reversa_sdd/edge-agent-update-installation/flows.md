# edge-agent-update-installation - Flows

## Fluxo 1 - Descobrir update por policy

1. 🟢 Agente possui `cloud_base_url` e `edge_token`.
2. 🟢 Agente chama `/api/edge/update-policy/`.
3. 🟢 Backend retorna versão alvo, pacote, checksum, canal, janela e health gate.
4. 🟢 Agente valida payload.
5. 🟢 Agente compara versão atual com `current_min_supported`.
6. 🟢 Agente valida janela local.
7. 🟢 Agente retorna `update available` e loga `UPD010`.

## Fluxo 2 - Bloquear update por política

1. 🟢 Agente recebe policy.
2. 🟢 Se payload é inválido, registra `UPD002`.
3. 🟢 Se versão atual é menor que o mínimo, registra `UPD015`.
4. 🟢 Se está fora da janela, registra `UPD016`.
5. 🟢 Se auto-update está desligado, registra `UPD011`.
6. 🟢 Fluxo termina sem download nem substituição de EXE.

## Fluxo 3 - Download e verificação

1. 🟢 Loop adquire `updates/update.lock`.
2. 🟢 Agente reporta `edge_update_started`.
3. 🟢 Agente baixa pacote para `updates/update-<version>`.
4. 🟢 Se download falha, reporta `failed` na fase `download`.
5. 🟢 Se SHA-256 diverge, registra `UPD021`, remove artefato e reporta falha.
6. 🟢 Se ZIP não contém EXE, registra `UPD022 zip sem exe`.
7. 🟢 Se válido, registra `UPD022 download ok` e reporta `downloaded`/`verified`.

## Fluxo 4 - Ativação, health gate e rollback

1. 🟢 Agente confirma que está rodando como `.exe`.
2. 🟢 Agente cria backup `.exe.bak`.
3. 🟢 Agente ativa/substitui executável.
4. 🟢 Agente executa health gate pós-update.
5. 🟢 Se heartbeat ocorre dentro do prazo, reporta `activated`.
6. 🟢 Se heartbeat falha, registra `UPD041`.
7. 🟢 Com backup disponível, agente tenta rollback.
8. 🟢 Rollback ok registra `UPD050 rollback aplicado`.
9. 🟢 Rollback falho registra `UPD051 rollback falhou`.

## Fluxo 5 - Gerar release Windows

1. 🟢 Operador executa `.\scripts\release_windows.ps1 -Version vX.Y.Z`.
2. 🟢 Script prepara `release/win`.
3. 🟢 Script copia EXE, modelo, README, `.env`, BATs, PS1s, aliases e scripts internos.
4. 🟢 Script calcula hashes de artefatos críticos.
5. 🟢 Script valida arquivos obrigatórios.
6. 🟢 Script compacta `release/win/*` em `dalevision-edge-agent-windows.zip`.
7. 🟢 Operador publica o ZIP em GitHub Release ou URL configurada.

## Fluxo 6 - Servir release latest

1. 🟢 Cliente chama endpoint latest com canal `stable` ou `canary`.
2. 🟢 Backend procura `EdgeRelease` ativo para o canal.
3. 🟢 Se encontrado, retorna versão, URL, SHA-256, tamanho, notas e setup URL.
4. 🟢 Se não encontrado, usa settings `EDGE_RELEASE_*`.
5. 🟢 Se setup URL específica existe, usa `EDGE_WINDOWS_SETUP_URL`.

## Fluxo 7 - Gerenciar release cloud

1. 🟢 Usuário autenticado envia dados de release.
2. 🟢 Backend valida versão, URL e canal.
3. 🟢 Backend cria ou atualiza `EdgeRelease`.
4. 🟢 Backend marca novo release como ativo.
5. 🟢 Backend desativa releases anteriores do mesmo canal.
6. 🟢 Resposta indica método `edge_release_upsert`.
