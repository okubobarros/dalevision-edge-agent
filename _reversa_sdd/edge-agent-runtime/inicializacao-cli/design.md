# Inicialização CLI, Design Técnico

## Interface

| Símbolo | Entrada | Retorno | Confiança |
|---|---|---|---|
| `_parse_args()` | `sys.argv` | `argparse.Namespace` | 🟢 |
| `_setup_logging()` | n/a | `logging.Logger` | 🟢 |
| `_get_version()` | package metadata | `str` | 🟢 |
| `resolve_runtime_paths(version)` | versão | `RuntimePaths` | 🟢 |

## Fluxo Principal

```mermaid
flowchart TD
    A[Processo inicia] --> B[Parse args]
    B --> C[Setup logging]
    C --> D{Subcomando?}
    D -- doctor/setup/scan/rtsp --> E[Executar fluxo dedicado]
    D -- nenhum/once/smoke --> F[Resolver paths]
    F --> G[Carregar env/settings]
    G --> H[Continuar para bootstrap/loop]
```

## Fluxos Alternativos

- 🟢 `doctor`: executa diagnóstico e encerra.
- 🟢 `setup-api`: inicia servidor local.
- 🟢 `--once`: executa uma tentativa de heartbeat.
- 🟢 Config inválida: retorna erro diagnosticável.

## Decisões

| Decisão | Evidência | Confiança |
|---|---|---|
| Um único entrypoint centraliza subcomandos e loop. | `main.py` `_parse_args` | 🟢 |
| Logger evita handlers duplicados. | `main.py` `_setup_logging` | 🟢 |
| Versão pode vir de metadata ou fallback. | `main.py` `_get_version` | 🟢 |

## Riscos

- 🟡 `main.py` acumula muitas responsabilidades; subcomandos devem ser testados para evitar regressões cruzadas.
- 🔴 Validar exit codes finais esperados pelo autostart/instalador.
