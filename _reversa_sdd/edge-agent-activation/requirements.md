# Edge Agent Activation

## Visão Geral

🟢 CONFIRMADO: Esta unit especifica o fluxo de ativação do agente Windows instalado no cliente. O agente usa um `activation_token` temporário e single-use para obter `edge_token`, `store_id`, `device_key`, `edge_device_id`, canal de update e versão persistidos localmente.

🟢 CONFIRMADO: O fluxo integra os dois repositórios: `dalevision-edge-agent` executa `ActivationClient` e `bootstrap_activation`; `dale-vision` emite token no backend `stores` e ativa device edge por endpoint público controlado.

## Responsabilidades

- 🟢 Emitir e consumir `activation_token` temporário/single-use.
- 🟢 Gerar ou reutilizar `device_key` local.
- 🟢 Chamar backend de ativação com token, device, versão instalada e canal de update.
- 🟢 Persistir credenciais recebidas e remover `activation_token` após sucesso.
- 🟢 Hidratar variáveis de runtime em memória e opcionalmente em `.env`.
- 🟢 Tratar rede como erro recuperável e 401/403/409 como erro não recuperável.
- 🟢 Nunca logar `activation_token` ou `edge_token` bruto.

## Regras de Negócio

- 🟢 `activation_token` é temporário e `single_use=True`.
- 🟢 Token emitido pelo backend possui TTL configurável por `EDGE_ACTIVATION_TOKEN_TTL_SECONDS`, com fallback de 24h.
- 🟢 Agente já provisionado com `device_key` e `edge_device_id` não deve reativar.
- 🟢 Ativação bem-sucedida muda `AgentState` para `active`.
- 🟢 Erro de rede durante ativação mantém estado `activating`, permitindo retry.
- 🟢 HTTP 401, 403 ou 409 durante ativação muda estado para `error`.
- 🟢 Após sucesso, `activation_token` local deve ser definido como `None`.
- 🟡 O backend marca o token como usado no serviço `activate_edge_device`; a leitura direta do service não foi expandida nesta etapa, mas é confirmada por state machine e view.

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|---|---|---|---|
| RF-ACT-01 | 🟢 Backend deve emitir activation token por loja para usuário autenticado autorizado. | Must | `StoreActivationTokenView.post` retorna `201`, `activation_token`, `expires_at`, `expires_in_seconds`, `single_use=True`. |
| RF-ACT-02 | 🟢 Agente deve armazenar token recebido antes de tentar ativação. | Must | `bootstrap_activation` grava `activation_token` via `ConfigManager.update_partial`. |
| RF-ACT-03 | 🟢 Agente deve gerar `device_key` quando ainda não existir. | Must | `_generate_device_key()` retorna `edge-<uuid>`. |
| RF-ACT-04 | 🟢 Agente deve chamar endpoint de ativação com `activation_token`, `device_key`, `installed_version` e `update_channel`. | Must | `ActivationClient.activate` monta body e faz `requests.post`. |
| RF-ACT-05 | 🟢 Backend deve retornar credenciais operacionais após ativação. | Must | `StoreActivateView` retorna `store_id`, `device_key`, `device_id`, `update_channel`, `edge_token`. |
| RF-ACT-06 | 🟢 Agente deve persistir credenciais e limpar `activation_token`. | Must | `bootstrap_activation` grava payload e `activation_token=None`. |
| RF-ACT-07 | 🟢 Agente deve tratar erro de rede como retry. | Must | `ActivationResult(network_error=True)` mantém `AgentState.ACTIVATING`. |
| RF-ACT-08 | 🟢 Agente deve tratar 401/403/409 como erro de ativação não recuperável. | Must | `bootstrap_activation` muda para `AgentState.ERROR`. |
| RF-ACT-09 | 🟢 `.env` deve ser hidratável com cloud/store/token/agent sem logar token bruto. | Should | `hydrate_runtime_env_from_activation_config` escreve valores e loga apenas `edge_token_len`. |
| RF-ACT-10 | 🟢 Edge token explícito deve autenticar chamadas posteriores via `X-EDGE-TOKEN`. | Must | `apps/edge/auth.py` dá precedência a `X-EDGE-TOKEN`. |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência | Confiança |
|---|---|---|---|
| Segurança | Tokens brutos não podem aparecer em logs. | `activation.py` loga `edge_token_len`; `edge/auth.py` mascara token por hash parcial. | 🟢 |
| Segurança | Activation token deve ser temporário e single-use. | `views_activation.py` retorna `single_use=True`; `state-machines.md`. | 🟢 |
| Disponibilidade | Falha de rede na ativação deve permitir retry. | `bootstrap_activation` `activation_network_retry`. | 🟢 |
| Operabilidade | Erros devem carregar `status_code`, `error_code` e `error_detail`. | `ActivationResult`. | 🟢 |

## Critérios de Aceitação

```gherkin
Dado uma loja autorizada
Quando o backend emitir activation token
Então a resposta deve conter activation_token, expires_at, expires_in_seconds e single_use igual a true
```

```gherkin
Dado um agente sem device e com activation_token válido
Quando a ativação retornar sucesso
Então o agente deve persistir edge_token, store_id, device_key e edge_device_id
E deve remover activation_token da configuração local
```

```gherkin
Dado uma falha de rede ao ativar
Quando o agente executar bootstrap_activation
Então o estado deve permanecer activating para retry
```

```gherkin
Dado um token inválido ou usado
Quando o backend responder 401, 403 ou 409
Então o agente deve entrar em error
```

## Rastreabilidade

| Arquivo | Função / Classe | Cobertura |
|---|---|---|
| `src/dalevision_edge_agent/activation.py` | `ActivationClient`, `ActivationResult`, `bootstrap_activation`, `hydrate_runtime_env_from_activation_config` | 🟢 |
| `C:\workspace\dale-vision\apps\stores\views_activation.py` | `StoreActivationTokenView`, `StoreActivateView` | 🟢 |
| `C:\workspace\dale-vision\apps\edge\auth.py` | `authenticate_edge_token`, `_extract_store_token`, `_mask_token` | 🟢 |
| `_reversa_sdd/adrs/0002-token-activation-single-use.md` | decisão arquitetural | 🟢 |
| `_reversa_sdd/state-machines.md` | `AgentState`, `ActivationToken` | 🟢 |
