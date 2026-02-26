DALE Vision — Edge Agent (Windows)

FASE A: CONFIGURAR
1) Edite o arquivo .env.template.
2) Preencha apenas STORE_ID e EDGE_TOKEN.
3) Salve como .env (copie/renomeie o arquivo).

FASE B: TESTE RAPIDO (UMA VEZ)
1) Execute 02_TESTE_RAPIDO.bat.
2) Verifique "status=201" em logs\agent.log.

FASE C: INSTALAR AUTOSTART
1) Execute 03_INSTALAR_AUTOSTART.bat (precisa admin).
2) A tarefa roda como SYSTEM, em janela oculta.

FASE D: VERIFICAR STATUS
1) Execute 04_VERIFICAR_STATUS.bat.
2) Veja a tarefa instalada + ultima execucao.
3) Logs: logs\agent.log.

FASE E: REMOVER SERVICO
1) Execute 05_REMOVER_SERVICO.bat.

IMPORTANTE
- Start_DaleVision_Agent.bat/.ps1 NAO sao para clicar manualmente.
  Eles sao usados pela tarefa agendada.
- Auto-update vem desativado por padrao (AUTO_UPDATE_ENABLED=0).

ARQUIVOS NO ZIP
- dalevision-edge-agent.exe
- .env.template
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
- Logs ficam em logs\agent.log e logs\update.log.
- Para checar a tarefa, use o Task Scheduler ou:
  schtasks /Query /TN DaleVisionEdgeAgent /V /FO LIST

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"
