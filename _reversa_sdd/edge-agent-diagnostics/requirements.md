# Edge Agent Diagnostics

## Visão Geral

🟢 CONFIRMADO: Esta unit define os fluxos locais de diagnóstico do DaleVision Edge Agent usados por suporte remoto e onboarding em campo. Ela cobre o comando `doctor`/`diagnostics`, teste RTSP, readiness de onboarding, installation check e rotas equivalentes da Setup API local.

🟢 CONFIRMADO: O objetivo operacional é diagnosticar rede, cloud, DNS, internet, permissão de escrita, suporte a snapshot, autenticação edge, portas do NVR, segmentação de rede/VLAN e conectividade RTSP sem quebrar o loop principal de heartbeat e camera health.

## Responsabilidades

- 🟢 CONFIRMADO: Coletar dados de rede Windows via `ipconfig /all`, `route print`, `arp -a` e `netsh wlan show interfaces`.
- 🟢 CONFIRMADO: Gerar resumo textual copiável para suporte com `ts`, cloud, IP local, máscara, CIDR, gateway, DNS, ping, internet, API, snapshot, escrita e autenticação edge.
- 🟢 CONFIRMADO: Persistir diagnóstico em JSON e TXT no diretório de logs resolvido por `DALE_LOG_DIR`, `%LOCALAPPDATA%\DaleVision\logs` ou `logs/`.
- 🟢 CONFIRMADO: Gerar ZIP compartilhável com diagnóstico e logs quando `--share` for usado.
- 🟢 CONFIRMADO: Detectar NVR fora do subnet local e emitir ação sugerida `NET002`.
- 🟢 CONFIRMADO: Testar portas conhecidas do NVR: `80`, `443`, `554` e `37777`.
- 🟢 CONFIRMADO: Validar autenticação edge tentando endpoints de cameras com `EDGE_TOKEN`.
- 🟢 CONFIRMADO: Testar RTSP Intelbras/Dahua por canal/subtype, mascarando senha em logs.
- 🟢 CONFIRMADO: Validar readiness de onboarding com env obrigatório, settings, ffmpeg e scan opcional.
- 🟢 CONFIRMADO: Validar pacote local com scripts `.bat` esperados e runner `.cmd`/`.exe`.

## Regras de Negócio

- 🟢 CONFIRMADO: `doctor` e `diagnostics` são aliases operacionais; ambos chamam `run_doctor()`.
- 🟢 CONFIRMADO: Ausência de `CLOUD_BASE_URL` gera `api_check.ok=false` com erro `missing_cloud_base_url`, mas o diagnóstico ainda é gerado.
- 🟢 CONFIRMADO: Ausência de `STORE_ID` ou `EDGE_TOKEN` gera `edge_auth_check.ok=false` com erro `missing_store_or_token`.
- 🟢 CONFIRMADO: Se `--nvr-ip` estiver fora do CIDR local calculado, `network_segmented=true` e o resumo deve orientar conectar o PC na mesma VLAN do NVR.
- 🟢 CONFIRMADO: Se `--nvr-ip` for informado e a porta `554` não estiver aberta, a ação sugerida deve incluir `RTSP554 Porta 554 fechada no NVR`.
- 🟢 CONFIRMADO: Snapshot é considerado disponível quando `ffmpeg` existe ou OpenCV está disponível.
- 🟢 CONFIRMADO: Teste RTSP com erro `unauthorized` tenta fallback sem DESCRIBE para lidar com desafio Digest inicial de NVRs.
- 🟢 CONFIRMADO: Erro RTSP `unauthorized` retorna mensagem `RTSP401 credencial invalida`.
- 🟢 CONFIRMADO: Erro RTSP `timeout` em rede segmentada retorna mensagem `NET002 NVR fora do subnet local (VLAN diferente)`.
- 🟢 CONFIRMADO: Readiness bloqueia quando variáveis obrigatórias faltam; warning de `ffmpeg_missing` não bloqueia.
- 🟢 CONFIRMADO: Installation check bloqueia quando faltam scripts de pacote; ausência de runner é warning.
- 🟡 INFERIDO: O ZIP `diagnostics-share-*.zip` é o artefato preferencial para envio via WhatsApp ou suporte remoto, conforme instruções locais do projeto.
- 🔴 LACUNA: O diagnóstico coleta saída bruta de comandos de rede no JSON; não há sanitização explícita de nomes de rede, hostname, MACs ou SSID antes de empacotar.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|-----------|-------------------|
| RF-01 | 🟢 O agente deve expor `doctor --nvr-ip <IP> --share` e `diagnostics --nvr-ip <IP> --share`. | Must | `_parse_args()` registra os dois subcomandos e `main()` roteia ambos para `run_doctor()`. |
| RF-02 | 🟢 O doctor deve coletar IP local, máscara, gateway, DNS e CIDR local. | Must | `_parse_ipconfig()` e `_compute_cidr()` populam `network_info`. |
| RF-03 | 🟢 O doctor deve testar DNS, internet, cloud API, permissão de escrita e suporte a snapshot. | Must | Payload inclui `dns_check`, `internet_check`, `api_check`, `permissions_check` e `snapshot_support`. |
| RF-04 | 🟢 O doctor deve testar autenticação edge quando cloud/store/token existirem. | Must | `_edge_auth_check()` tenta endpoints de cameras com headers gerados por `build_auth_headers()`. |
| RF-05 | 🟢 O doctor deve detectar NVR fora da subnet local. | Must | Com `nvr_ip` e `local_cidr`, `network_segmented` indica IP fora da rede. |
| RF-06 | 🟢 O doctor deve salvar JSON e TXT de diagnóstico. | Must | Arquivos `diagnostics-<id>.json` e `diagnostics-<id>.txt` são escritos em `_log_dir()`. |
| RF-07 | 🟢 O doctor deve gerar ZIP compartilhável quando `--share` for usado. | Should | `_build_share_zip()` cria `diagnostics-share-<id>.zip` com JSON, TXT e logs `.log`. |
| RF-08 | 🟢 O comando `test-rtsp` deve validar canal RTSP específico ou escanear canais 1..16. | Should | `main()` chama `test_rtsp()` ou `test_rtsp_channels()` conforme `--scan-channels`. |
| RF-09 | 🟢 O teste RTSP deve mascarar senha em logs. | Must | `test_rtsp()` registra `mask_rtsp_url(rtsp_url)`. |
| RF-10 | 🟢 O readiness de onboarding deve validar `.env`, settings, ffmpeg e scan opcional. | Should | `build_onboarding_readiness()` retorna `status`, `summary`, `env_file`, `settings`, `plan`, `discovery` e `checks`. |
| RF-11 | 🟢 O installation check deve validar scripts e runner no diretório corrente ou `release/`. | Should | `build_installation_check_payload()` retorna status `ready`, `needs_attention` ou `blocked`. |
| RF-12 | 🟢 A Setup API deve expor rotas locais de diagnóstico de onboarding. | Should | `/onboarding/readiness`, `/onboarding/installation-check` e `/onboarding/test-camera` retornam payloads JSON. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------|
| Operabilidade | Saídas devem ser legíveis para suporte e usuário leigo. | `_summarize()` gera bloco textual e ações `NET001`, `NET002`, `RTSP554`. | 🟢 |
| Segurança | Senha RTSP não deve aparecer em logs de teste RTSP. | `mask_rtsp_url()` usado antes de logar URL. | 🟢 |
| Segurança | Erros da Setup API devem redigir credenciais RTSP quando aparecem em exceções de snapshot. | `_redact_sensitive_text()` em `setup_api.py`. | 🟢 |
| Resiliência | Falha em um check não deve impedir geração do payload completo quando recuperável. | Checks capturam exceções e retornam `{ok:false,error}`. | 🟢 |
| Compatibilidade Windows | Diagnóstico de rede usa comandos nativos do Windows. | `_run_cmd()` executa `cmd /c` com `ipconfig`, `route`, `arp`, `netsh`. | 🟢 |
| Suporte remoto | O pacote compartilhável deve agregar diagnóstico e logs. | `_build_share_zip()` inclui JSON/TXT e todos os `.log` do diretório. | 🟢 |
| Privacidade | Dados sensíveis de ambiente não devem ser impressos em readiness. | Readiness report lista presença/ausência de env, não valores. | 🟢 |
| Privacidade | Saídas brutas de comandos de rede podem conter dados locais do cliente. | Payload inclui `commands.ipconfig`, `route_print`, `arp`, `wlan`. | 🔴 |

## Critérios de Aceitação

```gherkin
Dado um computador de cliente com agente instalado
Quando suporte executar python -m dalevision_edge_agent.main doctor --nvr-ip 192.168.15.10 --share
Então o agente deve imprimir um resumo textual copiável
E deve salvar diagnostics-<id>.json, diagnostics-<id>.txt e diagnostics-share-<id>.zip no diretório de logs
```

```gherkin
Dado um NVR informado fora do CIDR local
Quando o doctor calcular a rede local
Então o payload deve marcar network_segmented=true
E o resumo deve incluir NET002 com orientação de mesma VLAN
```

```gherkin
Dado CLOUD_BASE_URL ausente
Quando o doctor executar
Então api_check.ok deve ser false
E o restante do diagnóstico deve continuar sendo gerado
```

```gherkin
Dado STORE_ID ou EDGE_TOKEN ausente
Quando o doctor executar autenticação edge
Então edge_auth_check.ok deve ser false
E edge_auth_error deve indicar missing_store_or_token
```

```gherkin
Dado credencial RTSP inválida
Quando suporte executar test-rtsp
Então a resposta deve retornar ok=false
E a mensagem deve conter RTSP401 credencial invalida
E a senha não deve aparecer no log
```

```gherkin
Dado um pacote release com scripts de suporte e runner
Quando installation-check executar
Então o status deve ser ready
E checks_fail deve ser zero
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Doctor com resumo e arquivos JSON/TXT | Must | Principal ferramenta para suporte remoto sem acesso ao cliente. |
| Detecção de VLAN/subnet e porta RTSP | Must | Diagnostica a causa mais provável de NVR inacessível em campo. |
| Mascaramento de credenciais RTSP | Must | Evita vazamento de senha de NVR em logs. |
| Edge auth check | Must | Diferencia falha local de token/store/cloud inválidos. |
| ZIP compartilhável | Should | Otimiza suporte via WhatsApp, mas JSON/TXT já preservam diagnóstico. |
| Readiness e installation check | Should | Importantes para onboarding, mas não substituem doctor em incidente. |
| Setup API local de diagnóstico | Should | Permite frontend consumir checks durante onboarding. |
| Sanitização de comandos brutos | Should | Necessária para reduzir exposição de dados locais antes de compartilhar ZIP. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------|
| `src/dalevision_edge_agent/main.py` | `_parse_args`, roteamento `doctor`, `diagnostics`, `test-rtsp`, `onboarding-readiness` | 🟢 |
| `src/dalevision_edge_agent/diagnostics.py` | `run_doctor`, `_summarize`, `_edge_auth_check`, `_build_share_zip` | 🟢 |
| `src/dalevision_edge_agent/rtsp_test.py` | `test_rtsp`, `test_rtsp_channels`, `_build_intelbras_rtsp`, `_is_segmented` | 🟢 |
| `src/dalevision_edge_agent/onboarding_readiness.py` | `build_onboarding_readiness`, `render_onboarding_readiness_markdown`, `export_onboarding_readiness_report` | 🟢 |
| `src/dalevision_edge_agent/installation_check.py` | `build_installation_check_payload` | 🟢 |
| `src/dalevision_edge_agent/onboarding_error_codes.py` | `map_camera_health_error_to_code`, `map_heartbeat_failure_to_code` | 🟢 |
| `src/dalevision_edge_agent/setup_api.py` | `/onboarding/readiness`, `/onboarding/installation-check`, `/onboarding/test-camera`, `_redact_sensitive_text` | 🟢 |
| `tests/test_doctor_pytest.py` | Parse, doctor summary, share ZIP, RTSP helpers | 🟢 |
| `tests/test_rtsp_test_fallback.py` | Digest challenge fallback | 🟢 |
| `tests/test_installation_check.py` | Status ready/blocked/needs_attention | 🟢 |
| `tests/test_onboarding_readiness.py` | Readiness, scan summary, export JSON/MD | 🟢 |

## Lacunas de Validação

- 🔴 Definir política de sanitização para `commands.ipconfig`, `route_print`, `arp` e `wlan` antes de compartilhar diagnóstico com suporte externo.
- 🔴 Validar `doctor --share` em Windows real com `%LOCALAPPDATA%`, ffmpeg ausente/presente e permissões restritas.
- 🔴 Definir retenção/limpeza dos arquivos `diagnostics-*.json`, `diagnostics-*.txt` e `diagnostics-share-*.zip`.
- 🟡 Validar se `requests.get(CLOUD_BASE_URL)` é suficiente como health check de cloud em ambientes com redirect, WAF ou homepage 404.
- 🟡 Confirmar se endpoints tentados por `_edge_auth_check()` ainda representam todos os contratos suportados pelo backend.
