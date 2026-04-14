DALE Vision — Edge Agent (Windows)

DISTRIBUICAO RECOMENDADA
- Preferencial: DaleVisionEdgeSetup-vX.Y.Z.exe (instalacao 1 clique, sem admin).
- Fallback tecnico: dalevision-edge-agent-windows.zip.

SETUP.EXE COM TOKEN (RECOMENDADO NO ONBOARDING)
- O instalador aceita token sem CMD por tela no wizard ou automaticamente pelo nome do arquivo.
- O token e encaminhado ao bootstrap e gravado em %%APPDATA%%\DaleVision\agent_config.json.
- Fluxo recomendado: baixar e abrir o .exe normalmente; se nao houver token embutido no nome, o wizard pede "Token de Ativacao".
- Fluxo silencioso opcional por nome de arquivo:
  DaleVisionEdgeSetup_tk_SEU_TOKEN.exe
- Compatibilidade mantida com linha de comando:
- Exemplo (token direto):
  DaleVisionEdgeSetup-vX.Y.Z.exe /ACTIVATION_TOKEN=SEU_TOKEN
- Exemplo (token em arquivo):
  DaleVisionEdgeSetup-vX.Y.Z.exe /ACTIVATION_TOKEN_FILE="C:\temp\dalevision-token.txt"
- Opcional (forcar API no instalador):
  DaleVisionEdgeSetup-vX.Y.Z.exe /ACTIVATION_TOKEN=SEU_TOKEN /CLOUD_BASE_URL=https://api.dalevision.com

PASSO 1: CONFIGURAR
1) Edite o arquivo .env (copie para %%APPDATA%%\DaleVision\.env se necessario).
2) Preencha STORE_ID, EDGE_TOKEN e DASHBOARD_URL.

PASSO 2: TESTE RAPIDO
1) Execute 01_TESTE_RAPIDO.bat (nao precisa admin).
2) O script envia um heartbeat unico e encerra automaticamente.
3) Verifique "status=201" em %%LOCALAPPDATA%%\DaleVision\logs\agent.log.

PASSO 3: INSTALAR AUTOSTART
1) Execute 02_INSTALAR_AUTOSTART.bat (nao precisa admin).
2) O instalador copia os arquivos para %%LOCALAPPDATA%%\DaleVision\app\<versao>\.
3) O autostart e criado via Startup shortcut do usuario atual.
4) O .env usado fica em %%APPDATA%%\DaleVision\.env.

PASSO 4: VERIFICAR STATUS
1) Execute 03_VERIFICAR_STATUS.bat.
2) Veja startup shortcut, processo e ultimas linhas de log.

PASSO 5: REMOVER AUTOSTART
1) Execute 04_REMOVER_AUTOSTART.bat.

PASSO 6: PARAR AGENTE E LIBERAR PASTA
1) Execute 05_PARAR_AGENTE_E_LIBERAR_PASTA.bat (nao precisa admin).
2) Use antes de substituir/excluir a pasta extraida apenas se necessario.

IMPORTANTE
- Nao clique em arquivos .ps1 dentro de scripts\.
- Auto-update vem ativado por padrao (AUTO_UPDATE_ENABLED=1).
- Para desativar explicitamente, use AUTO_UPDATE_ENABLED=0 no .env.
- Runtime temporario usa %%LOCALAPPDATA%%\DaleVision\cache\runtime\ (cleanup automatico best effort).

ARQUIVOS NO ZIP
- dalevision-edge-agent.exe
- .env
- 01_TESTE_RAPIDO.bat
- 02_INSTALAR_AUTOSTART.bat
- 03_VERIFICAR_STATUS.bat
- 04_REMOVER_AUTOSTART.bat
- 05_PARAR_AGENTE_E_LIBERAR_PASTA.bat
- Diagnose.bat
- README.txt
- logs\
- scripts\

UPDATE (MVP)
1) Configure no .env:
   - UPDATE_GITHUB_REPO=org/repo
   - UPDATE_INTERVAL_SECONDS=21600
2) Reinstale o autostart para criar/atualizar a tarefa de update.
3) Logs do update: logs\update.log.

DIAGNOSTICO
- Execute Diagnose.bat e envie o ZIP para o suporte.
- Logs ficam em %%LOCALAPPDATA%%\DaleVision\logs\agent.log e update.log.
- Arquivo de instalacao em %%APPDATA%%\DaleVision\install.json.

SE O WINDOWS BLOQUEAR O ARQUIVO (DOWNLOAD)
1) Clique com o botao direito no .zip ou .exe
2) Propriedades > Desbloquear > Aplicar

TESTE MANUAL (INSTALL-SERVICE + FALLBACK)
1) Extraia o ZIP em uma pasta local.
2) Rode `02_INSTALAR_AUTOSTART.bat`.
3) Validar criacao do atalho em `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
4) Validar que app/config/log/cache apontam para %%LOCALAPPDATA%%/%%APPDATA%%.
5) Validar que nao ha uso operacional em Downloads.
