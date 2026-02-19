DALE Vision — Edge Agent (Windows)

PASSO 1 — Preencher o .env
Substitua o arquivo .env pelo .env enviado pelo suporte.

PASSO 2 — Iniciar
Execute: Start_DaleVision_Agent.bat
No app, clique em "Adicionar camera".

SE DER ERRO
Execute: Diagnose.bat
Envie o ZIP gerado para o suporte.

AVANCADO (OPCIONAL)
Testar_Conexao.bat: teste rapido.
install-service.ps1: instalar como servico (requer Administrador).
run.bat e run_once.bat: compatibilidade/avancado.

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"

ASSINATURA (OPCIONAL)
Se o pipeline tiver assinatura do executavel, adicione a etapa de code signing
no build/CI para reduzir o alerta do SmartScreen.
