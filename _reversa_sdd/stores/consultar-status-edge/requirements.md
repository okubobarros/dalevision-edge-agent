# consultar-status-edge - Requirements

## Escopo

- 🟢 Caso de uso de status operacional e status de ativação da loja.
- 🟢 Fontes: `views_edge_status.py`, `views_activation_status.py`, `services/activation_status.py`.

## Requisitos

- 🟢 Usuário deve estar autenticado.
- 🟢 Acesso deve respeitar papel de leitura.
- 🟢 Status edge deve combinar sinais de loja, câmeras, health logs, receipts e minute stats.
- 🟢 Deve classificar conectividade por idade.
- 🟢 Deve contar câmeras online/degraded/offline/unknown.
- 🟢 Deve retornar payload estável mesmo quando store não existe ou usuário não tem acesso.
- 🟢 Status de ativação deve derivar `activation_state`, `technical_status`, `value_status` e `next_action`.
- 🟢 Deve incluir device ativo mais recente, versão instalada, câmeras e ROI.
- 🟢 Deve incluir funil de onboarding baseado em `EdgeEventRaw`.

## Critérios de Aceitação

- 🟢 Store com câmera online retorna `store_status=online` ou `degraded`.
- 🟢 Store sem câmeras mas com edge recente retorna `online_no_cameras`.
- 🟢 Sem heartbeat retorna `offline` com reason adequado.
- 🟢 Ativação sem device retorna `pending_activation` e `issue_activation_token`.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\stores\views_edge_status.py`.
- 🟢 `C:\workspace\dale-vision\apps\stores\services\activation_status.py`.
