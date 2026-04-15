# Release Runbook

Objetivo: gerar pacote Windows seguro, compatível e registrar a versão publicada no `edge_releases` conforme `EDGE-SYSTEM-002`.

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
  - Padrão estável (recomendado): `https://github.com/okubobarros/dalevision-edge-agent/releases/latest/download/DaleVisionEdgeSetup-latest.exe`.
  - Apenas quando precisar fixar versão: `https://github.com/okubobarros/dalevision-edge-agent/releases/download/vX.Y.Z/DaleVisionEdgeSetup-vX.Y.Z.exe`.

Política de release limpa (obrigatória)
- Nunca commitar `.exe`, `.zip` e artefatos de build no Git.
- Artefatos de distribuição existem somente em GitHub Releases (assets da tag).
- A pipeline publica sempre dois nomes de asset:
  - imutável por versão (`DaleVisionEdgeSetup-vX.Y.Z.exe`, `dalevision-edge-agent-windows.zip`);
  - estável para ambiente (`DaleVisionEdgeSetup-latest.exe`, `dalevision-edge-agent-windows-latest.zip`).
- Em frontend/backend, preferir URL estável (`releases/latest/download/...`) para evitar trocar env a cada release.

Automação da tabela `edge_releases`
- `git push` comum não atualiza release nem a tabela `edge_releases`.
- O gatilho automático é a tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
- A workflow `.github/workflows/release_windows_zip.yml` agora faz 3 coisas no mesmo pipeline:
  - gera `dalevision-edge-agent-windows.zip` e `DaleVisionEdgeSetup-vX.Y.Z.exe`;
  - publica os assets no GitHub Releases;
  - faz `upsert` na tabela `edge_releases`.
- Campos sincronizados automaticamente:
  - `channel`: inferido da tag (`stable` por padrão; tags com `-beta`, `-rc`, `-alpha`, `-canary` mudam o canal).
  - `current_version`: tag sem o prefixo `v`.
  - `minimum_supported_version`: usa a versão ativa anterior do mesmo canal; se não existir, preserva o valor já salvo para a mesma versão; se ainda não existir, usa a própria versão atual.
  - `download_url`: asset ZIP do GitHub Release.
  - `release_notes`: `Edge Agent <versao>`.
  - `package_sha256` e `package_size_bytes`: calculados a partir do ZIP gerado no pipeline.
  - `is_active`: a versão nova fica `true` e as anteriores do mesmo canal são marcadas como `false`.

Pré-requisitos do GitHub
- Configurar o secret `EDGE_RELEASES_DATABASE_URL` com a connection string Postgres/Supabase que tenha permissão de escrita na tabela `edge_releases`.

Backfill/manual
- Para registrar uma release já publicada ou refazer o sync:
```powershell
$env:EDGE_RELEASES_DATABASE_URL="<postgres-connection-string>"
python .\scripts\sync_edge_release.py --tag v1.0.26 --repo okubobarros/dalevision-edge-agent --asset-path .\dalevision-edge-agent-windows.zip
```
- Para forçar manualmente `minimum_supported_version` fora do padrão automático:
```powershell
$env:EDGE_RELEASES_DATABASE_URL="<postgres-connection-string>"
python .\scripts\sync_edge_release.py --tag v1.0.26 --repo okubobarros/dalevision-edge-agent --asset-path .\dalevision-edge-agent-windows.zip --min-supported-version 1.0.24
```
