# Edge Agent Activation, Edge Cases

| ID | Caso | Comportamento esperado | Evidência | Confiança |
|---|---|---|---|---|
| EC-ACT-01 | Activation token ausente | Estado `unprovisioned`; log claro. | `activation.py` `missing_activation_token` | 🟢 |
| EC-ACT-02 | Cloud base URL ausente | Estado `error`; não chama backend. | `activation.py` `missing_cloud_base_url` | 🟢 |
| EC-ACT-03 | Device já possui `device_key` e `edge_device_id` | Retorna `active` sem reativar. | `activation.py` `has_device` | 🟢 |
| EC-ACT-04 | Falha de rede | Estado `activating`; retry permitido. | `ActivationResult.network_error` | 🟢 |
| EC-ACT-05 | Token inválido/expirado | Estado `error` se backend retorna 401/403. | `bootstrap_activation`; backend views | 🟢 |
| EC-ACT-06 | Token já usado/conflito | Estado `error` em 409. | `bootstrap_activation` | 🟢 |
| EC-ACT-07 | Resposta 2xx sem payload completo | Campos podem ficar vazios; deve ser tratado por validação posterior. | `bootstrap_activation` usa fallback `payload.get(...) or data.get(...)` | 🟡 |
| EC-ACT-08 | `.env` existente com outras chaves | Hidratação deve atualizar chaves conhecidas e preservar demais linhas. | `hydrate_runtime_env_from_activation_config` | 🟢 |
| EC-ACT-09 | Token bruto em log | Não permitido; usar tamanho/máscara. | `activation.py`; `edge/auth.py` | 🟢 |
| EC-ACT-10 | Store bloqueada após ativação | Edge auth posterior deve negar 403 por status/blocked_reason. | `apps/edge/auth.py` | 🟢 |

## Cenários

```gherkin
Dado um agente sem device identity
E sem activation_token
Quando executar bootstrap_activation
Então o estado deve ser unprovisioned
```

```gherkin
Dado um activation_token válido
Quando o backend retornar edge_token e device_id
Então a config local deve persistir credenciais
E activation_token deve ser removido
```

```gherkin
Dado um activation_token expirado
Quando a ativação retornar 401 ou 403
Então o estado deve ser error
```
