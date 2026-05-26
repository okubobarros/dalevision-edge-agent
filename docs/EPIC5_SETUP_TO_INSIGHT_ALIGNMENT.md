# Epic 5 Alignment — Setup to Insight Fluency

Date: 2026-05-26  
Repo: `dalevision-edge-agent`  
Linked cloud repo: `dale-vision`

## Objetivo
Alinhar o edge-agent à nova jornada unificada do produto:
`/activate -> setup/download -> install -> return-to-app -> first insight`.

## Contrato de jornada (edge -> cloud)
1. Usuário baixa instalador via app cloud (setup hub).
2. Instalação executa bootstrap local normalmente.
3. Ao finalizar, instalador deve tentar abrir URL canônica de retorno:
   - `/app/dashboard?openEdgeSetup=1&store_id=<STORE_ID>&source=edge_installer`
4. Se não conseguir abrir navegador, mostrar instrução objetiva com URL/copiar-colar.

## Requisitos UX mínimos no installer
- Mensagem final obrigatória:
  - “Instalação concluída. Clique em **Voltar para o DaleVision** para continuar a ativação.”
- Botão primário de retorno ao app.
- Botão secundário “Copiar link de retorno”.
- Erros legíveis para leigo (sem stack trace técnico).

## Telemetria recomendada (integração)
- `edge_installer_started`
- `edge_installer_completed`
- `edge_return_url_opened`
- `edge_return_url_open_failed`

## Dependências com o cloud app
- O app deve aceitar `store_id` no retorno e abrir passo de ativação automaticamente.
- O app deve exibir estado atual (edge online/offline, câmeras, ROI, first insight readiness).

## Checklist pré-loja (operação de campo)
- [ ] URL de retorno validada no ambiente real.
- [ ] `STORE_ID` resolvido corretamente no instalador.
- [ ] Mensagem de fallback testada (copiar/colar URL).
- [ ] Tempo total setup -> retorno ao app <= 5 minutos.
