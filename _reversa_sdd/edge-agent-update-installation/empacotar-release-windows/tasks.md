# empacotar-release-windows - Tasks

- [ ] 🟢 Implementar parâmetro obrigatório de versão.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: execução aceita `-Version vX.Y.Z` e usa essa versão no build info.

- [ ] 🟢 Preparar staging `release/win`.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: staging é criado/atualizado antes da cópia dos artefatos.

- [ ] 🟢 Copiar executável principal.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: `dist\dalevision-edge-agent.exe` aparece no bundle.

- [ ] 🟢 Copiar assets e configuração base.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: `yolov8n.pt`, README e `.env` derivado de `.env.template` aparecem no bundle.

- [ ] 🟢 Copiar scripts operacionais.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: BATs e PS1s de instalação, verificação, diagnóstico, update e remoção aparecem no bundle.

- [ ] 🟢 Registrar hashes críticos.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: build info contém hash de `install-service.ps1`, `02_INSTALAR_AUTOSTART.bat` e EXE.

- [ ] 🟢 Validar artefatos obrigatórios.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: script falha antes do ZIP se faltar item crítico.

- [ ] 🟢 Gerar ZIP final.
  - Fonte: `scripts/release_windows.ps1`.
  - Critério de pronto: `dalevision-edge-agent-windows.zip` contém o conteúdo de `release/win/*`.

- [ ] 🟡 Criar smoke test pós-ZIP.
  - Fonte: lacuna operacional.
  - Critério de pronto: teste extrai ZIP em pasta temporária e valida presença/execução básica de scripts sem segredos.
