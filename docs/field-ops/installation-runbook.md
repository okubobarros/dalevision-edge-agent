# Installation Runbook (Windows)

Pré-requisitos
- Acesso admin, firewall permitindo saída HTTPS para `CLOUD_BASE_URL`.
- Variáveis: `CLOUD_BASE_URL`, `STORE_ID`, `EDGE_TOKEN`, `AGENT_ID`.

Passos
1. Baixar ZIP oficial e extrair.
2. Preencher `.env` com variáveis acima.
3. Testar: `01_TESTE_RAPIDO.bat` (esperar `status=201`).
4. Produção: `02_INSTALAR_AUTOSTART.bat` (admin) e reiniciar PC.
5. Verificar: `03_VERIFICAR_STATUS.bat`.
6. Remover: `04_REMOVER_AUTOSTART.bat`.

Evidências
- Logs de instalação, saída do teste rápido, heartbeat visível no backend.
