# Estado Local e Configuração, Tasks

## Tarefas

- [ ] T-CONF-01, Implementar resolução de config path.
  - Origem no legado: `src/dalevision_edge_agent/activation.py` `ConfigManager.from_default`
  - Critério de pronto: respeita `DALE_AGENT_CONFIG_PATH`, depois `DALE_CONFIG_DIR`, depois cwd.
  - Confiança: 🟢

- [ ] T-CONF-02, Implementar load/save/update parcial de config.
  - Origem no legado: `ConfigManager.load`, `save`, `update_partial`
  - Critério de pronto: JSON inválido retorna dict vazio; save cria diretório pai.
  - Confiança: 🟢

- [ ] T-CONF-03, Implementar resolução de paths AppData.
  - Origem no legado: `src/dalevision_edge_agent/paths.py`
  - Critério de pronto: cria app/config/log/cache/tmp com fallback seguro.
  - Confiança: 🟢

- [ ] T-CONF-04, Implementar hidratação de `.env`.
  - Origem no legado: `activation.py` `hydrate_runtime_env_from_activation_config`
  - Critério de pronto: escreve cloud/store/token/agent preservando linhas existentes quando possível.
  - Confiança: 🟢

- [ ] T-CONF-05, Implementar redaction/segurança de logs.
  - Origem no legado: `activation.py`; `setup_api.py` `_redact_sensitive_text`
  - Critério de pronto: token e senha RTSP não aparecem em logs de teste.
  - Confiança: 🟢

- [ ] T-CONF-06, Implementar limpeza de tmp antigo.
  - Origem no legado: `paths.py` `cleanup_old_runtime_tmp`
  - Critério de pronto: remove apenas filhos sob `runtime_tmp_root`, preserva últimos diretórios e reporta erros.
  - Confiança: 🟢

## Testes

- [ ] TT-CONF-01, Precedência de path explícito.
- [ ] TT-CONF-02, Fallback para `DALE_CONFIG_DIR`.
- [ ] TT-CONF-03, Fallback para cwd.
- [ ] TT-CONF-04, `.env` hidratado sem token em log.
- [ ] TT-CONF-05, cleanup não remove fora de `runtime_tmp_root`.

## Lacunas

- 🔴 Definir ACL/permissões finais esperadas nos arquivos locais em Windows de cliente.
