# stores - Edge Cases

## Ativação

- 🟢 Store inexistente ao emitir token retorna `store_not_found`.
- 🟢 Usuário sem papel de gestão retorna `forbidden`.
- 🟢 Token de ativação ausente retorna `activation_token_required`.
- 🟢 Token inválido retorna `activation_token_invalid`.
- 🟢 Token já usado retorna `activation_token_already_used`.
- 🟢 Token expirado é marcado inativo e retorna `activation_token_expired`.
- 🟢 Store edge-disabled retorna `activation_store_disabled`.
- 🟢 Device key associado a outra loja retorna `device_key_conflict`.
- 🟢 Device retired retorna `device_retired`.

## Download

- 🟢 Setup URL ausente retorna `setup_url_not_configured`.
- 🟢 Token de download ausente retorna `download_token_required`.
- 🟢 Token inválido/expirado retorna `download_token_invalid`.
- 🟢 Store do token divergente retorna `download_store_mismatch`.
- 🟢 Target ausente retorna `download_target_missing`.

## Edge Access

- 🟢 POST com `enabled` diferente de `false` retorna `only_disable_supported`.
- 🟢 Desabilitar edge também retira devices e tokens, então agentes antigos passam a falhar auth.
- 🟡 Não há reenable simétrico no endpoint analisado.

## Status

- 🟢 Store inexistente em `/edge-status/` retorna payload offline em vez de 404.
- 🟢 Usuário sem acesso recebe payload estável com reason `forbidden` e status 200.
- 🟢 Banco indisponível retorna reason `db_unavailable`.
- 🟢 Erro inesperado retorna fallback com `request_id`.
- 🟢 Sem câmeras, loja pode ficar `online_no_cameras` se comunicação edge está recente.
- 🟢 Health log ausente mas sinal recente de câmera pode usar fallback operacional.

## Câmeras para Edge

- 🟢 Edge Token explícito inválido não cai para sessão de usuário.
- 🟢 Sem RTSP, connection_type vira `onvif` ou `unknown`.
- 🟢 RTSP pode ser reconstruído com credenciais atuais quando `rtsp_url` tem host.
- 🟢 Pull de câmeras falhando ao registrar stats apenas loga exceção.

## Update/Release

- 🟢 Canal inválido em latest cai para stable.
- 🟢 Release management sem versão/URL retorna `version_and_download_url_required`.
- 🟢 Trigger sem release ativa retorna `release_not_available`.
- 🟢 Trigger sem SHA retorna `package_sha256_missing`.
- 🟢 Device já na versão alvo retorna `already_up_to_date`, salvo force.
- 🟢 Runbook sem reason_code usa falha/rollback mais recente.

## Canary

- 🟢 Usuário não-staff recebe `PermissionDenied`.
- 🟢 Canary batch sem release retorna 404.
- 🟢 Lojas sem SHA são puladas com `package_sha256_missing`.
- 🟢 Sem lojas active/trial, batch retorna selected=0.

## Segurança

- 🟡 `token_plaintext` fica persistido no banco para edge setup; acesso indevido ao banco expõe segredo.
- 🟡 `edge-token-hint` mostra prefixo e sufixo em modo debug para staff/superuser.
