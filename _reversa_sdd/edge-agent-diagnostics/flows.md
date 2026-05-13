# Edge Agent Diagnostics, Fluxos

## Fluxo 1: Doctor Compartilhável

```mermaid
sequenceDiagram
    participant Suporte
    participant CLI as Edge Agent CLI
    participant Doctor as diagnostics.run_doctor
    participant Windows as Comandos Windows
    participant Cloud as Backend Cloud
    participant FS as Log Dir

    Suporte->>CLI: doctor --nvr-ip <IP> --share
    CLI->>Doctor: run_doctor(cloud, nvr_ip, share, store_id, edge_token)
    Doctor->>Windows: ipconfig /all, route print, arp -a, netsh wlan
    Windows-->>Doctor: saídas brutas
    Doctor->>Doctor: parse IP, mask, gateway, DNS, CIDR
    Doctor->>Cloud: GET cloud_base_url
    Cloud-->>Doctor: status ou erro
    Doctor->>Cloud: GET endpoints de cameras com EdgeToken
    Cloud-->>Doctor: lista/status/erro
    Doctor->>Doctor: DNS, internet, snapshot, disk, write, portas NVR
    Doctor->>FS: diagnostics-<id>.json
    Doctor->>FS: diagnostics-<id>.txt
    Doctor->>FS: diagnostics-share-<id>.zip
    Doctor-->>CLI: payload
    CLI-->>Suporte: resumo textual copiável
```

## Fluxo 2: Detecção de VLAN/Subnet

```mermaid
flowchart TD
    A[Doctor recebe nvr_ip] --> B[Parse local IPv4 e mask]
    B --> C{IPv4 e mask existem?}
    C -- no --> D[network_segmented=false]
    C -- yes --> E[Calcula local_cidr]
    E --> F{nvr_ip pertence ao CIDR?}
    F -- yes --> G[network_segmented=false]
    F -- no --> H[network_segmented=true]
    H --> I[Adicionar NET002 em summary e suggested_actions]
    G --> J[Continuar checks de porta]
    D --> J
    I --> J
```

## Fluxo 3: Teste RTSP com Fallback Digest

```mermaid
flowchart TD
    A[CLI test-rtsp] --> B[Montar URL Intelbras/Dahua]
    B --> C[Mascarar URL para log]
    C --> D[check_camera_health com DESCRIBE]
    D --> E{status online/degraded?}
    E -- yes --> F[Capturar snapshot se possível]
    E -- no --> G{erro contem unauthorized?}
    G -- yes --> H[check_camera_health sem DESCRIBE]
    H --> I{fallback online/degraded?}
    I -- yes --> F
    I -- no --> J[Retornar RTSP401]
    G -- no --> K{erro timeout?}
    K -- yes --> L{IP fora da subnet?}
    L -- yes --> M[Retornar NET002]
    L -- no --> N[Retornar RTSPTO]
    K -- no --> O[Retornar RTSPERR]
    F --> P[Estimar FPS via OpenCV se disponível]
    P --> Q[Retornar ok=true]
```

## Fluxo 4: Readiness de Onboarding

```mermaid
flowchart TD
    A[CLI/Setup API onboarding-readiness] --> B[Carregar .env do cwd]
    B --> C[Descrever arquivo .env]
    C --> D[Validar CLOUD_BASE_URL STORE_ID EDGE_TOKEN]
    D --> E[load_settings]
    E --> F[Verificar ffmpeg no PATH]
    F --> G{scan habilitado?}
    G -- yes --> H[Executar discovery_provider]
    H --> I[Gerar blueprint e recomendadas]
    G -- no --> J[Usar blueprint vazio pelo plano]
    I --> K[Somar checks]
    J --> K
    K --> L{algum fail?}
    L -- yes --> M[status blocked]
    L -- no --> N{algum warning?}
    N -- yes --> O[status needs_attention]
    N -- no --> P[status ready]
```

## Fluxo 5: Installation Check

```mermaid
flowchart TD
    A[CLI/Setup API installation-check] --> B[Resolver cwd]
    B --> C[Procurar scripts no root e release]
    B --> D[Procurar runner no root e release]
    C --> E{>=2 scripts encontrados?}
    D --> F{runner encontrado?}
    E -- no --> G[package_scripts fail]
    E -- yes --> H[package_scripts ok]
    F -- no --> I[package_runner warning]
    F -- yes --> J[package_runner ok]
    G --> K[status blocked]
    H --> L{runner warning?}
    I --> L
    J --> M{algum fail?}
    L -- yes --> N[status needs_attention]
    M -- no --> O[status ready]
```

## Fluxo 6: Setup API Local para Diagnóstico

```mermaid
sequenceDiagram
    participant Frontend as Onboarding UI
    participant API as Setup API local
    participant Readiness as build_onboarding_readiness
    participant Install as build_installation_check_payload
    participant RTSP as test_rtsp

    Frontend->>API: GET /health
    API-->>Frontend: status online + capabilities
    Frontend->>API: GET /onboarding/readiness?plan=trial&scan=1
    API->>Readiness: build_onboarding_readiness(...)
    Readiness-->>API: payload readiness
    API-->>Frontend: JSON readiness
    Frontend->>API: GET /onboarding/installation-check
    API->>Install: build_installation_check_payload()
    Install-->>API: payload installation
    API-->>Frontend: JSON installation
    Frontend->>API: GET /onboarding/test-camera?ip=...&user=...&password=...
    API->>RTSP: test_rtsp(...)
    RTSP-->>API: ok/erro
    API-->>Frontend: JSON RTSP
```

## Códigos Operacionais

| Código | Condição | Ação esperada | Confiança |
|---|---|---|---|
| `NET001` | Gateway padrão ausente | Verificar cabo/rede do PC. | 🟢 |
| `NET002` | NVR fora do subnet local ou timeout com rede segmentada | Conectar PC e NVR na mesma VLAN/rede. | 🟢 |
| `RTSP554` | Porta 554 fechada no NVR informado | Habilitar RTSP ou liberar porta. | 🟢 |
| `RTSP401` | Credencial RTSP inválida | Revisar usuário/senha do NVR. | 🟢 |
| `RTSPTO` | Timeout RTSP sem segmentação comprovada | Verificar firewall, porta ou NVR inacessível. | 🟢 |
| `RTSPERR` | Erro RTSP genérico | Encaminhar detalhe técnico ao suporte. | 🟢 |
| `NVR_AUTH_FAIL` | Camera health auth failed/401/403 | Revisar credencial do NVR/camera. | 🟢 |
| `RTSP_TIMEOUT` | Camera health timeout | Verificar rede/porta/VLAN. | 🟢 |
| `HEARTBEAT_REJECTED` | Heartbeat HTTP 401/403 | Revisar token edge/store. | 🟢 |

## Arquivos Gerados

| Arquivo | Gatilho | Conteúdo | Confiança |
|---|---|---|---|
| `diagnostics-<id>.json` | Sempre no doctor | Payload completo com checks e comandos brutos. | 🟢 |
| `diagnostics-<id>.txt` | Sempre no doctor | Resumo textual copiável. | 🟢 |
| `diagnostics-share-<id>.zip` | `--share` | JSON, TXT e logs `.log`. | 🟢 |
| Readiness JSON exportado | `onboarding-readiness --export-json` | Payload de readiness. | 🟢 |
| Readiness Markdown exportado | `onboarding-readiness --export-md` | Relatório legível. | 🟢 |

## Pontos de Controle

- 🟢 CONFIRMADO: Todo fluxo de diagnóstico deve retornar payload mesmo com checks parciais falhando.
- 🟢 CONFIRMADO: Falhas de request devem ser registradas e convertidas em erro estruturado.
- 🟢 CONFIRMADO: A senha RTSP deve ser mascarada no log antes de qualquer tentativa.
- 🟢 CONFIRMADO: O ZIP compartilhável deve ser gerado somente quando solicitado por `--share`.
- 🔴 LACUNA: Falta checkpoint explícito para sanitizar dados brutos antes de anexar ao ZIP.
