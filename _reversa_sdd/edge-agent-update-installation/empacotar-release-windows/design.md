# empacotar-release-windows - Design

## Visão Geral

- 🟢 O empacotamento é um script PowerShell local que transforma artefatos de build em um ZIP operacional para Windows.
- 🟢 O script separa staging (`release/win`) do artefato final (`dalevision-edge-agent-windows.zip`).
- 🟢 O design inclui tanto execução direta quanto instalação/autostart/update por scripts auxiliares.

## Entradas

- 🟢 Parâmetro `Version`.
- 🟢 `dist\dalevision-edge-agent.exe`.
- 🟢 `yolov8n.pt`.
- 🟢 `.env.template`.
- 🟢 Scripts BAT/PS1 de operação.
- 🟢 `DaleVisionEdgeSetup.iss`.

## Saídas

- 🟢 `release/win/` populado com bundle final.
- 🟢 `dalevision-edge-agent-windows.zip`.
- 🟢 Build info com versão e hashes.

## Etapas

1. 🟢 Resolver paths de release e staging.
2. 🟢 Limpar/preparar `release/win`.
3. 🟢 Copiar EXE principal.
4. 🟢 Copiar modelo YOLO e README.
5. 🟢 Copiar `.env.template` para `.env`.
6. 🟢 Copiar BATs operacionais.
7. 🟢 Copiar scripts PS1 e aliases.
8. 🟢 Copiar scripts internos `Start_DaleVision_Agent`.
9. 🟢 Calcular hashes críticos.
10. 🟢 Validar arquivos obrigatórios.
11. 🟢 Compactar staging em ZIP.
12. 🟢 Exibir orientação de publicação em GitHub Release.

## Decisões

- 🟢 `.env` no bundle vem de template para não embutir segredos.
- 🟢 `nssm.exe` é opcional, preservando compatibilidade com instalações sem NSSM.
- 🟢 Hashes são registrados para permitir suporte diagnosticar pacote divergente.
- 🟢 O ZIP contém scripts de suporte para reduzir dependência de linha de comando avançada no cliente.

## Falhas

- 🟢 Falta de arquivo crítico deve interromper release.
- 🟡 Falha de permissão em `release/` ou arquivo aberto pode impedir staging.
- 🟡 Build PyInstaller fora do caminho esperado exige ajuste manual antes do script.

## Rastreabilidade

- 🟢 `scripts/release_windows.ps1`.
