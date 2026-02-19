DALE Vision — Edge Agent (Windows)

ANTES DE TUDO
Preencha o arquivo .env (template) com os dados do suporte.

PASSO A PASSO (1 a 4)
1) 01 - Iniciar Agent.bat
2) 02 - Teste rapido (run once).bat
3) 03 - Diagnostico (gerar ZIP).bat
4) 04 - Instalar como Servico (Admin).ps1

QUANDO USAR CADA UM
1) Iniciar Agent: entrada principal do dia a dia.
2) Teste rapido: executa uma vez e sai (retorna erro se falhar).
3) Diagnostico: gera um ZIP em output\ para enviar ao suporte.
4) Instalar como Servico: inicia o agente no boot (requer Admin).

ALERTA DO WINDOWS (SmartScreen)
Se aparecer "Windows protegeu seu PC":
1) Clique em "Mais informacoes"
2) Clique em "Executar assim mesmo"

ASSINATURA (OPCIONAL)
Se o pipeline tiver assinatura do executavel, adicione a etapa de code signing
no build/CI para reduzir o alerta do SmartScreen.
