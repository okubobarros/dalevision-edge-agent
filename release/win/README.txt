DALE Vision — Edge Agent (Windows)

OBJETIVO
Manter a loja online no cloud e monitorar health das cameras.

TESTE RAPIDO (MANUAL)
1) Edite o arquivo .env e preencha os dados da loja.
2) Execute Start_DaleVision_Agent.bat.
3) Verifique logs em logs\agent.log.

PRODUCAO (AUTO START NO BOOT)
1) Clique com o botao direito em install-service.ps1 > Executar como administrador.
2) Reinicie o PC.
3) Verifique status da task:
   schtasks /Query /TN DaleVisionEdgeAgent /V /FO LIST
4) Verifique logs:
   Get-Content .\logs\agent.log -Tail 80

ARQUIVOS
- Start_DaleVision_Agent.bat: inicia o agente e grava logs em logs\agent.log.
- Start_DaleVision_Agent.ps1: wrapper oculto para uso em servico (Task Scheduler).
- Diagnose.bat: gera ZIP de diagnostico para suporte.
- install-service.ps1: instala o auto start no boot (Task Scheduler).
- uninstall-service.ps1: remove o auto start.
- update.ps1: checagem de update (MVP, seguro).

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"
