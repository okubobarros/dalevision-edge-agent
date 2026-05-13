# edge-agent-update-installation - Requirements

## Escopo

- 🟢 Esta unit cobre empacotamento Windows, publicação de release, consulta de política de atualização, download, validação, ativação, health gate pós-update, rollback e reporte de eventos entre o agente local e o backend DaleVision.
- 🟢 A responsabilidade local está principalmente em `src/dalevision_edge_agent/update.py`, `src/dalevision_edge_agent/main.py`, `src/dalevision_edge_agent/install_service.py` e `scripts/release_windows.ps1`.
- 🟢 A responsabilidade cloud está principalmente em `apps/edge/models.py`, `apps/stores/views_activation.py` e nas configurações `EDGE_RELEASE_*`/`EDGE_WINDOWS_SETUP_URL` em `backend/settings.py` no repositório `C:\workspace\dale-vision`.
- 🟡 Esta unit depende de `edge-agent-runtime` para loop operacional, configuração local e execução do processo como EXE/serviço.
- 🟡 Esta unit depende de `stores`/`edge` para autenticação, distribuição da policy e persistência dos eventos de update.

## Objetivos

- 🟢 Permitir que o agente Windows descubra uma atualização disponível por política remota ou URL legado.
- 🟢 Evitar update fora da janela de rollout local configurada.
- 🟢 Bloquear update quando a versão atual está abaixo da versão mínima suportada pela política.
- 🟢 Baixar pacote, validar SHA-256 e impedir ativação de artefato inválido.
- 🟢 Impedir concorrência local por `updates/update.lock`.
- 🟢 Ativar o novo executável com backup do executável anterior.
- 🟢 Validar health gate pós-update por heartbeat e pendência de camera health.
- 🟢 Reportar fases do update ao backend com chave idempotente estável.
- 🟢 Gerar ZIP de release Windows contendo EXE, scripts operacionais, `.env` template, modelo YOLO e arquivos de autostart/update.

## Requisitos Funcionais

### RF-001 - Consultar política de update

- 🟢 O agente deve consultar `/api/edge/update-policy/` quando `cloud_base_url` e `edge_token` estiverem disponíveis.
- 🟢 O agente deve aceitar fallback por `update_check_url` para compatibilidade com mecanismo legado.
- 🟢 A resposta deve aceitar campos `target_version` ou `version`, `package.url` ou `url`, `package.sha256` ou `sha256`, `channel`, `current_min_supported`, `rollout_window` e `health_gate`.
- 🟢 Payload inválido deve registrar `UPD002` e não deve iniciar download.

### RF-002 - Aplicar política de versão mínima

- 🟢 O agente deve comparar `current_version` com `current_min_supported` usando tuplas numéricas de versão.
- 🟢 Quando a versão atual estiver abaixo do mínimo, o update deve ser bloqueado em `policy_check`.
- 🟢 O bloqueio deve gerar log `UPD015` e dados de retorno com `blocked_phase="policy_check"`.

### RF-003 - Aplicar janela de rollout

- 🟢 O agente deve avaliar `rollout_window.start_local`, `rollout_window.end_local` e `rollout_window.timezone`.
- 🟢 Fora da janela, o update deve ser bloqueado e logar `UPD016`.
- 🟢 Janela inválida deve falhar aberto para evitar travar atualizações por erro de configuração.

### RF-004 - Respeitar flag de auto-update

- 🟢 Quando `AUTO_UPDATE_ENABLED=0`, o agente deve detectar update disponível, mas bloquear aplicação automática.
- 🟢 O bloqueio por flag deve registrar `UPD011`.

### RF-005 - Usar lock local de update

- 🟢 Antes de baixar/aplicar update, o agente deve criar `updates/update.lock`.
- 🟢 Lock ativo deve bloquear novo update com erro `UPDATE_LOCKED`.
- 🟢 Lock expirado por TTL deve ser tratado como stale e substituído.
- 🟢 Ao final do fluxo, o agente deve liberar o lock.

### RF-006 - Baixar e validar pacote

- 🟢 O download deve salvar em `updates/update-<version>`.
- 🟢 O timeout de download deve ser 15 segundos.
- 🟢 Quando `sha256` for informado, o agente deve calcular SHA-256 local e comparar com a política.
- 🟢 Checksum divergente deve registrar `UPD021`, apagar o artefato baixado e impedir ativação.
- 🟢 ZIP sem executável deve registrar `UPD022 zip sem exe` e impedir ativação.
- 🟢 Download válido deve registrar `UPD022 download ok`.

### RF-007 - Ativar executável com backup

- 🟢 O agente deve aplicar update somente quando estiver rodando como executável `.exe`.
- 🟢 Antes de substituir o executável atual, o agente deve manter backup `.exe.bak`.
- 🟡 A ativação completa pode depender de reinício externo do processo/serviço Windows.

### RF-008 - Executar health gate pós-update

- 🟢 Após ativação, o agente deve exigir heartbeat bem-sucedido dentro do timeout configurado.
- 🟢 Defaults do health gate: `max_boot_seconds=120`, `require_heartbeat_seconds=180`, `require_camera_health_count=3`.
- 🟢 Falha de heartbeat deve registrar `UPD041 health gate failed heartbeat...`.
- 🟡 A exigência de camera health é registrada como pendência operacional, não como bloqueio totalmente comprovado no trecho analisado.

### RF-009 - Executar rollback quando necessário

- 🟢 Quando health gate falhar e existir backup `.exe.bak`, o agente deve tentar rollback.
- 🟢 Rollback bem-sucedido deve registrar `UPD050 rollback aplicado`.
- 🟢 Rollback com falha deve registrar `UPD051 rollback falhou`.

### RF-010 - Reportar eventos de update

- 🟢 O agente deve enviar eventos para `/api/edge/update-report/`.
- 🟢 A chave de idempotência deve ser estável por fase/status/versão e não deve incluir timestamp.
- 🟢 Falha no envio de report deve registrar `UPD050` e não deve vazar segredos.
- 🟢 O backend deve persistir `EdgeUpdateEvent` com constraint única por chave idempotente.

### RF-011 - Publicar release Windows

- 🟢 O script `scripts/release_windows.ps1` deve montar staging em `release/win`.
- 🟢 O ZIP final deve ser `dalevision-edge-agent-windows.zip`.
- 🟢 O bundle deve incluir `dalevision-edge-agent.exe`, `yolov8n.pt`, `.env`, scripts BAT/PS1 de instalação, diagnóstico, autostart, update e verificação.
- 🟢 O script deve validar artefatos críticos antes de compactar.
- 🟢 O script deve escrever hashes de `install-service.ps1`, `02_INSTALAR_AUTOSTART.bat` e EXE no build info.

### RF-012 - Servir release pelo backend

- 🟢 O backend deve expor release ativo por canal `stable` ou `canary`.
- 🟢 Quando não houver `EdgeRelease` ativo, o backend deve usar fallback de settings `EDGE_RELEASE_*`.
- 🟢 A URL de setup Windows deve vir de `EDGE_WINDOWS_SETUP_URL`, depois de `EdgeRelease.download_url`, depois de `EDGE_RELEASE_STABLE_URL`.
- 🟢 O endpoint de gerenciamento deve validar `version`, `download_url` e canal antes de criar/atualizar release.
- 🟢 Ao ativar novo release de canal, releases anteriores do mesmo canal devem ser desativados.

## Requisitos Não Funcionais

- 🟢 Segurança: logs e reports não devem registrar `EDGE_TOKEN`, senhas ou segredos.
- 🟢 Confiabilidade: update usa lock local, checksum, backup e rollback.
- 🟢 Observabilidade: eventos usam fases e status explícitos (`policy_check`, `download`, `checksum`, `activation`; `started`, `downloaded`, `verified`, `activated`, `failed`).
- 🟢 Compatibilidade: fallback por `update_check_url` mantém protocolo legado.
- 🟢 Suporte remoto: códigos curtos `UPD*` permitem diagnóstico por log.
- 🟢 Operabilidade Windows: release inclui BAT/PS1 para instalação, verificação, diagnóstico, parada e remoção de autostart.

## MoSCoW

- **Must** 🟢: consulta de policy, bloqueio por versão mínima, janela de rollout, lock, download, SHA-256, backup, health gate por heartbeat, rollback e reports idempotentes.
- **Should** 🟢: release por canal `stable`/`canary`, fallback de settings e script de ZIP com validação de artefatos.
- **Could** 🟡: endurecer validação da exigência de camera health no health gate.
- **Won't** 🟢: atualizar automaticamente quando `AUTO_UPDATE_ENABLED=0`.

## Critérios de Aceitação

### Cenário: update disponível e válido

- 🟢 Dado um agente com `cloud_base_url`, `edge_token`, versão atual suportada e `AUTO_UPDATE_ENABLED` habilitado.
- 🟢 Quando `/api/edge/update-policy/` retornar `target_version`, URL e SHA-256 válidos dentro da janela de rollout.
- 🟢 Então o agente deve adquirir lock, baixar pacote, validar checksum, ativar update e reportar eventos até `activated`.

### Cenário: checksum inválido

- 🟢 Dado uma policy com `sha256` diferente do arquivo baixado.
- 🟢 Quando o download terminar.
- 🟢 Então o agente deve registrar `UPD021`, remover o arquivo baixado, reportar falha de checksum e não substituir o executável atual.

### Cenário: fora da janela de rollout

- 🟢 Dado uma policy com janela local configurada.
- 🟢 Quando o horário atual estiver fora de `start_local` e `end_local`.
- 🟢 Então o agente deve registrar `UPD016`, bloquear aplicação e reportar bloqueio/falha em `policy_check`.

### Cenário: health gate falha

- 🟢 Dado um update ativado com backup `.exe.bak`.
- 🟢 Quando o heartbeat pós-update não for confirmado dentro do timeout exigido.
- 🟢 Então o agente deve registrar falha de health gate e tentar rollback para o executável anterior.

### Cenário: release Windows empacotado

- 🟢 Dado `dist\dalevision-edge-agent.exe` e artefatos obrigatórios presentes.
- 🟢 Quando `.\scripts\release_windows.ps1 -Version vX.Y.Z` for executado.
- 🟢 Então `dalevision-edge-agent-windows.zip` deve ser gerado com EXE, scripts operacionais, `.env`, modelo YOLO e build info com hashes.

## Rastreabilidade

- 🟢 Edge local: `src/dalevision_edge_agent/update.py`.
- 🟢 Loop/health gate local: `src/dalevision_edge_agent/main.py`.
- 🟢 Resolver scripts de instalação: `src/dalevision_edge_agent/install_service.py`.
- 🟢 Empacotamento: `scripts/release_windows.ps1`.
- 🟢 Modelos backend: `C:\workspace\dale-vision\apps\edge\models.py`.
- 🟢 Releases backend: `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 Settings backend: `C:\workspace\dale-vision\backend\settings.py`.
- 🟢 Decisão arquitetural: `_reversa_sdd/adrs/0003-edge-update-policy-health-gate.md`.
