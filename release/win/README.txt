DALE Vision — Edge Agent (Windows)

PASSO 1 — Preencher o .env
Preencha o arquivo .env (template) com os dados do suporte.

PASSO 2 — Iniciar
Execute: Start_DaleVision_Agent.bat
No app, clique em "Adicionar camera".

SE DER ERRO
Execute: Diagnose.bat
Envie o ZIP gerado para o suporte.

AVANCADO (OPCIONAL)
01 - Iniciar Agent.bat: entrada principal (alias).
02 - Teste rápido (run once).bat: teste rapido.
03 - Diagnóstico (gerar ZIP).bat: suporte.
install-service.ps1: instalar como servico (requer Administrador).
run.bat e run_once.bat: compatibilidade/avancado.

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"

ASSINATURA (OPCIONAL)
Se o pipeline tiver assinatura do executavel, adicione a etapa de code signing
no build/CI para reduzir o alerta do SmartScreen.
