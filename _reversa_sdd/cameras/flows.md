# cameras - Flows

## Fluxo 1 - Criar Câmera

1. 🟢 Usuário envia POST com `store_id`.
2. 🟢 Backend valida store.
3. 🟢 Backend exige papel de gestão.
4. 🟢 Backend valida entitlement/trial.
5. 🟢 Serializer valida dados.
6. 🟢 Limite de câmeras ativas é aplicado.
7. 🟢 Câmera é salva com timestamps.
8. 🟢 Staff action e journey `camera_added` são registrados.

## Fluxo 2 - Publicar ROI

1. 🟢 Usuário gestor chama PUT `/cameras/{id}/roi/`.
2. 🟢 Backend valida `config_json`.
3. 🟢 Backend valida status.
4. 🟢 Se published, exige zona ou linha.
5. 🟢 Se já havia published, exige validação aprovada da versão anterior.
6. 🟢 Backend incrementa `roi_version`.
7. 🟢 Cria `CameraROIConfig`.
8. 🟢 Registra `roi_saved`.
9. 🟢 Completa onboarding `roi_published`.

## Fluxo 3 - Registrar Health

1. 🟢 Edge ou usuário envia POST `/cameras/{id}/health/`.
2. 🟢 Backend valida Edge Token ou papel de gestão.
3. 🟢 Normaliza status.
4. 🟢 Resolve `checked_at`.
5. 🟢 Cria `CameraHealthLog`.
6. 🟢 Atualiza campos denormalizados da câmera.
7. 🟢 Se online/degraded, completa onboarding e registra validação quando aplicável.

## Fluxo 4 - Testar RTSP

1. 🟢 Usuário gestor chama `/test_connection/`.
2. 🟢 Backend valida RTSP.
3. 🟢 Probe roda em processo separado.
4. 🟢 Sucesso marca online e cria health log.
5. 🟢 Falha marca offline e cria health log.
6. 🟢 Timeout retorna reason específico.

## Fluxo 5 - Snapshot Backend

1. 🟢 Usuário gestor envia multipart.
2. 🟢 Backend valida storage, org e content type.
3. 🟢 Gera storage key.
4. 🟢 Faz upload Supabase.
5. 🟢 Gera signed URL.
6. 🟢 Cria `CameraSnapshot` quando possível.
7. 🟢 Atualiza `last_snapshot_url`.

## Fluxo 6 - Snapshot Edge

1. 🟢 Agente envia multipart para `/api/edge/cameras/{camera_id}/snapshot/`.
2. 🟢 Backend autentica Edge Token.
3. 🟢 Confirma que câmera pertence à store do token.
4. 🟢 Sobe arquivo no Supabase.
5. 🟢 Atualiza `last_snapshot_url`.
