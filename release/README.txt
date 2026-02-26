DALE Vision — Edge Agent (Windows)

PASSO 1: CONFIGURAR
1) Edite o arquivo .env.
2) Preencha STORE_ID, EDGE_TOKEN e DASHBOARD_URL.

PASSO 2: TESTE RAPIDO
1) Execute 01_TESTE_RAPIDO.bat (nao precisa admin).
2) Verifique "Loaded env OK" e heartbeats.
3) Verifique "status=201" em logs\agent.log.
4) Para parar, feche a janela do teste rapido.

PASSO 3: INSTALAR AUTOSTART
1) Execute 02_INSTALAR_AUTOSTART.bat (precisa admin).
2) A tarefa roda como SYSTEM, em janela oculta.
3) O instalador copia automaticamente para C:\ProgramData\DaleVision\EdgeAgent
3) Se o Windows bloqueou o download, o instalador ja desbloqueia automaticamente.

PASSO 4: VERIFICAR STATUS
1) Execute 03_VERIFICAR_STATUS.bat.
2) Veja o status da tarefa e as ultimas linhas do log.

PASSO 5: REMOVER AUTOSTART
1) Execute 04_REMOVER_AUTOSTART.bat (precisa admin).

IMPORTANTE
- Nao clique em arquivos .ps1 dentro de scripts\.
- Auto-update vem desativado por padrao (AUTO_UPDATE_ENABLED=0).

ARQUIVOS NO ZIP
- dalevision-edge-agent.exe
- .env
- 01_TESTE_RAPIDO.bat
- 02_INSTALAR_AUTOSTART.bat
- 03_VERIFICAR_STATUS.bat
- 04_REMOVER_AUTOSTART.bat
- Diagnose.bat
- README.txt
- logs\
- scripts\

UPDATE (MVP)
1) Configure no .env:
   - AUTO_UPDATE_ENABLED=1
   - UPDATE_GITHUB_REPO=org/repo
   - UPDATE_INTERVAL_SECONDS=21600
2) Reinstale o autostart para criar a tarefa de update.
3) Logs do update: logs\update.log.

DIAGNOSTICO
- Execute Diagnose.bat e envie o ZIP para o suporte.
- Logs ficam em logs\agent.log e logs\update.log.
- Para checar a tarefa, use o Task Scheduler ou:
  schtasks /Query /TN DaleVisionEdgeAgent /V /FO LIST

SE O WINDOWS BLOQUEAR O ARQUIVO (DOWNLOAD)
1) Clique com o botao direito no .zip ou .exe
2) Propriedades > Desbloquear > Aplicar
