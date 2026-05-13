# ativar-loja-edge - Requirements

## Escopo

- 🟢 Caso de uso de emissão de token de ativação e ativação do agente local.
- 🟢 Fontes: `views_activation.py` e `services/activation_registry.py`.

## Requisitos

- 🟢 Gestor deve emitir activation token para store existente.
- 🟢 Activation token deve ser single-use e expirar.
- 🟢 Tokens anteriores ativos devem ser desativados.
- 🟢 Agente deve ativar usando token, device_key/version/channel.
- 🟢 Device key ausente deve ser gerado.
- 🟢 Device key em outra loja deve ser rejeitado.
- 🟢 Device retired deve ser rejeitado.
- 🟢 Ao ativar, deve emitir Edge Token novo e desativar Edge Tokens ativos anteriores.
- 🟢 Activation token deve ser marcado `used_at` e `is_active=false`.

## Critérios de Aceitação

- 🟢 Dado token válido, quando agente ativar, então recebe `edge_token` e `device_key`.
- 🟢 Dado token expirado, quando agente ativar, então recebe `activation_token_expired`.
- 🟢 Dado store edge-disabled, quando agente ativar, então recebe `activation_store_disabled`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_activation.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_registry.py`.
