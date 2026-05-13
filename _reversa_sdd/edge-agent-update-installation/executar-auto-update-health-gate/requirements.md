# executar-auto-update-health-gate - Requirements

## Escopo

- 🟢 Este caso de uso cobre a execução automática do update no agente, incluindo policy, lock, download, checksum, ativação, health gate, rollback e reports.
- 🟢 Fontes principais: `src/dalevision_edge_agent/update.py` e `src/dalevision_edge_agent/main.py`.

## Requisitos Funcionais

- 🟢 O agente deve consultar policy antes de baixar qualquer artefato.
- 🟢 O agente deve bloquear update se a versão atual estiver abaixo de `current_min_supported`.
- 🟢 O agente deve respeitar rollout window local.
- 🟢 O agente deve respeitar `AUTO_UPDATE_ENABLED=0`.
- 🟢 O agente deve adquirir lock antes de iniciar download.
- 🟢 O agente deve enviar report `edge_update_started`.
- 🟢 O agente deve baixar pacote com timeout.
- 🟢 O agente deve validar SHA-256 quando informado.
- 🟢 O agente deve impedir ativação de ZIP sem EXE.
- 🟢 O agente deve aplicar update apenas quando estiver executando como `.exe`.
- 🟢 O agente deve manter backup `.exe.bak`.
- 🟢 O agente deve validar heartbeat pós-update dentro do prazo.
- 🟢 O agente deve tentar rollback quando health gate falhar.
- 🟢 O agente deve reportar fases e status com idempotency key estável.
- 🟢 O agente deve liberar lock ao final.

## Requisitos Não Funcionais

- 🟢 Confiabilidade: falhas em download/checksum/health gate não devem deixar executável atual corrompido.
- 🟢 Observabilidade: logs devem usar códigos `UPD*` e reports estruturados.
- 🟢 Segurança: reports e logs não devem conter `EDGE_TOKEN` ou segredos.
- 🟢 Compatibilidade: fallback `update_check_url` deve continuar existindo.

## Critérios de Aceitação

### Cenário: update aplicado

- 🟢 Dado policy válida, checksum correto e janela aberta.
- 🟢 Quando o loop de update executar.
- 🟢 Então o agente deve baixar, validar, ativar, confirmar health gate e reportar `activated`.

### Cenário: update bloqueado por flag

- 🟢 Dado `AUTO_UPDATE_ENABLED=0`.
- 🟢 Quando policy indicar update disponível.
- 🟢 Então o agente deve registrar `UPD011`, não baixar pacote e não ativar update.

### Cenário: falha no health gate

- 🟢 Dado update ativado e backup disponível.
- 🟢 Quando heartbeat não for confirmado no prazo.
- 🟢 Então o agente deve registrar `UPD041`, tentar rollback e reportar falha.

## Rastreabilidade

- 🟢 `src/dalevision_edge_agent/update.py`.
- 🟢 `src/dalevision_edge_agent/main.py`.
- 🟢 `C:\workspace\dale-vision\apps\edge\models.py`.
