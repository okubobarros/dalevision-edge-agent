DALE Vision — Edge Agent (Windows)

OBJETIVO
Manter a loja online no cloud e monitorar health das cameras.

FASE 1: TESTE (MANUAL)
1) Edite o arquivo .env e preencha STORE_ID e EDGE_TOKEN.
2) Execute 02_TESTE_RAPIDO.bat.
3) Verifique logs em logs\agent.log.
4) No app, confirme "Edge Online".

FASE 2: SERVICO (AUTO START NO BOOT)
1) Execute 03_INSTALAR_AUTOSTART.bat.
2) Reinicie o PC.
3) Verifique status:
   04_VERIFICAR_STATUS.bat
4) Verifique logs:
   Get-Content .\logs\agent.log -Tail 80

DIAGNOSTICO
- Execute Diagnose.bat e envie o ZIP para o suporte.

UPDATE (MVP)
1) Preencha UPDATE_GITHUB_REPO no .env (ex: org/repo).
2) Execute update.ps1 manualmente.
3) Veja logs em logs\update.log.

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"
