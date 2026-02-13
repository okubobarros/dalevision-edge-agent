DALE Vision — Edge Agent (Windows)

PASSO A PASSO (2 minutos)
1) Extraia o ZIP em uma pasta (ex.: C:\dalevision-edge-agent\)
2) Abra o arquivo .env (tipo "Arquivo ENV")
3) Cole no .env o conteudo gerado no Wizard (Copiar .env) e salve
4) Primeiro rode: run.bat --once (ou run_once.bat)
5) Se retornar status=201 (exit code 0), rode normal: run.bat
6) Deixe a janela aberta
7) Volte no Dashboard e aguarde ficar ONLINE

LOGS
- Arquivo: logs\agent.log (rotaciona, 5 arquivos de 2MB)
- Stdout/Stderr: logs\stdout.log
- Se precisar de suporte, envie os logs mais recentes.

DICAS
- NAO rode de dentro do ZIP. Sempre extraia antes.
- Se aparecer .env.example em versoes antigas, ignore esse template e edite apenas o .env.
- Se aparecer erro de firewall, libere o aplicativo e tente de novo.
- Se der erro de token, gere um novo token no Wizard e copie o .env novamente.
- Se a janela fechar rapido, abra o Prompt na pasta e rode: cmd /k run.bat

TESTES MANUAIS (SMOKE TEST)
- Caso OK: execute run.bat --once e confirme "status=201" e exit code 0.
- Caso token invalido: execute run.bat --once e confirme "HTTP 403" e exit code 3.
- Caso sem .env: execute run.bat --once e confirme exit code 2.
