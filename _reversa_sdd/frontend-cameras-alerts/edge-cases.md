# frontend-cameras-alerts — Casos de Borda

## CE-01 — Diagnóstico de câmera: online, mas com erro no `camera_health`

**Contexto:** Camera com `camera_health.status = "online"` mas `camera_health.error` preenchido

**Comportamento:**
```
diagnoseCameraFailure:
  statusValue = "online" → return null
```

**Resultado:** diagnóstico retorna null — câmera tratada como saudável mesmo com error preenchido 🟡

**Risco:** Câmera degradada com erro documentado mas não diagnosticado; usuário não recebe orientação de ação

---

## CE-02 — Câmeras em modo rede: getCameras() retorna vazio mas stores tem lojas

**Contexto:** API global de câmeras retorna `[]` (ex.: sem permissão de rede)

**Comportamento:**
```
if (allCameras.length > 0) return allCameras
// vazio → fallback:
if (stores.length > 0):
  Promise.all(stores.map(s => getStoreCameras(s.id).catch(() => [])))
  return results.flat()
```

**Resultado:** fallback por loja garante que câmeras sejam exibidas 🟢

---

## CE-03 — ROI: `initialZoneId` definido mas câmeras ainda não carregadas

**Contexto:** URL `?openRoi=1&zone_id=abc` → cameras ainda `undefined` ou `[]` no primeiro render

**Comportamento:**
```
useEffect:
  if (!cameras || cameras.length === 0) return  // aguarda
  // executa quando cameras chega
  cameraMatch = cameras.find(c => c.zone_id === initialZoneId)
  zoneOpenHandled.current = true  // marca como tratado
```

**Resultado:** aguarda cameras carregar antes de tentar abrir ROI 🟢

**Risco:** 🟡 Se a câmera nunca chegar (erro de fetch), ROI nunca abre — sem feedback visual de "aguardando câmeras"

---

## CE-04 — Criação via blueprint: todos os IPs selecionados já têm câmera criada

**Contexto:** Usuário seleciona 3 IPs, cria 3 câmeras; tenta criar uma 4ª via blueprint

**Comportamento:**
```
resolveNextCreatePrefill:
  nextIp = selectedIps.find(ip => !usedIps.has(ip))  → undefined
  nextIp = nextIp || selectedIps[0]  // fallback para primeiro IP
  return { ip: selectedIps[0], ... }  // retorna mesmo com IP já usado
```

**Risco:** 🟡 Fallback retorna primeiro IP mesmo que já exista câmera com aquele IP — pode gerar erro 409 na criação

---

## CE-05 — Câmera com `rtsp_url_masked` vazia vs. diagnóstico de credencial

**Contexto:** Câmera cadastrada sem RTSP URL definida

**Comportamento:**
```
rtspMissing = !(camera.rtsp_url_masked || "").trim()  // true
→ diagnose: "credencial" com ação "Revisar usuário, senha e RTSP"
```

**Resultado:** câmera sem RTSP diagnosticada como "credencial" — instrução clara 🟢

---

## CE-06 — Support Grant expirado: `canManageStore` erroneamente true

**Contexto:** `latestSupportRequest.expires_at` é data inválida (NaN)

**Comportamento:**
```
hasActiveSupportGrant:
  expiresAt = new Date(invalid) → NaN
  Number.isNaN(expiresAt.getTime()) → true
  return false
```

**Resultado:** NaN tratado corretamente → grant não concedido 🟢

---

## CE-07 — LocalBlueprint: Setup API local offline (127.0.0.1:8787 inacessível)

**Contexto:** Edge Agent não está rodando ou firewall bloqueia porta 8787

**Comportamento:**
- `localBlueprintLoading = true` → fetch timeout → `localBlueprintError = mensagem de erro`
- UI exibe estado de erro com botão de retry

**Risco:** 🟡 `EDGE_SETUP_LOCAL_BASE_URL = "http://127.0.0.1:8787"` hardcoded — se porta mudar, sem fallback

---

## CE-08 — Alertas: `occurred_at` ausente no SLA Timer

**Contexto:** Alerta sem `occurred_at` preenchido

**Comportamento:**
```
const occurred = new Date(selectedEvent.occurred_at || selectedEvent.created_at || now)
// fallback para now → targetTime = now + 30min → sempre positivo
```

**Resultado:** sem crash — usa `now` como fallback, SLA começa do presente 🟢

**Risco:** 🟡 Comportamento confuso: alerta antigo sem `occurred_at` parece ter 30min de SLA restantes

---

## CE-09 — Delegação de alerta: funcionário sem e-mail ou telefone vinculado

**Contexto:** `delegateEventEmail` falha porque funcionário não tem canal de contato

**Comportamento:**
```
catch:
  payload.employee_phone → string com mensagem
  → toast.error("Delegação indisponível: vincule um e-mail ou telefone ao colaborador na aba 'Equipe & Alçadas' dos detalhes da loja.")
```

**Resultado:** erro com instrução de ação corretiva 🟢

---

## CE-10 — Filtro de data em Alertas: `dateFrom` e `dateTo` iguais (mesma data)

**Contexto:** Usuário quer ver alertas de hoje apenas

**Comportamento:**
```
occurredFrom = new Date("2026-05-07T00:00:00").toISOString()  // início do dia local
occurredTo   = new Date("2026-05-07T23:59:59").toISOString()  // fim do dia local
```

**Risco:** 🟡 Usa `new Date("YYYY-MM-DDT00:00:00")` sem especificar timezone — interpreta no fuso local do browser; pode diferir do servidor

---

## CE-11 — Qualidade de regra: 0 logs (regra nova)

**Contexto:** Regra criada há menos de 1 dia sem nenhum evento ainda

**Comportamento:**
```
buildRuleQuality(rule, []):
  totalLogs = 0
  suppressionRate = 0 / 0 = 0 (guarda: 0 se sem logs)
  failureRate = 0
  base = totalLogs === 0 ? 60 : 100  → 60
  score = clamp(60 - 0 - 0, 0, 100) = 60
  level = score >= 55 → "medio"
  suggestion = null (totalLogs < 6)
```

**Resultado:** regra nova recebe score 60, "medio", sem sugestão — comportamento intencional 🟢

---

## CE-12 — Aplicar sugestão de cooldown: `type !== "increase_cooldown"`

**Contexto:** Sugestão é "review_channels"; usuário não pode clicar (não há botão de aplicação)

**Comportamento:**
```
handleApplySuggestion:
  if (suggestion.type !== "increase_cooldown") return
  // sem efeito silencioso
```

**Resultado:** apenas `increase_cooldown` tem aplicação automática; `review_channels` exige ação manual via link 🟢

---

## CE-13 — Resolução de alerta: `resolutionTarget.id` ausente

**Contexto:** Objeto de alerta sem `id` (resposta de backend malformada)

**Comportamento:**
```
handleSubmitResolution:
  if (!resolutionTarget?.id) return  // retorna silenciosamente
```

**Risco:** 🟡 Sem feedback visual para o usuário — botão some sem explicação se `id` for undefined

---

## CE-14 — Câmeras: localStorage corrompido para cache de ROI

**Contexto:** localStorage tem JSON inválido para chave de ROI publicadas

**Comportamento:**
```
useEffect:
  JSON.parse(raw) → lança exceção
  catch → setLocalPublishedRoiCameraIds(new Set())
```

**Resultado:** falha silenciosa, cache resetado 🟢

---

## CE-15 — Alerta com `storeId` mas loja não encontrada em `storesMap`

**Contexto:** Alerta de loja deletada ou sem acesso do usuário

**Comportamento:**
```
storesMap.get(String(e.store_id)) → undefined
storeName = undefined || "Loja"  // fallback
```

**Resultado:** exibe "Loja" como nome — sem crash 🟢

---

## CE-16 — `trackedSuggestionKeysRef` em AlertRules: sugestão re-exibida após re-mount

**Contexto:** Usuário navega para outra página e volta; qualidade re-calculada com a mesma sugestão

**Comportamento:**
```
trackedSuggestionKeysRef.current = new Set()  // criado no mount
// keys já rastreadas são perdidas
// trackJourneyEvent("alert_rule_suggestion_shown") dispara novamente
```

**Risco:** 🟡 Analytics duplicado por re-mount — `trackedSuggestionKeysRef` é local e não persiste entre renders
