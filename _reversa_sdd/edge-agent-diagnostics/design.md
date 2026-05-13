# Edge Agent Diagnostics, Design Técnico

## Interface

🟢 CONFIRMADO: A interface primária desta unit é CLI local do agente, complementada por funções Python reutilizáveis e rotas HTTP da Setup API para onboarding.

### CLI

| Comando / Opção | Entrada | Saída | Observação | Confiança |
|---|---|---|---|---|
| `python -m dalevision_edge_agent.main doctor` | `.env` e ambiente | Resumo textual + JSON/TXT | Alias operacional para diagnóstico local. | 🟢 |
| `python -m dalevision_edge_agent.main doctor --nvr-ip <IP>` | IP do NVR | Diagnóstico com subnet e portas do NVR | Detecta VLAN/subnet e porta 554 fechada. | 🟢 |
| `python -m dalevision_edge_agent.main doctor --share` | Flag booleana | ZIP `diagnostics-share-<id>.zip` | Inclui JSON, TXT e logs `.log`. | 🟢 |
| `python -m dalevision_edge_agent.main diagnostics --nvr-ip <IP> --share` | Mesma entrada do doctor | Mesma saída do doctor | Subcomando equivalente. | 🟢 |
| `python -m dalevision_edge_agent.main test-rtsp --ip --user --pass --channel --subtype --timeout` | Credenciais e canal RTSP | Console OK/FAIL e payload interno | Usa template Intelbras/Dahua. | 🟢 |
| `python -m dalevision_edge_agent.main test-rtsp --scan-channels` | Credenciais RTSP | Resultado por canal até 16 | Para no primeiro OK ou em erro de credencial. | 🟢 |
| `python -m dalevision_edge_agent.main onboarding-readiness --plan trial --scan --json` | Plano e scan opcional | Payload JSON ou resumo textual | Valida env/settings/ffmpeg/scan. | 🟢 |

### Setup API Local

| Rota | Entrada | Saída | Observação | Confiança |
|---|---|---|---|---|
| `GET /health` | Nenhuma | Status, versão, IPs e capabilities | Inclui capacidades de readiness e installation check. | 🟢 |
| `GET /onboarding/readiness?plan=<plan>&scan=1` | Plano e flag scan | Payload de readiness | Reutiliza `build_onboarding_readiness()`. | 🟢 |
| `GET /onboarding/installation-check` | Diretório corrente do processo | Payload de instalação | Reutiliza `build_installation_check_payload()`. | 🟢 |
| `GET /onboarding/test-camera?ip=&user=&password=&channel=` | Dados RTSP | Resultado de `test_rtsp()` | Retorna JSON para frontend local. | 🟢 |
| `GET /onboarding/snapshot?...` | Dados RTSP | JPEG ou erro JSON | Redige credenciais em exceções. | 🟢 |

### Funções Principais

| Símbolo | Entrada | Retorno | Observação | Confiança |
|---|---|---|---|---|
| `diagnostics.run_doctor` | `cloud_base_url`, `logger`, `nvr_ip`, `share`, `store_id`, `edge_token` | `dict[str, Any]` | Orquestra coleta, resumo, arquivos e ZIP. | 🟢 |
| `diagnostics._parse_ipconfig` | Texto do `ipconfig` | dict com `ipv4`, `mask`, `gateway`, `dns_servers` | Suporta inglês e português. | 🟢 |
| `diagnostics._edge_auth_check` | cloud/store/token | dict com `ok`, `status`, `count`, `tried` | Tenta múltiplos endpoints de cameras. | 🟢 |
| `diagnostics._build_share_zip` | paths JSON/TXT | `None` | Compacta artefatos e logs. | 🟢 |
| `rtsp_test.test_rtsp` | IP, user, password, channel, subtype, timeout | dict com `ok`, `health`, `snapshot`, `fps` | Faz DESCRIBE, fallback e snapshot. | 🟢 |
| `rtsp_test.test_rtsp_channels` | canais 1..16 | dict com `results` | Escaneia canais sequencialmente. | 🟢 |
| `onboarding_readiness.build_onboarding_readiness` | plano, scan opcional | payload de readiness | Valida env/settings/ffmpeg/scan. | 🟢 |
| `installation_check.build_installation_check_payload` | cwd opcional | payload de instalação | Procura scripts e runner no root/release. | 🟢 |

## Modelo de Dados

### Payload `run_doctor`

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `ts` | string ISO UTC | Timestamp do diagnóstico. | 🟢 |
| `id` | string | Identificador `YYYYMMDD-HHMMSS`. | 🟢 |
| `cloud_base_url` | string | URL base da cloud usada no check. | 🟢 |
| `network_info.local_ipv4` | string/null | IPv4 local parseado. | 🟢 |
| `network_info.local_mask` | string/null | Máscara local parseada. | 🟢 |
| `network_info.local_cidr` | string/null | CIDR calculado. | 🟢 |
| `network_info.gateway` | string/null | Gateway padrão. | 🟢 |
| `network_info.dns_servers` | string/null | DNS encontrados. | 🟢 |
| `gateway_ping_ms` | float/null | Latência do ping ao gateway. | 🟢 |
| `nvr_ip` | string/null | IP informado via CLI. | 🟢 |
| `network_segmented` | bool | Se NVR está fora do CIDR local. | 🟢 |
| `api_check` | object | Resultado de GET em `cloud_base_url`. | 🟢 |
| `dns_check` | object | Resolução de `google.com`. | 🟢 |
| `internet_check` | object | Socket TCP em `1.1.1.1:443`. | 🟢 |
| `snapshot_support` | object | Suporte por OpenCV/ffmpeg. | 🟢 |
| `edge_auth_check` | object | Resultado de autenticação edge. | 🟢 |
| `disk_check` | object | Espaço total/livre do log dir. | 🟢 |
| `permissions_check` | object | Escrita em log dir. | 🟢 |
| `ports.nvr` | list[int] | Portas abertas no NVR informado. | 🟢 |
| `suggested_actions` | list[string] | Códigos e orientações curtas. | 🟢 |
| `commands` | object | Saídas brutas de rede. | 🟢 |
| `summary` | string | Bloco textual copiável. | 🟢 |

### Payload `build_onboarding_readiness`

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `ok` | bool | Indica geração bem-sucedida do relatório. | 🟢 |
| `method.id` | string | `edge_onboarding_readiness`. | 🟢 |
| `status` | string | `ready`, `needs_attention` ou `blocked`. | 🟢 |
| `summary.checks_ok` | int | Quantidade de checks OK. | 🟢 |
| `summary.checks_warning` | int | Quantidade de warnings. | 🟢 |
| `summary.checks_fail` | int | Quantidade de falhas. | 🟢 |
| `summary.missing_required_env` | list[string] | Env obrigatória ausente. | 🟢 |
| `env_file` | object | Metadados do `.env`, não valores sensíveis. | 🟢 |
| `settings` | object | Settings carregados sem token. | 🟢 |
| `plan.camera_limit` | int | Limite derivado do plano. | 🟢 |
| `discovery` | object | Resumo de scan opcional. | 🟢 |
| `checks` | list[object] | Lista detalhada de checks. | 🟢 |

### Payload `build_installation_check_payload`

| Campo | Tipo | Descrição | Confiança |
|---|---|---|---|
| `status` | string | `ready`, `needs_attention` ou `blocked`. | 🟢 |
| `working_dir` | string | Diretório analisado. | 🟢 |
| `checks[].key` | string | `package_scripts` ou `package_runner`. | 🟢 |
| `checks[].reason_code` | string | `scripts_found`, `scripts_missing`, `runner_found`, `runner_missing`. | 🟢 |
| `checks[].details.files` | list[string] | Arquivos encontrados. | 🟢 |

## Fluxo Principal: Doctor

1. 🟢 CONFIRMADO: `main()` detecta `args.command in {"diagnostics", "doctor"}`.
2. 🟢 CONFIRMADO: O runtime lê `CLOUD_BASE_URL`/`DALE_CLOUD_BASE_URL`, `STORE_ID`/`DALE_STORE_ID` e `EDGE_TOKEN`/`DALE_EDGE_TOKEN`.
3. 🟢 CONFIRMADO: `run_doctor()` executa comandos Windows de rede com timeout.
4. 🟢 CONFIRMADO: `_parse_ipconfig()` extrai IPv4, máscara, gateway e DNS.
5. 🟢 CONFIRMADO: `_compute_cidr()` calcula a rede local.
6. 🟢 CONFIRMADO: `_ping_gateway()`, `_dns_check()`, `_internet_check()` e `_api_check()` testam conectividade básica.
7. 🟢 CONFIRMADO: `detect_snapshot_support()` verifica OpenCV/ffmpeg.
8. 🟢 CONFIRMADO: `_edge_auth_check()` tenta endpoints de camera com token edge.
9. 🟢 CONFIRMADO: `_disk_check()` e `_permissions_check()` validam o diretório de logs.
10. 🟢 CONFIRMADO: Se `nvr_ip` for informado, o doctor calcula segmentação e testa portas.
11. 🟢 CONFIRMADO: `_summarize()` monta bloco textual copiável.
12. 🟢 CONFIRMADO: JSON e TXT são gravados no log dir.
13. 🟢 CONFIRMADO: Se `share=true`, `_build_share_zip()` cria pacote ZIP com diagnóstico e logs.

## Fluxos Alternativos

- **Cloud ausente:** 🟢 CONFIRMADO: `_api_check()` retorna `missing_cloud_base_url`; o payload continua.
- **Store/token ausente:** 🟢 CONFIRMADO: `_edge_auth_check()` retorna `missing_store_or_token`; o payload continua.
- **Gateway ausente:** 🟢 CONFIRMADO: `suggested_actions` recebe `NET001 Verifique o cabo/rede. Sem gateway padrao.`
- **NVR fora da rede:** 🟢 CONFIRMADO: `suggested_actions` recebe `NET002 Conecte o PC na mesma rede/VLAN do NVR`.
- **Porta 554 fechada:** 🟢 CONFIRMADO: `suggested_actions` recebe `RTSP554 Porta 554 fechada no NVR.`
- **Permissão de escrita falha:** 🟢 CONFIRMADO: `permissions_check.ok=false` e erro é registrado no payload.
- **Erro de comando Windows:** 🟢 CONFIRMADO: `_run_cmd()` retorna string `[command_error] ...` em vez de lançar exceção.

## Fluxo RTSP Test

1. 🟢 CONFIRMADO: CLI `test-rtsp` recebe IP, usuário, senha, canal, subtype e timeout.
2. 🟢 CONFIRMADO: `_build_intelbras_rtsp()` monta URL `rtsp://user:pass@host:554/cam/realmonitor?channel=N&subtype=N`.
3. 🟢 CONFIRMADO: `mask_rtsp_url()` mascara senha antes do log.
4. 🟢 CONFIRMADO: `check_camera_health()` executa DESCRIBE RTSP.
5. 🟢 CONFIRMADO: Se DESCRIBE retorna unauthorized, tenta fallback de conectividade sem DESCRIBE para evitar falso negativo por Digest.
6. 🟢 CONFIRMADO: Em sucesso, tenta snapshot com `capture_snapshot_if_possible()`.
7. 🟢 CONFIRMADO: Em sucesso, tenta estimar FPS com OpenCV, se disponível.
8. 🟢 CONFIRMADO: Em falha, retorna mensagem curta `RTSP401`, `NET002`, `RTSPTO` ou `RTSPERR`.

## Dependências

- 🟢 CONFIRMADO: Windows `cmd`, `ipconfig`, `route`, `arp`, `netsh` para diagnóstico de rede.
- 🟢 CONFIRMADO: `requests` para checks de cloud e autenticação edge.
- 🟢 CONFIRMADO: `socket` para DNS, internet e portas do NVR.
- 🟢 CONFIRMADO: `ffmpeg` e/ou OpenCV para suporte a snapshot.
- 🟢 CONFIRMADO: `dalevision_edge_agent.cameras` para headers edge, snapshot support, health e máscara de RTSP.
- 🟢 CONFIRMADO: Backend cloud do DaleVision para endpoints de cameras usados em `_edge_auth_check()`.
- 🟡 INFERIDO: Ambiente de suporte remoto depende de o cliente conseguir enviar arquivos ZIP/TXT por canal externo.

## Decisões de Design Identificadas

| Decisão | Evidência no código | Confiança |
|---|---|---|
| Doctor é local-first e não depende de backend saudável para gerar evidência. | Checks retornam erros estruturados e o payload é gravado mesmo com cloud ausente. | 🟢 |
| Diagnóstico preserva contexto bruto de rede para suporte avançado. | Payload inclui `commands` com saídas de comandos Windows. | 🟢 |
| Mensagens curtas usam códigos operacionais para leigo/suporte. | `NET001`, `NET002`, `RTSP554`, `RTSP401`, `RTSPTO`. | 🟢 |
| `doctor` e `diagnostics` são dois nomes para o mesmo fluxo. | `main()` roteia ambos para `run_doctor()`. | 🟢 |
| Teste RTSP implementa fallback para desafio Digest inicial. | `test_rtsp()` repete `check_camera_health(... perform_describe=False)` em unauthorized. | 🟢 |
| Readiness não expõe valores sensíveis de env. | Checks indicam presença/ausência, settings não incluem token. | 🟢 |
| Setup API usa CORS aberto para facilitar onboarding local. | `_set_cors_headers()` retorna `Access-Control-Allow-Origin: *`. | 🟢 |

## Observabilidade

- 🟢 CONFIRMADO: Doctor imprime o resumo no console.
- 🟢 CONFIRMADO: Doctor registra `Diagnostics saved: <json> <txt>` no logger.
- 🟢 CONFIRMADO: Doctor registra `Diagnostics share ZIP: <zip>` quando `--share` é usado.
- 🟢 CONFIRMADO: `_api_check()` e `_edge_auth_check()` registram erros de request no logger.
- 🟢 CONFIRMADO: `test_rtsp()` registra tentativa e falha/ok com URL mascarada.
- 🟢 CONFIRMADO: Readiness pode exportar JSON e Markdown.
- 🟢 CONFIRMADO: Setup API suprime logs HTTP padrão por `log_message()`.

## Segurança e Privacidade

- 🟢 CONFIRMADO: Senha RTSP é mascarada em logs do teste RTSP.
- 🟢 CONFIRMADO: Setup API redige credenciais RTSP em texto de exceção de snapshot.
- 🟢 CONFIRMADO: Readiness não imprime valores de `EDGE_TOKEN`.
- 🟡 INFERIDO: `diagnostics-share-*.zip` deve ser tratado como artefato sensível porque contém topologia local.
- 🔴 LACUNA: Não há sanitização explícita dos comandos brutos antes de gravar/zipar diagnóstico.
- 🔴 LACUNA: `/onboarding/test-camera` aceita `password` em query string local, que pode aparecer em histórico do navegador/proxy local dependendo do ambiente.

## Diagrama de Fluxo

```mermaid
flowchart TD
    A[CLI doctor/diagnostics] --> B[Read env aliases]
    B --> C[run_doctor]
    C --> D[Collect Windows network commands]
    D --> E[Parse IP config and CIDR]
    E --> F[Connectivity checks]
    F --> G[Snapshot support check]
    G --> H[Edge auth check]
    H --> I[Disk and permission checks]
    I --> J{nvr_ip informed?}
    J -- yes --> K[Check subnet and NVR ports]
    J -- no --> L[Skip NVR-specific checks]
    K --> M[Build suggested actions]
    L --> M
    M --> N[Build text summary]
    N --> O[Write diagnostics JSON/TXT]
    O --> P{share?}
    P -- yes --> Q[Build diagnostics ZIP]
    P -- no --> R[Return payload]
    Q --> R
```

## Contratos Preservados

- 🟢 CONFIRMADO: Diagnóstico deve ser subcomando isolado e não deve entrar no loop contínuo do agente.
- 🟢 CONFIRMADO: Diagnóstico deve continuar gerando evidência mesmo quando cloud, DNS, internet ou token falham.
- 🟢 CONFIRMADO: Senhas RTSP não devem ser registradas em claro em logs.
- 🟢 CONFIRMADO: Os códigos operacionais curtos devem ser preservados porque orientam suporte remoto.
- 🟢 CONFIRMADO: `doctor --share` deve incluir os logs `.log` existentes para investigação remota.

## Riscos e Lacunas

- 🔴 LACUNA: Falta redaction/sanitização centralizada para dados de rede local no ZIP compartilhável.
- 🔴 LACUNA: Falta teste de integração que valide a estrutura completa do ZIP em Windows real.
- 🟡 RISCO: Health check de cloud por GET no base URL pode gerar falso negativo/positivo se a cloud responder 404, redirect ou página protegida.
- 🟡 RISCO: `_edge_auth_check()` tenta endpoints legados e atuais; mudanças no backend podem deixar o diagnóstico defasado sem quebrar testes locais.
- 🟡 RISCO: `/onboarding/test-camera` recebe senha em query string; aceitável no loopback, mas frágil se host for exposto fora de `127.0.0.1`.
