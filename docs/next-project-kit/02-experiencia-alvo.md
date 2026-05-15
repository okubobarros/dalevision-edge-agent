# Experiencia Alvo (Tela Unica + Barra de Progresso)

## Fluxo proposto
1. Usuario cria loja e clica em `Ativar Edge`.
2. App abre modal/tela unica com barra de progresso e status em tempo real.
3. Backend entrega `download-agent` com onboarding ref efemero.
4. Usuario executa instalador com duplo clique.
5. Edge faz bootstrap de ativacao e envia primeiro heartbeat.
6. Frontend avanca automaticamente para configuracao de cameras.
7. Primeira camera valida inicia geracao de dados e conclui onboarding.

## Etapas da barra
1. `Download do Agente`
2. `Instalacao Local`
3. `Conexao com a Nuvem`
4. `Descoberta de Cameras`
5. `Primeira Camera Validada`
6. `Diagnostico Inicial Iniciado`

## Regras de UX
- Nada de botao "ja conclui" para pular etapa.
- Cada etapa exibe: status, tempo estimado, erro curto (se houver), proxima acao.
- Timeout de etapa gera fallback com CTA unico (ex.: `Rodar Diagnostico`).

## Contratos minimos
- `GET /api/v1/stores/{store_id}/download-agent`
- `GET /api/v1/stores/{store_id}/status`
- Heartbeat atual preservado; novos campos opcionais.

## SLO inicial
- activation_success_rate >= 90%
- median_time_to_activation < 15 min
- auto-advance apos primeiro heartbeat <= 10s
