# Edge Agent Runtime, Fluxos Operacionais

## Visão Geral

🟢 CONFIRMADO: Esta unit possui múltiplos fluxos distintos porque `main.py` atua como orquestrador do runtime local, dos subcomandos de suporte/onboarding e do loop operacional contínuo.

## Fluxo 1, Inicialização Contínua do Agente

### Entrada

| Campo | Origem | Obrigatório | Confiança |
|---|---|---|---|
| `CLOUD_BASE_URL` | `.env`, ambiente ou `DALE_CLOUD_BASE_URL` | Sim | 🟢 |
| `STORE_ID` | `.env`, ambiente ou `DALE_STORE_ID` | Sim | 🟢 |
| `EDGE_TOKEN` | `.env`, ambiente ou `DALE_EDGE_TOKEN` | Sim | 🟢 |
| `AGENT_ID` | `.env`, ambiente ou `DALE_AGENT_ID` | Sim no contrato operacional | 🟢 |
| `DALE_*_DIR` | Ambiente | Não | 🟢 |

### Sequência

```mermaid
sequenceDiagram
    participant OS as Windows/Processo
    participant Main as main.py
    participant Paths as paths.py
    participant Env as env.py
    participant Activation as activation.py
    participant Logger as agent.log

    OS->>Main: iniciar entrypoint
    Main->>Main: parse CLI args
    Main->>Logger: configurar logging rotacionado
    Main->>Paths: resolve_runtime_paths(version)
    Paths-->>Main: app/config/log/cache/tmp dirs
    Main->>Env: load_env_from_cwd + load_settings
    Env-->>Main: settings normalizados ou erro
    Main->>Activation: bootstrap_activation
    Activation-->>Main: AgentState + config
    Main->>Logger: registrar estado inicial
```

### Saídas

- 🟢 Diretórios locais criados.
- 🟢 Logger pronto.
- 🟢 Settings validados.
- 🟢 Estado inicial definido.
- 🟢 Erro diagnosticável quando configuração/ativação é inválida.

## Fluxo 2, Loop Operacional de Heartbeat

### Sequência

```mermaid
flowchart TD
    A[Início do loop] --> B{Camera sync habilitado?}
    B -- sim --> C[Sincronizar cameras e health]
    B -- nao --> D[Registrar camera sync disabled periodicamente]
    C --> E[Montar campos agregados de camera]
    D --> E
    E --> F[Criar HeartbeatPayload]
    F --> G[Enviar heartbeat via HeartbeatClient]
    G --> H[Atualizar watchdog]
    H --> I[Calcular próximo AgentState]
    I --> J{Heartbeat OK pela primeira vez?}
    J -- sim --> K[Emitir agent_first_heartbeat]
    J -- nao --> L[Não emitir evento duplicado]
    K --> M[Verificar update se intervalo venceu]
    L --> M
    M --> N[Calcular sleep por estado/backoff]
    N --> A
```

### Regras de Transição

| Condição | Estado seguinte | Evidência | Confiança |
|---|---|---|---|
| `ok=True` | `active` | `tests/test_heartbeat_state.py` | 🟢 |
| `ok=False`, `status_code=None` | `degraded` | `tests/test_heartbeat_state.py` | 🟢 |
| `ok=False`, `status_code=401` | `error` | `tests/test_heartbeat_state.py` | 🟢 |
| `state=degraded` no sleep | intervalo degradado, padrão 300s | `tests/test_heartbeat_state.py` | 🟢 |

## Fluxo 3, Subcomando Doctor

### Sequência

```mermaid
flowchart TD
    A[CLI doctor] --> B[Parse --nvr-ip e --share]
    B --> C[Configurar logger]
    C --> D[Chamar run_doctor]
    D --> E[Validar rede/NVR/API/config/snapshot]
    E --> F[Gerar diagnostics.json e diagnostics.txt]
    F --> G{--share?}
    G -- sim --> H[Gerar pacote compartilhável]
    G -- nao --> I[Encerrar com resultado local]
    H --> I
```

### Contrato

| Item | Comportamento | Confiança |
|---|---|---|
| Diagnóstico legível | Mensagens devem orientar usuário leigo/suporte remoto. | 🟢 |
| Sem segredos | Não registrar senha, token ou RTSP com credencial. | 🟢 |
| Saída compartilhável | `--share` prepara material para envio. | 🟢 |

## Fluxo 4, Setup API Local

### Sequência

```mermaid
sequenceDiagram
    participant CLI as CLI setup-api
    participant Server as setup_api.py
    participant Browser as Frontend/Onboarding local
    participant Agent as Runtime local

    CLI->>Server: serve_setup_api(host, port)
    Browser->>Server: GET rota local
    Server->>Agent: build_setup_api_response
    Agent-->>Server: JSON ou arquivo local
    Server-->>Browser: resposta com CORS
```

### Rotas/Comportamentos

| Caso | Comportamento | Evidência | Confiança |
|---|---|---|---|
| `OPTIONS` | Retorna 204 com CORS. | `setup_api.py` `do_OPTIONS` | 🟢 |
| `GET` rota de API | Retorna JSON via `build_setup_api_response`. | `setup_api.py` `do_GET` | 🟢 |
| Arquivo HLS local | Serve arquivo de `tmp_streams` quando existe. | `setup_api.py` stream handling | 🟢 |
| Snapshot solicitado | Tenta snapshot e retorna arquivo ou falha controlada. | `setup_api.py` snapshot flow | 🟢 |

## Fluxo 5, Health Gate Pós-Update

### Sequência

```mermaid
flowchart TD
    A[Runtime inicia após update] --> B[Ler updates/pending.json]
    B --> C[Calcular deadline do health gate]
    C --> D[Enviar heartbeat para /api/edge/events/]
    D --> E{Heartbeat OK?}
    E -- sim --> F[Health gate aprovado]
    E -- nao --> G{Ainda dentro do deadline?}
    G -- sim --> D
    G -- nao --> H[Registrar UPD041 health gate failed]
    H --> I[Aplicar rollback se backup existir]
    I --> J[Registrar UPD050 ou UPD051]
```

### Regras

| Regra | Comportamento | Confiança |
|---|---|---|
| Heartbeat é gate mínimo | Update só é saudável se heartbeat pós-boot funcionar. | 🟢 |
| Camera health pode ficar pendente | O gate registra que camera health ainda não foi avaliado nesse estágio. | 🟢 |
| Rollback é best-effort | Falha de rollback é logada, não escondida. | 🟢 |

## Fluxo 6, Falha de Autenticação no Loop

```mermaid
flowchart TD
    A[Heartbeat ou camera event] --> B{Status 401/403?}
    B -- nao --> C[Tratar como falha comum ou sucesso]
    B -- sim --> D[Incrementar falhas consecutivas]
    D --> E[Logar auth rejected sem token]
    E --> F{Limite atingido?}
    F -- nao --> G[Continuar ou retry conforme fluxo]
    F -- sim --> H[Emitir activation_failed se aplicável]
    H --> I[Retornar EXIT_AUTH_ERROR]
```

## Fluxo 7, Paths e Temporários

```mermaid
flowchart TD
    A[resolve_runtime_paths] --> B{LOCALAPPDATA existe?}
    B -- sim --> C[Usar LOCALAPPDATA/DaleVision]
    B -- nao --> D{USERPROFILE existe?}
    D -- sim --> E[Usar USERPROFILE/AppData/Local/DaleVision]
    D -- nao --> F[Usar cwd]
    C --> G[Criar app/config/log/cache/tmp]
    E --> G
    F --> G
    G --> H[Retornar RuntimePaths]
```

## Pontos de Observabilidade por Fluxo

| Fluxo | Logs/Eventos | Confiança |
|---|---|---|
| Inicialização | logger configurado, config ausente, activation state. | 🟢 |
| Heartbeat | `Heartbeat -> <url> status=<status>`, warnings de falha. | 🟢 |
| Camera sync | status por camera, ROI error, snapshot upload status. | 🟢 |
| Doctor | diagnostics files e pacote share. | 🟢 |
| Setup API | respostas JSON/arquivos e erros redigidos. | 🟢 |
| Update | `UPD041`, `UPD050`, `UPD051`, update reports. | 🟢 |

## Lacunas de Fluxo

- 🔴 Confirmar política operacional para tempo máximo em `degraded` antes de intervenção.
- 🔴 Confirmar se `setup-api` pode escutar em interface diferente de `127.0.0.1`.
- 🔴 Confirmar matriz final de autostart Windows: shortcut, scheduled task ou serviço, por versão de Windows e nível de privilégio.
