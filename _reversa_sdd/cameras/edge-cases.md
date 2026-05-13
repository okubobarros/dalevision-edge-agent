# cameras - Edge Cases

## Cadastro

- 🟢 `store_id` ausente retorna `CAMERA_VALIDATION_ERROR`.
- 🟢 Store inexistente retorna `STORE_NOT_FOUND`.
- 🟢 Usuário sem papel retorna `PERMISSION_DENIED`.
- 🟢 Trial expirado retorna `PAYWALL_TRIAL_LIMIT`.
- 🟢 Limite de câmeras retorna `LIMIT_CAMERAS_REACHED`.
- 🟢 Atualizar câmera inativa para ativa revalida limite.

## Segredos

- 🟢 Senha vazia em update é ignorada para não apagar senha existente acidentalmente.
- 🟢 `rtsp_url` e `password` não aparecem no serializer público.
- 🟢 Logs sanitizam `password` e `rtsp_url`.
- 🟡 Endpoint operacional para edge recebe segredos completos por design.

## ROI

- 🟢 `config_json` inválido retorna `400`.
- 🟢 Status inválido retorna `400`.
- 🟢 Publicar sem zonas/linhas retorna `400`.
- 🟢 Publicar nova versão sem validação da anterior retorna `409 ROI_VALIDATION_REQUIRED`.
- 🟢 Falha ao consultar ROI retorna `ROI_UNAVAILABLE`.
- 🟢 Falha ao salvar ROI retorna `ROI_SAVE_FAILED`.

## Health

- 🟢 Status textual desconhecido retorna `400`.
- 🟢 Status `error/failed/down/unreachable` vira `offline`.
- 🟢 Timestamp inválido cai para `timezone.now()`.
- 🟢 Edge Token inválido retorna `edge_token_invalid`.

## RTSP

- 🟢 Câmera sem RTSP retorna `CAMERA_RTSP_MISSING`.
- 🟢 Sem OpenCV, probe tenta TCP.
- 🟢 Processo de probe vivo após hard timeout é terminado.
- 🟢 Resultado sem queue retorna `rtsp_probe_no_result`.

## Snapshot

- 🟢 Sem arquivo retorna `SNAPSHOT_MISSING`.
- 🟢 Storage não configurado retorna `STORAGE_NOT_CONFIGURED`.
- 🟢 Tipo diferente de JPEG/PNG retorna `SNAPSHOT_INVALID_TYPE`.
- 🟢 Falha de upload retorna `SNAPSHOT_UPLOAD_FAILED`.
- 🟢 Falha ao assinar URL retorna `SNAPSHOT_SIGN_FAILED`.
- 🟢 Sem snapshot retorna `SNAPSHOT_NOT_FOUND`.
- 🟢 Catálogo indisponível é tolerado no upload/delete, com warning.

## Edge Snapshot

- 🟢 Token inválido retorna 401.
- 🟢 Câmera fora da store do token retorna 404.
- 🟢 Sem arquivo `snapshot` retorna 400.
- 🟢 Falha no driver Supabase retorna 500.
