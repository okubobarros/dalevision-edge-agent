# Inicialização CLI, Tasks

## Tarefas

- [ ] T-CLI-01, Implementar parser CLI.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_parse_args`
  - Critério de pronto: todos os comandos documentados em `requirements.md` são aceitos.
  - Confiança: 🟢

- [ ] T-CLI-02, Implementar logger idempotente.
  - Origem no legado: `src/dalevision_edge_agent/main.py` `_setup_logging`
  - Critério de pronto: logger possui handler rotacionado e não duplica handlers em chamadas repetidas.
  - Confiança: 🟢

- [ ] T-CLI-03, Implementar roteamento de subcomandos.
  - Origem no legado: `src/dalevision_edge_agent/main.py`
  - Critério de pronto: `doctor`, `setup-api`, `scan` e `test-rtsp` executam fluxo dedicado sem entrar no loop contínuo.
  - Confiança: 🟢

- [ ] T-CLI-04, Integrar resolução de versão e paths.
  - Origem no legado: `main.py` `_get_version`; `paths.py` `resolve_runtime_paths`
  - Critério de pronto: versão e paths são resolvidos antes dos fluxos que dependem de logs/config/cache.
  - Confiança: 🟢

## Testes

- [ ] TT-CLI-01, Parser reconhece todos os subcomandos.
- [ ] TT-CLI-02, `_setup_logging()` chamado duas vezes não duplica handlers.
- [ ] TT-CLI-03, `doctor` não aciona heartbeat loop.
- [ ] TT-CLI-04, config ausente retorna erro claro.

## Lacunas

- 🔴 Confirmar contrato final de exit codes para processos chamados por task scheduler.
