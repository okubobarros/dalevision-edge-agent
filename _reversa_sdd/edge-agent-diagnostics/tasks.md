# Edge Agent Diagnostics, Tasks

## Status da Unit

🟢 CONFIRMADO: A implementação principal desta unit já existe no legado e possui testes unitários para parse de rede, geração de summary, ZIP compartilhável, fallback RTSP Digest, readiness e installation check.

## Tarefas Funcionais

| ID | Tarefa | Status | Evidência | Confiança |
|----|--------|--------|-----------|-----------|
| T-01 | Mapear comandos CLI `doctor` e `diagnostics`. | [X] | `src/dalevision_edge_agent/main.py` `_parse_args()` e roteamento em `main()`. | 🟢 |
| T-02 | Documentar coleta de rede Windows. | [X] | `diagnostics.py` `_run_cmd()`, `run_doctor()`. | 🟢 |
| T-03 | Documentar parsing de IP, máscara, gateway e DNS. | [X] | `diagnostics.py` `_parse_ipconfig()`; `tests/test_doctor_pytest.py`. | 🟢 |
| T-04 | Documentar cálculo de CIDR e detecção de segmentação. | [X] | `_compute_cidr()`, `network_segmented`, `_is_segmented()`. | 🟢 |
| T-05 | Documentar checks de cloud, DNS, internet, disco e permissão. | [X] | `_api_check()`, `_dns_check()`, `_internet_check()`, `_disk_check()`, `_permissions_check()`. | 🟢 |
| T-06 | Documentar autenticação edge em múltiplos endpoints. | [X] | `_edge_auth_check()`. | 🟢 |
| T-07 | Documentar geração de JSON/TXT e ZIP compartilhável. | [X] | `run_doctor()`, `_build_share_zip()`. | 🟢 |
| T-08 | Documentar teste RTSP por canal e scan de canais. | [X] | `rtsp_test.py`, CLI `test-rtsp`. | 🟢 |
| T-09 | Documentar fallback RTSP para desafio Digest. | [X] | `tests/test_rtsp_test_fallback.py`. | 🟢 |
| T-10 | Documentar readiness de onboarding e export JSON/Markdown. | [X] | `onboarding_readiness.py`, `tests/test_onboarding_readiness.py`. | 🟢 |
| T-11 | Documentar installation check do pacote release. | [X] | `installation_check.py`, `tests/test_installation_check.py`. | 🟢 |
| T-12 | Documentar rotas diagnósticas da Setup API. | [X] | `setup_api.py`. | 🟢 |

## Tarefas de Validação Recomendadas

| ID | Tarefa | Status | Justificativa | Prioridade |
|----|--------|--------|---------------|------------|
| V-01 | Criar teste que valide que `diagnostics-share-*.zip` contém JSON, TXT e logs esperados. | [ ] | Hoje o teste valida criação do ZIP, mas não seu conteúdo completo. | Should |
| V-02 | Criar teste de redaction para garantir que senha RTSP não aparece em logs de `test-rtsp`. | [ ] | O código usa máscara, mas o contrato de segurança merece teste explícito. | Must |
| V-03 | Criar sanitizador para `commands` antes de ZIP compartilhável. | [ ] | Reduz risco de vazar SSID, MACs, hostname e topologia local. | Should |
| V-04 | Validar `doctor --share` em Windows limpo com `%LOCALAPPDATA%` e usuário sem admin. | [ ] | Ambiente real pode divergir dos testes com `tmp_path`. | Should |
| V-05 | Validar health check de cloud contra endpoints reais do backend em produção/staging. | [ ] | GET no base URL pode não representar disponibilidade da API autenticada. | Should |
| V-06 | Migrar `/onboarding/test-camera` para evitar senha em query string quando possível. | [ ] | Query string pode ficar em histórico local; POST seria mais seguro. | Could |
| V-07 | Definir política de retenção de `diagnostics-*` e `diagnostics-share-*`. | [ ] | Evita acúmulo e exposição prolongada de dados locais. | Should |

## Testes Existentes

| Teste | Cobertura | Confiança |
|-------|-----------|-----------|
| `tests/test_doctor_pytest.py::test_parse_ipconfig_extracts_ipv4_and_gateway` | Parse de IPv4, máscara e gateway. | 🟢 |
| `tests/test_doctor_pytest.py::test_doctor_generates_summary` | Geração de payload com summary. | 🟢 |
| `tests/test_doctor_pytest.py::test_doctor_share_zip` | Criação do ZIP compartilhável. | 🟢 |
| `tests/test_doctor_pytest.py::test_segmented_network_detects_different_subnet` | Detecção de rede segmentada no RTSP test. | 🟢 |
| `tests/test_rtsp_test_fallback.py` | Fallback de Digest challenge para conectividade simples. | 🟢 |
| `tests/test_installation_check.py` | Status `ready`, `blocked`, `needs_attention`. | 🟢 |
| `tests/test_onboarding_readiness.py` | Readiness pronto, scan, render Markdown e export. | 🟢 |
| `tests/test_onboarding_error_codes.py` | Mapeamento de erros para códigos operacionais. | 🟢 |

## Checklist de Reimplementação

- [ ] Preservar aliases CLI `doctor` e `diagnostics`.
- [ ] Preservar formato dos arquivos `diagnostics-<id>.json`, `diagnostics-<id>.txt` e `diagnostics-share-<id>.zip`.
- [ ] Preservar códigos curtos `NET001`, `NET002`, `RTSP554`, `RTSP401`, `RTSPTO`.
- [ ] Preservar suporte a aliases de env `DALE_CLOUD_BASE_URL`, `DALE_STORE_ID` e `DALE_EDGE_TOKEN`.
- [ ] Preservar fallback RTSP para `unauthorized` inicial por Digest challenge.
- [ ] Preservar status `ready`, `needs_attention` e `blocked` nos checks de readiness/installation.
- [ ] Não registrar token edge, senha de NVR ou URL RTSP com senha em claro.
- [ ] Tratar diagnóstico compartilhável como artefato sensível.

## Ordem Recomendada

1. Implementar contratos de payload e snapshots de teste para `run_doctor()`.
2. Implementar coleta de rede com adaptadores para Windows e mocks de teste.
3. Implementar redaction/sanitização antes de gravação/ZIP.
4. Implementar RTSP test com máscara de senha e fallback Digest.
5. Implementar readiness e installation check como funções puras testáveis.
6. Expor CLI e rotas Setup API reutilizando as funções puras.
7. Validar em Windows real com NVR em mesma VLAN e VLAN diferente.
