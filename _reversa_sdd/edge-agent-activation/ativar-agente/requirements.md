# Ativar Agente, Requirements

## Visão Geral

🟢 CONFIRMADO: Caso de uso em que um agente sem device identity usa `activation_token` para se registrar no backend e receber credenciais permanentes de operação.

## Requisitos

| ID | Requisito | Prioridade | Critério |
|---|---|---|---|
| RF-ATV-01 | 🟢 Aceitar token novo e device_key. | Must | Request contém token + device_key. |
| RF-ATV-02 | 🟢 Enviar versão instalada e canal. | Should | Request contém `installed_version` e `update_channel`. |
| RF-ATV-03 | 🟢 Persistir credenciais em sucesso. | Must | Config contém edge_token/store/device após sucesso. |
| RF-ATV-04 | 🟢 Marcar estado `active`. | Must | `ActivationBootstrapOutcome.state == ACTIVE`. |
| RF-ATV-05 | 🟢 Não reutilizar token após sucesso. | Must | `activation_token=None`. |

## Critérios de Aceitação

```gherkin
Dado um agente novo com activation_token válido
Quando ativar
Então deve receber edge_token e device_id
E deve entrar em active
```

## Rastreabilidade

| Arquivo | Símbolo | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/activation.py` | `ActivationClient.activate`, `bootstrap_activation` | 🟢 |
| `C:\workspace\dale-vision\apps\stores\views_activation.py` | `StoreActivateView` | 🟢 |
