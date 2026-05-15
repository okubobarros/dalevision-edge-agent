# Roteiro de Execucao (Comeco, Meio e Fim)

## Fase 0 - Alinhamento
- Definir PRD curto com metrica de sucesso de onboarding.
- Fechar contratos backend/frontend/edge para estado de ativacao.
- Congelar compatibilidade dos eventos legados.

## Fase 1 - Onboarding Foundation
- Implementar download inteligente por loja com token efemero.
- Implementar endpoint de status unico com `activation_state`.
- Tela unica no frontend com polling e auto-advance.

## Fase 2 - Edge Bootstrap
- Installer hidrata config sem edicao manual de `.env`.
- Ativacao inicial persistindo credenciais runtime.
- Heartbeat inicial com onboarding_ref/capabilities opcionais.

## Fase 3 - Cameras e Dados
- Descoberta assistida + fallback manual guiado.
- Persistencia de `indicators[]` por camera.
- Primeiro dado operacional validado no dashboard.

## Fase 4 - Harness + CI/CD
- Teste automatizado E2E do funil (registro -> dado).
- Pipeline de release windows com checklist de observabilidade.
- Gate de regressao para heartbeat/camera health.

## Fase 5 - Operacao e Evolucao
- Runbook de suporte com codigos curtos.
- Dashboard de funil e taxa de falha por etapa.
- Ciclo mensal de melhoria baseado em telemetria real.

## Definition of Done do novo projeto
- Usuario ativa sem terminal e sem editar `.env`.
- Frontend avanca por estados reais do backend.
- Primeira camera valida e dados chegam ao backend.
- Doctor share operacional e logs sanitizados.
- CI/CD impede merge com regressao de onboarding critico.
