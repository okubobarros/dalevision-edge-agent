# Harness Progress

## Semana de 2026-04-14

### Top friccoes
1. Onboarding de loja/camera com baixa previsibilidade de resultado.
2. Diagnostico nem sempre conclusivo na primeira tentativa.
3. Variacao de setup local sem gate unico antes de release.
4. Handoff LGPD -> dashboard no frontend com rebound para `/onboarding` e abertura inconsistente do modal de ativacao.

### Hipoteses
- H1: Um gate unico (`harness_check.ps1`) reduz regressao operacional.
- H2: Menos documentos e mais atualizacao em docs centrais reduz retrabalho.

### Acoes em andamento
- [x] Criar estrutura `docs/harness`.
- [x] Publicar spec oficial `EDGE-SYSTEM-003-onboarding-frictionless.md`.
- [x] Adicionar script de sensor local (`scripts/harness_check.ps1`).
- [x] Triangular gaps e fases com `C:\workspace\dale-vision` (backend/frontend/db).
- [x] Consolidar docs do repo para nucleo essencial (README/progress/sensors + specs EDGE-SYSTEM).
- [x] Etapa 1 (Edge): telemetria de onboarding no runtime (`onboarding_started`, `agent_first_heartbeat`, `activation_failed`).
- [x] Etapa 2 (Edge): telemetria de discovery/validacao (`camera_discovered`, `camera_validated`, `activation_completed`) + campos opcionais no heartbeat (`onboarding_ref`, `agent_capabilities`).
- [x] Normalizar `error_code` no `activation_failed` (heartbeat + camera health) com deduplicacao de eventos.
- [x] Politica de release limpa: assets versionados + aliases `latest` no GitHub Releases, sem binarios no git.
- [x] Frontend (`dale-vision`): remover CTA de falso positivo ("Já concluí a instalação") no wizard e manter espera por heartbeat automático.
- [ ] Dashboard com taxa de ativacao e tempo para ativar.
- [x] Etapa 0 (`activation_state`) implementada no `dale-vision` (backend/status/download + testes).
- [x] Smart Download 100% frictionless no `dale-vision`: setup com token efêmero embutido no filename (`_tk_`) e fluxo padrão sem dependência de CMD.
- [x] Diagnostico cross-repo de rebound no fim do LGPD e ausencia do modal edge (INC-007 no `dale-vision`).
- [ ] Corrigir corrida de redirecionamento no frontend (`Onboarding.tsx` + `Dashboard.tsx`) e validar 10/10 sem rebound.
- [ ] Validar E2E real em homologação (download -> install -> heartbeat -> câmera -> ROI -> activation_completed).

### Decisoes
- Manter compatibilidade do protocolo heartbeat/camera health como restricao dura.
- Mensagens e codigos de erro curtos, orientados a operador leigo.

### Evidencias
- Artefatos: `docs/harness/*`, `scripts/harness_check.ps1`, `specs/EDGE-SYSTEM-003-onboarding-frictionless.md`.
- Escopo cross-repo consolidado na `EDGE-SYSTEM-003` e no backlog de execucao do time.
- Testes/gates: registrar aqui cada execucao de release.
- Incidente ativo de UX: `dale-vision/docs/operations/incidents/INC-007-onboarding-lgpd-handoff-loop-and-missing-edge-modal.md`.

### Proxima semana
1. Fechar nomenclatura final de eventos de onboarding.
2. Publicar runbook de ativacao com exemplos de erro/correcao.
3. Definir metas oficiais de funil por ambiente (piloto/producao).
