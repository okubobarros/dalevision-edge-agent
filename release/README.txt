DALE Vision — Edge Agent (Windows)

EM 10 SEGUNDOS
1) Substitua o arquivo .env pelo .env enviado pelo suporte.
2) Execute: Start_DaleVision_Agent.bat
3) No app, clique em "Adicionar camera".

SE QUISER TESTAR ANTES (OPCIONAL)
Execute: Testar_Conexao.bat

SE DER ERRO
1) Execute: Diagnose.bat
2) Envie o ZIP gerado para o suporte.

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"

ASSINATURA (OPCIONAL)
Se o pipeline tiver assinatura do executavel, adicione a etapa de code signing
no build/CI para reduzir o alerta do SmartScreen.
