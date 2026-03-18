DALE Vision — Edge Agent (Windows)

PASSO 1: CONFIGURAR
1) Edite o arquivo .env.
2) Preencha STORE_ID, EDGE_TOKEN e DASHBOARD_URL.

PASSO 2: TESTE RAPIDO
1) Execute 01_TESTE_RAPIDO.bat (nao precisa admin).
2) O script envia um heartbeat unico e encerra automaticamente.
3) Verifique "status=201" em logs\agent.log.

PASSO 3: INSTALAR AUTOSTART
1) Execute 02_INSTALAR_AUTOSTART.bat (nao precisa admin).
2) A tarefa roda no login do usuario (ONLOGON) e usa a mesma pasta do ZIP.
3) O .env lido e o da pasta extraida (onde voce editou).
4) Se o Windows bloqueou o download, o instalador ja desbloqueia automaticamente.

PASSO 4: VERIFICAR STATUS
1) Execute 03_VERIFICAR_STATUS.bat.
2) Veja o status da tarefa e as ultimas linhas do log.

PASSO 5: REMOVER AUTOSTART
1) Execute 04_REMOVER_AUTOSTART.bat.

PASSO 6: PARAR AGENTE E LIBERAR PASTA
1) Execute 05_PARAR_AGENTE_E_LIBERAR_PASTA.bat (nao precisa admin).
2) Use antes de substituir/excluir a pasta extraida do agente.

IMPORTANTE
- Nao clique em arquivos .ps1 dentro de scripts\.
- Auto-update vem ativado por padrao (AUTO_UPDATE_ENABLED=1).
- Para desativar explicitamente, use AUTO_UPDATE_ENABLED=0 no .env.

ARQUIVOS NO ZIP
- dalevision-edge-agent.exe
- .env
- 01_TESTE_RAPIDO.bat
- 02_INSTALAR_AUTOSTART.bat
- 03_VERIFICAR_STATUS.bat
- 04_REMOVER_AUTOSTART.bat
- 05_PARAR_AGENTE_E_LIBERAR_PASTA.bat
- Diagnose.bat
- README.txt
- logs\
- scripts\

UPDATE (MVP)
1) Configure no .env:
   - UPDATE_GITHUB_REPO=org/repo
   - UPDATE_INTERVAL_SECONDS=21600
2) Reinstale o autostart para criar/atualizar a tarefa de update.
3) Logs do update: logs\update.log.

DIAGNOSTICO
- Execute Diagnose.bat e envie o ZIP para o suporte.
- Logs ficam em logs\agent.log e logs\update.log.
- Para checar a tarefa, use o Task Scheduler ou:
  schtasks /Query /TN DaleVisionEdgeAgent /V /FO LIST

SE O WINDOWS BLOQUEAR O ARQUIVO (DOWNLOAD)
1) Clique com o botao direito no .zip ou .exe
2) Propriedades > Desbloquear > Aplicar

TESTE MANUAL (INSTALL-SERVICE + FALLBACK)
1) Extraia o ZIP em uma pasta local.
2) Rode `dalevision-edge-agent.exe` e escolha opcao 3.
3) Validar criacao das tarefas `DaleVisionEdgeAgent` e `DaleVisionEdgeAgentUpdate` (quando auto-update estiver ativo).
4) Validar que a tarefa aponta para a pasta extraida (mesmo local do .env).
5) Validar que o app nao fecha apos erro de script ausente; o menu deve continuar ativo.
