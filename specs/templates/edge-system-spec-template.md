# Edge System Spec Template

- Título / ID: `EDGE-SPEC-XXX - <tema>`
- Objetivo: problema do edge que a spec resolve.
- Escopo: o que está dentro (protocolo, update, health) e fora (decisão de negócio, UX cloud).
- Compatibilidade: versões mínimas do agente e do protocolo; impactos em heartbeat/camera health.
- Fluxo/estados: descrever estados principais (init, online, degraded, offline, updating) e transições.
- APIs/contratos: endpoints utilizados, schemas, eventos emitidos.
- Config/flags: variáveis de ambiente relevantes e defaults.
- Observabilidade: métricas, logs, códigos de erro curtos.
- Operação em campo: como validar, rollback, evidências.
- Riscos e fallback: cenários de falha e mitigação.
- Critérios de pronto: condições verificáveis antes de liberar.
