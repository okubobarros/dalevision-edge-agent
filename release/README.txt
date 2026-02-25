DALE Vision — Edge Agent (Windows)

PASSO 1: CONFIGURAR
1) Edite o arquivo .env e preencha STORE_ID e EDGE_TOKEN (e CLOUD_BASE_URL).

PASSO 2: TESTE RAPIDO (UMA VEZ)
1) Execute 02_TESTE_RAPIDO.bat.
2) Verifique "status=201" em logs\agent.log.

PASSO 3: INSTALAR AUTOSTART
1) Execute 03_INSTALAR_AUTOSTART.bat (precisa admin).
2) Reinicie o PC.

PASSO 4: VERIFICAR STATUS
1) Execute 04_VERIFICAR_STATUS.bat.
2) Veja a tarefa instalada + ultima execucao.
3) Logs: logs\agent.log.

PASSO 5: REMOVER SERVICO
1) Execute 05_REMOVER_SERVICO.bat.

ARQUIVOS NO ZIP
- dalevision-edge-agent.exe
- .env
- 02_TESTE_RAPIDO.bat
- 03_INSTALAR_AUTOSTART.bat
- 04_VERIFICAR_STATUS.bat
- 05_REMOVER_SERVICO.bat
- Start_DaleVision_Agent.bat
- Start_DaleVision_Agent.ps1
- install-service.ps1
- uninstall-service.ps1
- verify-service.ps1
- update.ps1
- Diagnose.bat
- logs\

UPDATE (MVP)
1) Configure no .env:
   - AUTO_UPDATE_ENABLED=1
   - UPDATE_GITHUB_REPO=org/repo
   - UPDATE_INTERVAL_SECONDS=21600
2) Reinstale o autostart para criar a tarefa de update.
3) Logs do update: logs\update.log.

DIAGNOSTICO
- Execute Diagnose.bat e envie o ZIP para o suporte.

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"
