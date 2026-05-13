# Inicialização CLI, Requirements

## Visão Geral

🟢 CONFIRMADO: Este caso de uso cobre a inicialização do agente por linha de comando ou executável, incluindo parsing de argumentos, configuração de logger, escolha entre loop contínuo e subcomandos, e validação inicial de ambiente.

## Responsabilidades

- 🟢 Interpretar argumentos CLI sem efeitos colaterais destrutivos.
- 🟢 Configurar logs antes de executar fluxos longos.
- 🟢 Roteiar subcomandos especializados sem entrar no loop contínuo indevidamente.
- 🟢 Preparar runtime paths e settings quando o modo exige operação cloud.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-CLI-01 | 🟢 CLI deve aceitar execução padrão sem subcomando. | Must | Processo entra no fluxo contínuo após carregar settings. |
| RF-CLI-02 | 🟢 CLI deve aceitar `--once`. | Must | Processo envia um heartbeat e encerra. |
| RF-CLI-03 | 🟢 CLI deve aceitar `doctor --nvr-ip --share`. | Should | Processo chama doctor sem iniciar loop contínuo. |
| RF-CLI-04 | 🟢 CLI deve aceitar `setup-api --host --port`. | Should | Processo inicia HTTP local no host/porta informados. |
| RF-CLI-05 | 🟢 CLI deve configurar logger uma única vez. | Must | Chamadas repetidas não duplicam handlers. |
| RF-CLI-06 | 🟢 CLI deve retornar erro claro para configuração inválida. | Must | Ausência de env obrigatório impede loop operacional válido. |

## Critérios de Aceitação

```gherkin
Dado um ambiente com variáveis obrigatórias válidas
Quando executar o agente sem subcomando
Então o runtime deve configurar logs, carregar settings e iniciar o loop operacional
```

```gherkin
Dado um operador de suporte
Quando executar doctor --nvr-ip 192.168.0.10 --share
Então o runtime deve executar diagnóstico e não iniciar loop contínuo
```

## Rastreabilidade

| Arquivo | Símbolo | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/main.py` | `_parse_args`, `_setup_logging` | 🟢 |
| `src/dalevision_edge_agent/env.py` | `load_settings` | 🟢 |
| `src/dalevision_edge_agent/paths.py` | `resolve_runtime_paths` | 🟢 |
