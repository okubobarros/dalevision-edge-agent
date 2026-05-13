# Calcular Degradação Local, Requirements

## Visão Geral

🟢 CONFIRMADO: Caso de uso que transforma resultado de heartbeat em estado local do agente e intervalo de retry.

## Requisitos

| ID | Requisito | Prioridade | Critério |
|---|---|---|---|
| RF-DG-01 | 🟢 Sucesso deve resultar em `active`. | Must | Teste passa. |
| RF-DG-02 | 🟢 Erro de rede deve resultar em `degraded`. | Must | Teste passa. |
| RF-DG-03 | 🟢 401/403 deve resultar em `error`. | Must | Teste cobre 401. |
| RF-DG-04 | 🟢 `degraded` deve usar intervalo maior. | Must | Teste valida 300s. |

## Critérios

```gherkin
Dado estado active
Quando heartbeat retorna erro de rede
Então estado deve mudar para degraded
E sleep deve ser 300 segundos por padrão
```
