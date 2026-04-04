# Release Runbook

Objetivo: gerar pacote Windows seguro e compatível.

Checklist
- Build com PyInstaller/pipeline oficial.
- Rodar `scripts/release_windows.ps1 -Version vX.Y.Z`.
- Verificar bloqueios automáticos: não incluir `tools/`, `outputs/`, `configs/*.yaml`, vídeos (`*.mp4` etc.), pesos (`*.pt`), arquivos `.env`/logs.
- Conferir bundle contém `Start_DaleVision_Agent.bat/.ps1` e tasks de autostart/update.
- Testar smoke: `01_TESTE_RAPIDO.bat` em VM limpa.
- Publicar ZIP: `dalevision-edge-agent-windows.zip` + checksums.
- Registrar versão mínima suportada no protocolo e compatibilidade de update.
- Criar tag nova: `git tag vX.Y.Z && git push origin vX.Y.Z`.
- Atualizar URLs de distribuição:
  - `EDGE_WINDOWS_SETUP_URL` (Render/infra)
  - `VITE_EDGE_AGENT_DOWNLOAD_URL` (Vercel FE)
  - Formato: `https://github.com/okubobarros/dalevision-edge-agent/releases/download/vX.Y.Z/DaleVisionEdgeSetup-vX.Y.Z.exe`.
