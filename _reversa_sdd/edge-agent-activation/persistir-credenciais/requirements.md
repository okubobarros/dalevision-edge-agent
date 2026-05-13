# Persistir Credenciais, Requirements

## Visão Geral

🟢 CONFIRMADO: Após ativação bem-sucedida, o agente deve persistir credenciais de operação e hidratar ambiente local sem vazar segredos.

## Requisitos

| ID | Requisito | Prioridade | Critério |
|---|---|---|---|
| RF-PC-01 | 🟢 Persistir `edge_token`. | Must | Config e `.env` podem fornecer token ao runtime. |
| RF-PC-02 | 🟢 Persistir `store_id`. | Must | Heartbeat posterior identifica loja. |
| RF-PC-03 | 🟢 Persistir `device_key` e `edge_device_id`. | Must | Bootstrap futuro detecta device existente. |
| RF-PC-04 | 🟢 Remover `activation_token`. | Must | Config salva `activation_token=None`. |
| RF-PC-05 | 🟢 Não logar token bruto. | Must | Log usa `edge_token_len`. |

## Critérios

```gherkin
Dado payload de ativação com edge_token
Quando persistir credenciais
Então activation_token deve ser removido
E o log não deve conter o valor do edge_token
```
