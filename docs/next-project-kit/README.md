# Next Project Kit (Edge Agent v2)

Objetivo: reduzir friccao de onboarding e operacao do edge agent, mantendo compatibilidade do protocolo atual (heartbeat/camera health) e melhorando confiabilidade desde download ate geracao de dados.

## Conteudo
- `01-diagnostico-erros.md`: erros recorrentes e causa-raiz.
- `02-experiencia-alvo.md`: fluxo novo de ativacao em tela unica com progresso.
- `03-reuso-legado.md`: o que manter/reutilizar do projeto atual.
- `04-roteiro-execucao.md`: plano de execucao com fases e DoD.
- `template/`: estrutura base para novo repositorio (PRD, AGENTS, CI/CD, etc.).

## Principios obrigatorios
- Nao quebrar compatibilidade do protocolo atual de heartbeat e camera health.
- Diagnostico primeiro: mensagens claras, codigos curtos e orientacao para leigo.
- Nunca logar segredos (token/senha RTSP).
- Primeiro heartbeat valido deve destravar onboarding no backend, sem confirmacao manual no frontend.
