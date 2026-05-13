# frontend-cameras-alerts

## Visão Geral
Módulo responsável pelas páginas de gestão de câmeras, alertas operacionais e regras de alerta do DaleVision. É o hub de configuração de infraestrutura de visão computacional e de resposta a eventos operacionais.

## Responsabilidades
- Listar, criar, editar e excluir câmeras de uma loja, com suporte a descoberta local via ONVIF/blueprint do Edge Agent
- Configurar ROI (Region of Interest) de câmeras via `CameraRoiEditor`
- Testar conectividade RTSP de câmeras com cooldown de 8s
- Diagnosticar falhas de câmera (credencial, conectividade, stream, heartbeat) com ação recomendada
- Exibir alertas operacionais com filtros (severidade, status, loja, data) em layout master-detail
- Gerenciar resolução de alertas: resolução local, delegação por e-mail, escalação técnica
- Gerenciar regras de alerta (trigger, severidade, cooldown, canais) com análise de qualidade por regra
- Controlar acesso por role (`owner/admin/manager`) com extensão via support grant
- Acompanhar progresso de onboarding de câmeras (checklist de ativação)

## Regras de Negócio

### Câmeras
- `edgeOnline`: derivado de `connectivity_status in [online, degraded]` ou `online === true` ou `connectivity_age_seconds <= 120s` 🟢 (`Cameras.tsx:485-491`)
- `canEditRoi`: `canManageStore || user.is_staff || user.is_superuser` 🟢 (`Cameras.tsx:593`)
- `canManageStore`: `role in [owner, admin, manager]` + `selectedStore !== "all"` 🟢 (`Cameras.tsx:397-399`)
- **Support Grant**: `canManageStore` é estendido se há `supportRequest.status === "granted"` com `expires_at` no futuro 🟢 (`Cameras.tsx:583-592`)
- Câmeras buscadas diferentemente em modo rede: `selectedStore === "all"` → `camerasService.getCameras()` global; fallback via `Promise.all` por loja 🟢 (`Cameras.tsx:441-460`)
- Retry de câmeras: apenas 1 retry; somente em ECONNABORTED, timeout, 502/503/504 🟢 (`Cameras.tsx:465-483`)
- Cache de ROI publicadas em `localStorage` por loja: chave `dv_roi_published_cameras_v1_<storeId>` 🟢 (`Cameras.tsx:44,595-638`)
- ROI só pode ser aberto se `canEditRoi` — toast de erro caso contrário 🟢 (`Cameras.tsx:651-654`)
- `?openRoi=1&zone_id=<id>` abre ROI da câmera com `camera.zone_id === zone_id` automaticamente 🟢 (`Cameras.tsx:641-656`)
- Paywall: código `PAYWALL_TRIAL_LIMIT` ou `LIMIT_CAMERAS_REACHED` exibe toast customizado com link para billing 🟢 (`Cameras.tsx:760-782`)
- **Local Blueprint** (ONVIF): busca IPs via `EDGE_SETUP_LOCAL_BASE_URL = "http://127.0.0.1:8787"` (Setup API local do Edge Agent) 🟢 (`Cameras.tsx:45`)
- Indicadores de câmera (CameraIndicatorKey): `flow` (contador), `queue` (fila), `productivity` (equipe) 🟢 (`Cameras.tsx:151-173`)
- Diagnóstico de falha segue cascata: RTSP missing/credencial → heartbeat → conectividade → stream 🟢 (`Cameras.tsx:235-301`)

### Alertas
- Filtros: severidade (`critical/warning/info/all`), status (`open/resolved/ignored/all`), loja, texto livre, intervalo de datas 🟢 (`Alerts.tsx:89-109`)
- Filtro de data usa `T00:00:00` e `T23:59:59` locais para `occurred_from` e `occurred_to` 🟢 (`Alerts.tsx:190-198`)
- SLA Timer: 30 minutos a partir de `occurred_at` do evento; exibe countdown e muda para overdue com `animate-pulse` 🟢 (`Alerts.tsx:755-777`)
- Resolução tripartite: `resolvido_localmente` (resolve direto), `delegado` (e-mail + ignore), `incidente_tecnico` (ignore + escalação) 🟢 (`Alerts.tsx:390-411`)
- Delegação via `alertsService.delegateEventEmail` retorna `{ ok, employee.name, message }` 🟢 (`Alerts.tsx:294-320`)
- Escalação técnica navega para `/app/edge-help?store_id=...&camera_id=...&event_id=...` 🟢 (`Alerts.tsx:322-350`)
- `reasonRequired = delegado || incidente_tecnico` — bloqueia submit sem motivo 🟢 (`Alerts.tsx:353-354`)
- Botão "Simular Evento" visível apenas em `import.meta.env.DEV` 🟢 (`Alerts.tsx:223`)
- `normalizeArray`: suporta resposta como array, `{data:[]}` ou `{results:[]}` 🟢 (`Alerts.tsx:67-78`)
- Analytics: `trackJourneyEvent("alert_resolution_completed", {...})` em todas as resoluções 🟢 (`Alerts.tsx:413-421`)

### Regras de Alerta
- Tipos válidos: `queue_long`, `staff_missing`, `suspicious_cancel` 🟢 (`AlertRules.tsx:40-45`)
- Canais: `dashboard` (padrão habilitado), `email`, `whatsapp` 🟢 (`AlertRules.tsx:34`)
- Cooldown padrão: 15 minutos 🟢 (`AlertRules.tsx:170`)
- **Qualidade da regra** calculada no frontend: `score = 100 - suppressionRate×60 - failureRate×40`; nenhum log → score=60 (base) 🟢 (`AlertRules.tsx:111-157`)
- Sugestão automática: `suppressionRate >= 0.4 && totalLogs >= 6` → aumentar cooldown; `failureRate >= 0.2` → revisar canais 🟢 (`AlertRules.tsx:123-147`)
- Aplicar sugestão de cooldown via mutação `updateRule` com `trackJourneyEvent("alert_rule_suggestion_applied")` 🟢 (`AlertRules.tsx:304-332`)
- `storeId` resolução: `storeIdOverride` se definido, senão primeira loja da lista 🟢 (`AlertRules.tsx:182-186`)
- Analytics: `trackJourneyEvent("alert_rule_quality_viewed")` na montagem por regra 🟢 (`AlertRules.tsx:248-258`)

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|------------|-------------------|
| RF-01 | Listar câmeras por loja com status de conectividade (online/offline) | Must | Lista atualizada a cada 15s (staleTime: 15s); modo rede agrega câmeras de todas as lojas |
| RF-02 | Criar câmera manualmente com formulário (nome, IP, usuário, senha, RTSP URL) | Must | Toast "Câmera criada"; queryClient invalida `store-cameras` e `store-limits` |
| RF-03 | Criar câmera via blueprint local (ONVIF discovery do Edge Agent) | Should | Blueprint busca IPs de http://127.0.0.1:8787; seleção de IPs pré-preenche formulário |
| RF-04 | Testar conectividade RTSP de câmera com cooldown de 8s | Must | Cooldown impede novo teste por 8s; toast de sucesso/erro com mensagem do backend |
| RF-05 | Abrir ROI Editor para câmera com controle de permissão | Must | Apenas owner/admin/manager/staff/superuser abrem ROI; toast de erro para sem permissão |
| RF-06 | Abertura automática de ROI via `?openRoi=1&zone_id=<id>` | Should | Câmera com `zone_id` correspondente é selecionada e ROI aberto |
| RF-07 | Diagnosticar falha de câmera (credencial, heartbeat, conectividade, stream) | Must | Diagnóstico exibido inline com título e ação recomendada |
| RF-08 | Detectar paywall (LIMIT_CAMERAS_REACHED) e exibir CTA para billing | Must | Toast customizado com link para `/app/billing` |
| RF-09 | Cache local de ROI publicadas por loja em localStorage | Should | Câmeras com ROI publicado marcadas visualmente sem nova requisição |
| RF-10 | Exibir alertas com filtros (severidade, status, loja, data, texto) | Must | Lista filtrada; zero resultados exibe estado vazio |
| RF-11 | Layout master-detail de alertas (inbox + drawer de detalhes) | Should | Coluna de detalhe oculta sem seleção em mobile; visível em desktop |
| RF-12 | SLA Timer dinâmico de 30 minutos por alerta | Should | Countdown atualizado a cada 1s; overdue com animate-pulse |
| RF-13 | Fluxo de resolução tripartite (local/delegado/técnico) com motivo obrigatório | Must | Delegado e incidente_tecnico exigem motivo; resolve/ignore chamados conforme tipo |
| RF-14 | Delegação de alerta por e-mail com feedback do destinatário | Should | `delegateEventEmail` → toast com nome do funcionário ou mensagem genérica |
| RF-15 | Escalação técnica para `/app/edge-help` com contexto de loja/câmera/evento | Should | navigate com params corretos; `trackJourneyEvent("incident_escalate_clicked")` |
| RF-16 | Listar e criar regras de alerta por loja | Must | Formulário com tipo, severidade, cooldown, canais; toast "Regra criada" |
| RF-17 | Exibir qualidade de cada regra com score e sugestões automáticas | Should | Score calculado frontend por suppression/failure rate; badge alto/medio/baixo |
| RF-18 | Aplicar sugestão de cooldown automaticamente | Should | Mutação `updateRule` com novo cooldown; toast de confirmação |

## Critérios de Aceitação (Gherkin)

```gherkin
# RF-05 — ROI sem permissão
Dado que o usuário tem role "viewer" e não tem support grant
Quando tenta abrir o ROI de uma câmera
Então toast.error("Sem permissão para abrir o ROI desta câmera.") é exibido

# RF-08 — Paywall
Dado que a loja atingiu o limite de câmeras do plano
Quando o formulário de criação é submetido
Então response.code === "LIMIT_CAMERAS_REACHED" → toast customizado com botão "Ir para billing"

# RF-13 — Resolução delegada sem motivo
Dado que tipo de resolução é "delegado"
E o campo de motivo está vazio
Quando "Confirmar" é clicado
Então toast.error("Informe um motivo curto para continuar.") é exibido

# RF-12 — SLA overdue
Dado que o alerta ocorreu há mais de 30 minutos
Quando o drawer de detalhes é aberto
Então timer exibe "-HH:MM:SS Delayed" com estilo rose e animate-pulse

# RF-17 — Regra sem histórico de logs
Dado que a regra não tem notificação de logs
Quando a qualidade é calculada
Então score = 60 (base), level = "medio", sem sugestão
```

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------| 
| `frontend/src/pages/Cameras/Cameras.tsx` | `Cameras`, `diagnoseCameraFailure`, `isPrivateIp`, `buildReadinessMarkdown`, `resolveNextCreatePrefill`, `cameraSourceSummary` | 🟢 |
| `frontend/src/pages/Alerts/Alerts.tsx` | `Alerts`, `normalizeArray`, `buildDelegationMessage`, `delegateToWhatsapp`, `handleSubmitResolution`, `buildRuleQuality` | 🟢 |
| `frontend/src/pages/AlertRules/AlertRules.tsx` | `AlertRulesPage`, `buildRuleQuality`, `parseRuleCreateError`, `handleApplySuggestion` | 🟢 |
| `frontend/src/components/CameraRoiEditor.tsx` | `CameraRoiEditor` | 🟡 (não lido) |
| `frontend/src/components/StoreActivationWizard.tsx` | `StoreActivationWizard` | 🟡 |
| `frontend/src/services/cameras.ts` | `camerasService`, `Camera`, `CreateCameraPayload` | 🟡 |
| `frontend/src/services/alerts.ts` | `alertsService`, `AlertRule`, `NotificationLog`, `AlertIngestPayload` | 🟡 |
| `frontend/src/queries/alerts.queries.ts` | `useAlertsEvents`, `useAlertLogs`, `useResolveEvent`, `useIgnoreEvent`, `useIngestAlert` | 🟡 |
| `frontend/src/services/support.ts` | `supportService` | 🟡 |
