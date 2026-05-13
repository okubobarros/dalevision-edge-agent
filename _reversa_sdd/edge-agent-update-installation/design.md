# edge-agent-update-installation - Design

## Visão Geral

- 🟢 O mecanismo de update é dividido entre agente Windows e backend DaleVision.
- 🟢 O backend publica política e releases; o agente executa decisão local, download, validação, ativação e reporte.
- 🟢 A arquitetura prioriza operação assistida por suporte: logs com códigos curtos, pacote ZIP autoexplicativo e scripts BAT/PS1 para usuários leigos.
- 🟢 O design evita quebrar heartbeat e camera health: update roda no loop operacional, mas preserva reports e rollback quando health gate falha.

## Componentes

### Edge Agent - update.py

- 🟢 `check_for_update` consulta policy no backend ou fallback legado.
- 🟢 `_is_version_supported` compara versão atual e mínima.
- 🟢 `_sha256_file` calcula checksum local.
- 🟢 `_build_update_report_idempotency_key` gera chave estável sem timestamp.
- 🟢 `acquire_update_lock` e `release_update_lock` controlam concorrência por arquivo.
- 🟢 `download_update` baixa, valida checksum e extrai/identifica executável quando necessário.
- 🟢 `apply_update_if_possible` ativa update quando o processo está rodando como `.exe`.
- 🟢 `send_update_report` envia fases e status para o backend.

### Edge Agent - main.py

- 🟢 O loop operacional chama a checagem de update e, quando aplicável, encadeia lock, download, validação, ativação, reports e release do lock.
- 🟢 `_run_post_update_health_gate` valida heartbeat pós-update com timeouts da policy.
- 🟢 `_rollback_update_if_needed` restaura backup `.exe.bak` quando health gate falha.

### Empacotamento Windows

- 🟢 `scripts/release_windows.ps1` monta `release/win` e gera `dalevision-edge-agent-windows.zip`.
- 🟢 O bundle inclui EXE, modelo YOLO, README, `.env`, scripts BAT/PS1, Inno Setup script e aliases de instalação/desinstalação.
- 🟢 O script valida artefatos críticos antes de comprimir.

### Backend - Edge Models

- 🟢 `EdgeUpdatePolicy` define store, canal, versão alvo, versão mínima, janela de rollout, health gate, rollback e ativação.
- 🟢 `EdgeUpdateEvent` registra eventos com índice por store/timestamp e constraint única por idempotency key.
- 🟢 `EdgeDevice` armazena `installed_version`, `update_channel`, status e `last_seen`.
- 🟢 `EdgeRelease` representa release ativo por canal e metadados de pacote.

### Backend - Release Views

- 🟢 `EdgeReleaseLatestView` retorna release público por canal com fallback para settings.
- 🟢 `EdgeReleaseManagementView` cria/atualiza releases, valida campos e desativa releases anteriores do canal.
- 🟢 `_resolve_windows_setup_url` prioriza `EDGE_WINDOWS_SETUP_URL`, depois release ativo, depois fallback stable.

## Fluxo de Update

1. 🟢 O agente inicia loop com configuração local carregada.
2. 🟢 O agente chama `check_for_update`.
3. 🟢 A função consulta `/api/edge/update-policy/` com token do edge.
4. 🟢 O agente valida formato da policy.
5. 🟢 O agente verifica `current_min_supported`.
6. 🟢 O agente verifica janela de rollout local.
7. 🟢 O agente respeita `AUTO_UPDATE_ENABLED`.
8. 🟢 O agente registra update disponível (`UPD010`) quando aplicável.
9. 🟢 O loop adquire `updates/update.lock`.
10. 🟢 O agente reporta `edge_update_started`.
11. 🟢 O agente baixa pacote para `updates/update-<version>`.
12. 🟢 O agente valida SHA-256.
13. 🟢 O agente reporta `downloaded` e `verified`.
14. 🟢 O agente aplica update com backup.
15. 🟢 O agente executa health gate pós-update.
16. 🟢 Em sucesso, reporta `activated`.
17. 🟢 Em falha, reporta `failed` e tenta rollback.
18. 🟢 O lock é liberado ao final.

## Estados e Transições

| Estado | Origem | Saída | Confiança |
| --- | --- | --- | --- |
| `idle` | Loop sem policy aplicável | nova consulta futura | 🟡 |
| `blocked_policy` | versão mínima, janela, flag ou payload | sem download | 🟢 |
| `locked` | lock local adquirido | download ou falha | 🟢 |
| `downloading` | evento started enviado | checksum | 🟢 |
| `verified` | checksum ok | activation | 🟢 |
| `activated` | executável substituído | health gate | 🟢 |
| `rollback` | health gate falhou | executável anterior restaurado ou falha | 🟢 |
| `failed` | erro em qualquer fase | report com fase/status | 🟢 |

## Dados

### Policy

- 🟢 `target_version`/`version`: versão alvo.
- 🟢 `package.url`/`url`: URL de download.
- 🟢 `package.sha256`/`sha256`: checksum esperado.
- 🟢 `channel`: `stable` por padrão.
- 🟢 `current_min_supported`: versão mínima permitida para update.
- 🟢 `rollout_window.start_local`: início da janela local.
- 🟢 `rollout_window.end_local`: fim da janela local.
- 🟢 `rollout_window.timezone`: timezone da janela.
- 🟢 `health_gate.max_boot_seconds`: tempo máximo de boot.
- 🟢 `health_gate.require_heartbeat_seconds`: prazo para heartbeat.
- 🟢 `health_gate.require_camera_health_count`: quantidade esperada de camera health.

### Report

- 🟢 Report inclui store/agente por contexto autenticado.
- 🟢 Report inclui fase, status, versão e evento.
- 🟢 Idempotency key é derivada de campos estáveis.
- 🟢 Timestamp não participa da chave idempotente.

## Decisões de Design

- 🟢 A política de update fica no backend para permitir rollout centralizado por loja.
- 🟢 A aplicação real é local para manter autonomia do agente em redes de cliente.
- 🟢 O checksum é obrigatório quando informado para evitar ativar artefato corrompido.
- 🟢 A janela inválida falha aberta para evitar brick operacional por policy mal configurada.
- 🟢 O lock em arquivo é suficiente para impedir concorrência local entre loops/processos simples.
- 🟢 A constraint única no backend reduz duplicação causada por retries/reinícios.

## Pontos de Atenção

- 🟡 A ativação de EXE em execução no Windows pode exigir reinício externo ou agendamento pelo serviço, dependendo de como `apply_update_if_possible` manipula o binário ativo.
- 🟡 A exigência de camera health no health gate aparece como parte da policy e pendência, mas a decisão final de bloqueio parece centrada no heartbeat.
- 🟡 Não foi comprovado teste automatizado end-to-end em VM Windows para release/update/rollback.

## Rastreabilidade

- 🟢 `src/dalevision_edge_agent/update.py`.
- 🟢 `src/dalevision_edge_agent/main.py`.
- 🟢 `scripts/release_windows.ps1`.
- 🟢 `src/dalevision_edge_agent/install_service.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 `_reversa_sdd/adrs/0003-edge-update-policy-health-gate.md`.
