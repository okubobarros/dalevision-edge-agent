# stores - Flows

## Fluxo 1 - Ativar Loja Edge

1. 🟢 Gestor chama `/stores/{store_id}/activation-token/`.
2. 🟢 Backend valida store e papel.
3. 🟢 Backend desativa activation tokens anteriores.
4. 🟢 Backend gera token, salva hash e retorna segredo.
5. 🟢 Agente chama `/stores/activate/`.
6. 🟢 Backend valida token, expiração e store.
7. 🟢 Backend cria/atualiza `EdgeDevice`.
8. 🟢 Backend marca activation token usado/inativo.
9. 🟢 Backend desativa edge tokens ativos anteriores e emite novo Edge Token.
10. 🟢 Agente persiste `edge_token` localmente.

## Fluxo 2 - Consultar Status Edge

1. 🟢 Frontend chama `/stores/{store_id}/edge-status/`.
2. 🟢 Backend valida acesso de leitura.
3. 🟢 Backend lê câmeras ativas.
4. 🟢 Backend busca último health log por câmera.
5. 🟢 Backend busca heartbeats em `event_receipts` e `EdgeEventMinuteStats`.
6. 🟢 Backend classifica conectividade e câmera.
7. 🟢 Backend calcula `store_status` e `pipeline_status`.
8. 🟢 Backend completa onboarding `edge_connected` se online.
9. 🟢 Responde payload estável.

## Fluxo 3 - Sincronizar Câmeras com Agente

1. 🟢 Agente chama `GET /stores/{store_id}/cameras` com Edge Token.
2. 🟢 Backend valida token contra a store.
3. 🟢 Backend filtra câmeras ativas.
4. 🟢 Backend resolve RTSP operacional.
5. 🟢 Backend registra `edge_camera_sync_pull`.
6. 🟢 Backend retorna lista operacional.

## Fluxo 4 - Gerenciar Release

1. 🟢 Staff chama `/edge/releases/`.
2. 🟢 Backend valida versão, canal e URL.
3. 🟢 Backend cria/atualiza `EdgeRelease`.
4. 🟢 Se ativa, desativa releases anteriores do canal.
5. 🟢 Agentes/instaladores consultam `/edge/releases/latest/`.

## Fluxo 5 - Solicitar Update de Loja

1. 🟢 Gestor chama `/stores/{store_id}/edge/update/`.
2. 🟢 Backend seleciona device e policy existentes.
3. 🟢 Backend escolhe canal por device, policy ou stable.
4. 🟢 Backend busca release ativa.
5. 🟢 Backend valida SHA.
6. 🟢 Backend cria/atualiza `EdgeUpdatePolicy`.
7. 🟢 Se não estiver up-to-date, cria `EdgeUpdateEvent` queued/requested.
8. 🟢 Agente consome policy em `/api/edge/update-policy/`.

## Fluxo 6 - Canary

1. 🟢 Staff cria release canary.
2. 🟢 Staff chama batch-tag com percentual.
3. 🟢 Backend amostra lojas active/trial.
4. 🟢 Backend aplica policy canary e registra evento.
5. 🟢 Staff acompanha canary health.
6. 🟢 Se necessário, rollback aplica stable release nas policies canary.
