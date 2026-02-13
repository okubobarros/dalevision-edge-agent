DALE Vision — Edge Agent (Windows)

PASSO A PASSO (2 minutos)
1) Extraia o ZIP em uma pasta (ex.: C:\dalevision-edge-agent\)
2) Abra o arquivo .env (tipo "Arquivo ENV")
3) Cole no .env o conteudo gerado no Wizard (Copiar .env) e salve
4) Clique duas vezes em run.bat
5) Deixe a janela aberta
6) Volte no Dashboard e aguarde ficar ONLINE

LOGS
- Arquivo: logs\agent.log (rotaciona, 5 arquivos de 2MB)
- Stdout/Stderr: stdout.log (nesta pasta)
- Se precisar de suporte, envie os logs mais recentes.

DICAS
- NAO rode de dentro do ZIP. Sempre extraia antes.
- Se aparecer .env.example em versoes antigas, ignore esse template e edite apenas o .env.
- Se aparecer erro de firewall, libere o aplicativo e tente de novo.
- Se der erro de token, gere um novo token no Wizard e copie o .env novamente.
- Se a janela fechar rapido, abra o Prompt na pasta e rode: cmd /k run.bat
