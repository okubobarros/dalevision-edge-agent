# empacotar-release-windows - Requirements

## Escopo

- 🟢 Este caso de uso cobre a geração do bundle Windows distribuído aos clientes.
- 🟢 A implementação fonte é `scripts/release_windows.ps1`.
- 🟢 O resultado esperado é `dalevision-edge-agent-windows.zip`.

## Requisitos Funcionais

- 🟢 O operador deve informar `-Version vX.Y.Z`.
- 🟢 O script deve preparar staging em `release/win`.
- 🟢 O script deve usar `dist\dalevision-edge-agent.exe` como EXE principal.
- 🟢 O script deve incluir `yolov8n.pt`.
- 🟢 O script deve copiar `.env.template` como `.env`.
- 🟢 O script deve incluir README e BATs operacionais: teste rápido, instalar autostart, verificar status, remover autostart, parar agente, diagnosticar e executar agente.
- 🟢 O script deve incluir PS1s de instalação, usuário, desinstalação, verificação, parada e update.
- 🟢 O script deve incluir aliases `install_service.ps1` e `uninstall_service.ps1`.
- 🟢 O script deve incluir `Start_DaleVision_Agent.bat` e `Start_DaleVision_Agent.ps1`.
- 🟢 O script deve incluir `DaleVisionEdgeSetup.iss`.
- 🟢 O script deve calcular hashes de `install-service.ps1`, `02_INSTALAR_AUTOSTART.bat` e EXE.
- 🟢 O script deve validar artefatos críticos antes de compactar.
- 🟢 O script deve compactar `release/win/*` em `dalevision-edge-agent-windows.zip`.

## Requisitos Não Funcionais

- 🟢 Operabilidade: scripts devem permitir instalação por usuário leigo com suporte remoto.
- 🟢 Auditabilidade: build info deve registrar versão e hashes críticos.
- 🟢 Compatibilidade: bundle deve manter nomes de BAT/PS1 existentes.
- 🟢 Segurança: `.env` distribuído deve vir de template, sem segredos reais.

## Critérios de Aceitação

### Cenário: bundle gerado

- 🟢 Dado `dist\dalevision-edge-agent.exe`, scripts e assets obrigatórios presentes.
- 🟢 Quando o operador executar `.\scripts\release_windows.ps1 -Version vX.Y.Z`.
- 🟢 Então `dalevision-edge-agent-windows.zip` deve existir e conter EXE, scripts, `.env`, modelo e build info.

### Cenário: artefato obrigatório ausente

- 🟢 Dado que um arquivo crítico não existe.
- 🟢 Quando o script validar a pasta de staging.
- 🟢 Então o script deve falhar antes de gerar release inválido.

## Rastreabilidade

- 🟢 `scripts/release_windows.ps1`.
- 🟢 `_reversa_sdd/deployment.md`.
