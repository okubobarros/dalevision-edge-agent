# Edge Agent Heartbeat e Camera Health, Perguntas Pendentes

## Lacunas Críticas

1. 🔴 Qual é o SLA final por ambiente para classificar edge/camera como `online`, `degraded` e `offline`?
   - Impacto: dashboards, alertas, suporte e retry/backoff.
   - Evidência atual: thresholds existem em backend e domínio, mas podem variar por piloto/prod.

2. 🔴 Depois de quanto tempo em `degraded` o agente deve gerar alerta externo ou reiniciar?
   - Impacto: watchdog, suporte remoto, ruído de alerta.

3. 🔴 `CAMERA_SYNC_FATAL=0` deve ser padrão em produção?
   - Impacto: disponibilidade do heartbeat versus visibilidade de falhas de câmera.

4. 🔴 Quais campos de `camera_health` são obrigatórios para compatibilidade com dashboards atuais?
   - Impacto: risco de quebrar frontend/backend se reimplementação simplificar payload.

5. 🔴 O backend deve aceitar `edge_token` em query string em produção ou isso é apenas legado?
   - Impacto: segurança e compatibilidade.

## Decisão Recomendada

🟡 INFERIDO: Manter todos os campos atuais e endurecer somente depois de uma suíte de regressão que compare payloads reais do agente instalado contra o backend atual.
