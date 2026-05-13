# frontend-cameras-alerts — Tarefas de Implementação

## Tarefas — Câmeras

- [ ] T-01 — Implementar `isPrivateIp` e `isPrivateHost`
  - `Cameras.tsx:27-39` | Critério: `10.x`, `192.168.x`, `172.16-31.x`, `localhost` retornam true | 🟢

- [ ] T-02 — Implementar `diagnoseCameraFailure({ camera, realtimeReason, edgeOnline })`
  - `Cameras.tsx:235-301` | Critério: cascata credencial → heartbeat → conectividade → stream; online/degraded retorna null | 🟢

- [ ] T-03 — Implementar `formatRelativeTime`, `formatExactDateTime`, `formatAgeLabel` (versões Cameras)
  - `Cameras.tsx:175-213` | Critério: formatação pt-BR correta; segundos/minutos/horas/dias | 🟢

- [ ] T-04 — Implementar `buildReadinessMarkdown(report)` e `downloadTextFile`
  - `Cameras.tsx:99-141` | Critério: arquivo Markdown com status, checks, missing env gerado; link para download | 🟢

- [ ] T-05 — Implementar `cameraSourceSummary` derivado de `edgeStatus`
  - `Cameras.tsx:493-531` | Critério: `api_first` → emerald; `local_only_or_unknown` → amber (instável/contingência); else → gray | 🟢

- [ ] T-06 — Implementar `edgeCameraMap` (Map de cameras do edge por camera_id)
  - `Cameras.tsx:533-542` | Critério: Map<cameraId, EdgeCameraRow> para lookup rápido | 🟢

- [ ] T-07 — Implementar `edgeOnline` derivado com três fallbacks
  - `Cameras.tsx:485-491` | Critério: connectivity_status, online boolean, connectivity_age_seconds <= 120s | 🟢

- [ ] T-08 — Implementar React Query stack de Cameras
  - `Cameras.tsx:401-562` | Critério: `onboardingNextStep`, `onboardingProgress`, `edgeStatus` (polling 20-30s), `cameras` (retry seletivo), `limits`, `mySupportRequests` | 🟢

- [ ] T-09 — Implementar fetch de câmeras em modo rede (selectedStore === "all")
  - `Cameras.tsx:441-460` | Critério: getCameras() global; fallback Promise.all por loja; resultado vazio seguro | 🟢

- [ ] T-10 — Implementar `canManageStore` e `canEditRoi` com support grant
  - `Cameras.tsx:397-593` | Critério: `hasActiveSupportGrant` estende canManageStore; is_staff/is_superuser permitem edição de ROI | 🟢

- [ ] T-11 — Implementar cache de ROI publicadas em localStorage
  - `Cameras.tsx:595-638` | Critério: lê ao trocar loja; `markLocalRoiPublished` adiciona e persiste; erros de localStorage silenciosos | 🟢

- [ ] T-12 — Implementar abertura automática de ROI via `?openRoi=1&zone_id=<id>`
  - `Cameras.tsx:641-656` | Critério: câmera com zone_id encontrada → setRoiCamera; não encontrada → toast.error; sem permissão → toast.error | 🟢

- [ ] T-13 — Implementar `resolveNextCreatePrefill` para criação sequencial via blueprint
  - `Cameras.tsx:674-700` | Critério: encontra próximo IP não usado; externalId `auto-<ip-com-hífens>`; connectionType: "nvr" | 🟢

- [ ] T-14 — Implementar mutação `createCameraMutation` com modo onboarding
  - `Cameras.tsx:702-738` | Critério: paywall → toast customizado com link billing; 400 → fieldMap com labels; modo onboarding → reabre modal para próximo IP | 🟢

- [ ] T-15 — Implementar mutação `requestSupportMutation`
  - `Cameras.tsx:658-672` | Critério: chama requestStoreSupport; toast.success com mensagem da resposta; invalida store-support-requests | 🟢

- [ ] T-16 — Implementar busca e display do blueprint local (ONVIF via 127.0.0.1:8787)
  - `Cameras.tsx:336-346` | Critério: GET /onboarding/blueprint → LocalOnboardingBlueprint; loading/error states; seleção de IPs respeita max_selectable | 🟡

- [ ] T-17 — Implementar LocalReadinessReport (GET /onboarding/readiness)
  - `Cameras.tsx:341-347` | Critério: checks exibidos; download de Markdown via `downloadTextFile + buildReadinessMarkdown` | 🟡

## Tarefas — Alertas

- [ ] T-18 — Implementar `normalizeArray<T>` (suporta array, {data:[]}, {results:[]})
  - `Alerts.tsx:67-78` | Critério: sem crash para null/undefined; compatível com os 3 formatos | 🟢

- [ ] T-19 — Implementar filtros de Alertas com sincronização por searchParams
  - `Alerts.tsx:88-144` | Critério: filtros inicializados de URL params; `startTransition` ao mudar URL | 🟢

- [ ] T-20 — Implementar SLA Timer dinâmico (setInterval 1s)
  - `Alerts.tsx:113-116,755-777` | Critério: countdown 30min; overdue com rose + animate-pulse; cleanup do interval | 🟢

- [ ] T-21 — Implementar fluxo de resolução tripartite
  - `Alerts.tsx:376-432` | Critério: razão obrigatória para delegado/técnico; resolve/ignore/delegate chamados corretamente; refetch após resolução | 🟢

- [ ] T-22 — Implementar `delegateToWhatsapp` (delegação por e-mail)
  - `Alerts.tsx:281-320` | Critério: `delegateEventEmail` → toast com nome ou genérico; erro de vínculo exibe mensagem de "vincule e-mail" | 🟢

- [ ] T-23 — Implementar `handleEscalateTechnical` com navigate para `/app/edge-help`
  - `Alerts.tsx:335-351` | Critério: params store_id, camera_id, event_id, source, reason corretos; trackJourneyEvent | 🟢

- [ ] T-24 — Implementar layout master-detail responsivo (inbox + drawer)
  - `Alerts.tsx:623-702` | Critério: coluna direita oculta sem seleção em mobile; drawer visível em desktop com 450/500px; `animate-in fade-in slide-in-from-right-4` | 🟢

- [ ] T-25 — Implementar simulação de evento (dev-only)
  - `Alerts.tsx:225-262` | Critério: visível apenas em `import.meta.env.DEV`; `receipt_id: "ui-dev-<timestamp>"`; abre drawer do evento criado | 🟢

## Tarefas — Regras de Alerta

- [ ] T-26 — Implementar `buildRuleQuality(rule, logs)`
  - `AlertRules.tsx:111-157` | Critério: score calculado corretamente; sem logs → base=60; sugestões corretas por threshold | 🟢

- [ ] T-27 — Implementar `parseRuleCreateError` com extração multi-campo
  - `AlertRules.tsx:57-109` | Critério: detalha campo a campo; hint de "Eventos válidos" quando hint detectado | 🟢

- [ ] T-28 — Implementar `qualityByRule` (Map<ruleId, RuleQualitySnapshot>) agrupando logs por rule_id
  - `AlertRules.tsx:233-246` | Critério: groupBy correto; regras sem logs recebem array vazio → score=60 | 🟢

- [ ] T-29 — Implementar `handleApplySuggestion` com tracking
  - `AlertRules.tsx:304-332` | Critério: apenas `increase_cooldown` implementado; toast de confirmação; trackJourneyEvent com old/new cooldown | 🟢

- [ ] T-30 — Implementar formulário de criação de regra com validação
  - `AlertRules.tsx:282-302` | Critério: storeId e type obrigatórios; channels pelo menos um; erro inline com parseRuleCreateError | 🟢

## Tarefas de Teste

- [ ] TT-01 — `diagnoseCameraFailure`: camera online → null; sem RTSP → "credencial"; edge offline → "heartbeat"
- [ ] TT-02 — `buildRuleQuality`: 0 logs → score=60, medio; alta supressão → baixo + suggestion; alta falha → review_channels
- [ ] TT-03 — `normalizeArray`: null → []; array → same; {data:[]} → []; {results:[]} → []
- [ ] TT-04 — `resolveNextCreatePrefill`: IP usado → pula para próximo; todos usados → retorna primeiro
- [ ] TT-05 — Fluxo de resolução: "delegado" sem motivo → toast.error; com motivo → delegate + ignore
- [ ] TT-06 — Cache ROI: loja A → ids corretos; trocar para loja B → limpa e recarrega loja B
- [ ] TT-07 — SLA Timer: evento de 29min → countdown verde; evento de 31min → overdue rose
- [ ] TT-08 — Paywall: code LIMIT_CAMERAS_REACHED → toast customizado com botão billing
- [ ] TT-09 — `isPrivateIp`: "10.0.0.1" → true; "192.168.1.1" → true; "8.8.8.8" → false; "localhost" → true
- [ ] TT-10 — Regra de alerta: `storeIdOverride=null` → usa primeira loja da lista

## Ordem Sugerida
1. T-01 a T-07 (utilitários e derivadores puros) — sem dependências
2. T-08, T-09 (React Query de câmeras) — depende de services
3. T-10 a T-13 (controle de acesso e cache) — depende de T-08
4. T-14 a T-17 (mutações e blueprint) — depende de T-08, T-13
5. T-18 a T-25 (Alertas) — independente de câmeras
6. T-26 a T-30 (Regras) — independente, pode ser paralelo a Alertas

## Lacunas Pendentes (🔴)
- `CameraRoiEditor` precisa ser lido antes de T-11 (integração de ROI)
- `camerasService` precisa ser lido antes de T-08, T-14 (campos exatos da Camera)
- `useAlertsEvents` e hooks precisam ser lidos antes de T-19, T-21
- Protocolo exato do setup API local (127.0.0.1:8787/onboarding/blueprint) precisa ser confirmado antes de T-16
