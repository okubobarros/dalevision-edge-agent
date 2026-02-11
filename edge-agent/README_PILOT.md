# DALE Vision — Pilot (Edge Agent Setup em 30 minutos)

## Objetivo
Rodar o agente dentro da loja (sem VPN e sem abrir portas) e enviar apenas:
- status (heartbeat)
- métricas agregadas
- alertas

## Pré-requisitos
- Um PC Windows ligado na loja (na mesma rede do NVR/câmeras)
- Acesso às URLs RTSP (ou ONVIF → RTSP)
- Token do Edge (X-EDGE-TOKEN) e Store ID

## Passo a passo (Setup)
1) Rode `01_setup.bat --run`
2) Vai abrir o navegador em: http://localhost:7860
3) Preencha:
   - Cloud Base URL (padrão dev: http://127.0.0.1:8000)
   - Store ID
   - Edge Token
   Clique em **Salvar Config**
   Dica:
   - local: `DALE_CLOUD_BASE_URL=http://127.0.0.1:8000`
   - prod:  defina `DALE_CLOUD_BASE_URL` no `.env`
4) Para cada câmera:
   - cole a URL RTSP
   - clique **Testar (preview)** (deve aparecer a imagem)
   - preencha o nome e clique **Adicionar câmera**
5) ROI (YAML):
   - Digite o camera_id (ex: cam01)
   - Selecione o arquivo YAML de ROI (ex: config/rois/cam01.yaml)
   - Clique **Upload ROI**
6) Clique **Iniciar agente**
    - Você verá: PID + caminho do log (logs/agent.log)

## Instalação 24/7 (Task Scheduler)
1) Abra PowerShell como administrador (recomendado).
2) Rode o instalador:
   `.\install_edge_agent.ps1 -BaseUrl <URL> -StoreId <UUID> -EdgeToken <TOKEN> -AgentId <ID>`
3) Para rodar mesmo sem usuário logado (boot), passe também:
   `-RunAsPassword <SENHA_DO_USUÁRIO>`
4) Iniciar/parar a task:
   `schtasks /Run /TN "DALE Edge Agent"`
   `schtasks /End /TN "DALE Edge Agent"`
   `schtasks /Delete /TN "DALE Edge Agent" /F`

## Logs (para suporte)
Arquivo: **logs/agent.log**

Para ver as últimas linhas:
- Abra PowerShell na pasta edge-agent e rode:
  `Get-Content .\logs\agent.log -Tail 80`

Logs da Task Scheduler:
Arquivo: **logs/task.out.log** e **logs/task.err.log**
Para ver as últimas linhas:
`Get-Content .\logs\task.out.log -Tail 80`
`Get-Content .\logs\task.err.log -Tail 80`

## Se der erro de porta 7860
A porta já está em uso.
Feche o terminal antigo ou mate o processo:
- `netstat -ano | findstr :7860`
- `taskkill /PID <PID> /F`
