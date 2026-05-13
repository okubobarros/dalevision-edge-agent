# frontend-auth-onboarding

## Visão Geral
Módulo responsável por todo o ciclo de entrada e integração do usuário à plataforma DaleVision: registro via Supabase Auth, login via Knox/Django, recuperação de senha, callback OAuth, onboarding guiado (loja + equipe + LGPD) e roteamento pós-login. É o portão de acesso a toda a área protegida `/app`.

## Responsabilidades
- Registro de novo usuário via Supabase Auth (e-mail + senha + metadados de empresa)
- Login com credenciais (username/password) via Knox token no backend Django
- Gerenciamento de sessão no lado cliente (AuthContext + localStorage/sessionStorage)
- Recuperação e redefinição de senha (Supabase)
- Callback OAuth (`/auth/callback`) com resolução de rota pós-login
- Onboarding multi-step: criação de loja, cadastro de equipe, aceite LGPD
- Roteamento inteligente pós-login (`resolvePostLoginDecision`)
- Guarda de rota (`PrivateRoute`) para área protegida

## Regras de Negócio
- Email deve ser único no Supabase; em caso de duplicidade, Supabase retorna erro na camada de signUp 🟢
- Senha mínima de 8 caracteres no registro; validação client-side antes do envio 🟢 (`Register.tsx:32`)
- Após registro bem-sucedido, e-mail de confirmação é enviado antes de qualquer login 🟢 (`Register.tsx:87`)
- Login usa `username` (e-mail) + senha via `authService.login()` → Knox token; não usa sessão Supabase para login 🟢 (`AuthContext.tsx:52`)
- Token Knox salvo em localStorage; `AuthContext` re-hidrata via `authService.bootstrapSession()` no mount 🟢 (`AuthContext.tsx:23`)
- `subscribeAuthChanges` sincroniza estado de auth entre abas via storage event 🟢 (`AuthContext.tsx:110`)
- Rota pós-login é resolvida por `resolvePostLoginDecision()`: se usuário não tem loja → `/onboarding`; se tem → `/app/dashboard` 🟡 (inferido de `Onboarding.tsx:146`)
- Onboarding tem 3 steps: (1) Criar loja, (2) Cadastrar equipe/indicadores, (3) Aceite LGPD 🟢 (`Onboarding.tsx:33`)
- Step 2 (equipe) pode ser pulado (lista vazia permitida); Step 3 (LGPD) exige aceite dos dois campos obrigatórios (`legalBasisAck` e `operatorRoleAck`) 🟢 (`Onboarding.tsx:419`)
- Estado parcial do onboarding é persistido em `sessionStorage` key `dv_onboarding_state` para sobreviver reload 🟢 (`Onboarding.tsx:88`)
- Sessão inconsistente (step > 1 sem storeId) limpa estado e volta ao step 1 🟢 (`Onboarding.tsx:65`)
- Se usuário já tem loja ao entrar em `/onboarding` sem sessão ativa, redireciona para `/app/dashboard?openEdgeSetup=1` 🟢 (`Onboarding.tsx:146`)
- Cooldown de 5 segundos após submissão no Register para evitar re-envio acidental 🟢 (`Register.tsx:56`)
- Throttling do Supabase Auth (429) tratado com mensagem amigável 🟢 (`Register.tsx:77`)
- E-mail do último login é salvo em `dv_last_auth_email` no localStorage 🟢 (`Login.tsx:50`)
- `PostLoginExplainer` é exibido no onboarding com base em flag persistida 🟡
- Ao concluir LGPD, navega para `/app/dashboard?openEdgeSetup=1&store_id=<id>` e limpa session 🟢 (`Onboarding.tsx:455`)
- Custo médio/hora (`avgHourlyLaborCost`) é obrigatório no step 2; campo vazio ou não numérico bloqueia avanço 🟢 (`Onboarding.tsx:316`)
- Deduplicação de funcionários por fingerprint `nome|email|whatsapp` antes de enviar; segunda tentativa automática para registros faltantes 🟢 (`Onboarding.tsx:338`)
- Baseline comercial (ticket médio × vendas/dia = receita estimada/dia e mês) é calculado no frontend e persistido no `StoreProfile.defaults` via `copilotService` 🟢 (`Onboarding.tsx:191`)

## Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de Aceite |
|----|-----------|------------|-------------------|
| RF-01 | Registro de novo usuário (nome, e-mail, empresa, senha ≥ 8 chars) via Supabase Auth | Must | Usuário recebe e-mail de confirmação; formulário bloqueia campos inválidos antes do envio |
| RF-02 | Login com e-mail/senha via Knox token; sessão persistida em localStorage | Must | Token Knox salvo; AuthContext popula `user` e `isAuthenticated=true` |
| RF-03 | Bootstrap de sessão ao carregar a app (rehydrate de localStorage) | Must | Usuário com token válido não é redirecionado para login ao reabrir a aba |
| RF-04 | Sincronização de estado de auth entre abas via storage event | Should | Logout em uma aba desloga as demais em ≤ 1s |
| RF-05 | Recuperação de senha via link enviado por Supabase | Must | Usuário recebe e-mail com link funcional de reset |
| RF-06 | Callback OAuth `/auth/callback` resolve rota pós-login correta | Must | Após confirmar e-mail, usuário é direcionado ao onboarding ou dashboard |
| RF-07 | Guarda de rota `PrivateRoute` bloqueia `/app` sem autenticação | Must | Usuário não autenticado é redirecionado para `/login` |
| RF-08 | Onboarding step 1: criar loja com nome, cidade, estado e indicadores comerciais | Must | Loja criada no backend com ID retornado; baseline comercial persistido no StoreProfile |
| RF-09 | Onboarding step 2: cadastrar equipe (opcional) e custo médio/hora (obrigatório) | Must | Funcionários persistidos; custo médio/hora salvo em `Store.avg_hourly_labor_cost` |
| RF-10 | Onboarding step 3: aceite LGPD com 2 campos obrigatórios e 1 opcional | Must | Aceite registrado via `onboardingService.registerLgpdAcceptance`; navega para dashboard |
| RF-11 | Persistência parcial do onboarding em sessionStorage | Should | Reload na metade do onboarding retoma do step correto |
| RF-12 | Redirecionamento para dashboard se usuário já tem loja ao iniciar onboarding | Must | Usuário com loja existente não fica preso no onboarding |
| RF-13 | Reenvio de e-mail de confirmação via botão na tela de login | Could | Supabase reenvio acionado; feedback de sucesso ou erro exibido |
| RF-14 | Cooldown de 5s no botão de registro para evitar duplo envio | Should | Botão desabilitado por 5s após click; estado visual bloqueado |
| RF-15 | Tratamento de throttling Supabase (429) com mensagem amigável | Should | Mensagem "Muitos envios recentes" exibida sem stack trace |
| RF-16 | Deduplicação de funcionários por fingerprint antes do envio | Should | Funcionários duplicados não geram erro 400 de unique constraint |

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
|------|--------------------|---------------------|-----------| 
| Segurança | Token Knox nunca exposto em URL; senha nunca logada | `AuthContext.tsx:63` (catch sem logar senha) | 🟢 |
| Segurança | Campo senha com toggle show/hide; autocomplete `new-password` / `current-password` | `Login.tsx:204`, `Register.tsx:213` | 🟢 |
| Disponibilidade | Supabase resend com retry manual; throttling tratado | `Login.tsx:94` | 🟢 |
| Performance | Lazy loading de todas as páginas via `React.lazy` + `Suspense` | `App.tsx:1-38` | 🟢 |
| Usabilidade | Scroll to top automático na troca de step do onboarding | `Onboarding.tsx:92` | 🟢 |
| Confiabilidade | Estado de onboarding persistido em sessionStorage; limpeza após conclusão | `Onboarding.tsx:453` | 🟢 |

> Inferido a partir do código. Validar com equipe de operações.

## Critérios de Aceitação

```gherkin
# RF-02 — Login happy path
Dado que o usuário existe no sistema com Knox token válido
Quando ele preenche e-mail e senha corretos e clica em "Entrar"
Então AuthContext.user é populado, token salvo em localStorage e navegação ocorre para rota resolvida por resolvePostLoginDecision

# RF-02 — Login falha
Dado que o usuário informa senha errada
Quando o formulário é submetido
Então mensagem de erro do backend (detail ou non_field_errors) é exibida; sem redirecionamento

# RF-01 — Registro happy path
Dado que o usuário preenche nome, e-mail válido, empresa e senha ≥ 8 chars
Quando clica em "Criar Conta"
Então Supabase.auth.signUp é chamado; estado `success=true`; mensagem de e-mail enviado é exibida

# RF-01 — Registro com e-mail inválido
Dado que o usuário informa e-mail sem @
Quando tenta submeter o formulário
Então botão permanece desabilitado (canSubmit=false); mensagem inline de validação exibida

# RF-10 — LGPD obrigatório
Dado que o usuário está no step 3 do onboarding
Quando clica "Avançar" sem marcar legalBasisAccepted ou operatorRoleAccepted
Então setLgpdError("Confirme os aceites obrigatórios para continuar.") é exibido; sem avanço

# RF-12 — Redirecionamento se loja existe
Dado que o usuário autenticado entra em /onboarding sem sessão ativa de onboarding
E já possui uma loja cadastrada no backend
Quando o componente monta
Então navega para /app/dashboard?openEdgeSetup=1&store_id=<id>
```

## Prioridade (MoSCoW)

| Requisito | MoSCoW | Justificativa |
|-----------|--------|---------------|
| Login + sessão Knox (RF-02, RF-03) | Must | Portão de entrada a toda a plataforma |
| PrivateRoute (RF-07) | Must | Segurança de acesso |
| Onboarding loja (RF-08) | Must | Sem loja, nenhuma feature funciona |
| LGPD (RF-10) | Must | Obrigação legal; bloqueia conclusão do onboarding |
| Registro (RF-01) | Must | Aquisição de novos usuários |
| Callback OAuth (RF-06) | Must | Necessário para confirmar e-mail Supabase |
| Persistência onboarding (RF-11) | Should | UX de continuidade |
| Sync entre abas (RF-04) | Should | Segurança multi-tab |
| Cooldown / throttling (RF-14, RF-15) | Should | Evita abuso do Supabase |
| Deduplicação funcionários (RF-16) | Should | Robustez de dados |
| Reenvio e-mail confirmação (RF-13) | Could | Raramente acionado |

> Prioridade inferida por frequência de chamada e posição na cadeia de dependências.

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
|---------|-----------------|-----------| 
| `frontend/src/contexts/AuthContext.tsx` | `AuthProvider` | 🟢 |
| `frontend/src/services/auth.ts` | `authService.login`, `bootstrapSession`, `rehydrate` | 🟢 |
| `frontend/src/services/authStorage.ts` | `subscribeAuthChanges` | 🟢 |
| `frontend/src/pages/Login/Login.tsx` | `Login`, `handleSubmit`, `handleResend` | 🟢 |
| `frontend/src/pages/Register/Register.tsx` | `Register`, `handleSubmit` | 🟢 |
| `frontend/src/pages/Onboarding/Onboarding.tsx` | `Onboarding`, `handleCreateStore`, `handleEmployeesNext`, `handleLgpdNext` | 🟢 |
| `frontend/src/pages/AuthCallback/AuthCallback.tsx` | `AuthCallback` | 🟡 (não lido diretamente) |
| `frontend/src/components/PrivateRoute.tsx` | `PrivateRoute` | 🟢 |
| `frontend/src/services/postLoginRoute.ts` | `resolvePostLoginDecision`, `persistPostLoginExplainer` | 🟡 |
| `frontend/src/services/onboarding.ts` | `onboardingService.registerLgpdAcceptance` | 🟡 |
| `frontend/src/services/journey.ts` | `trackJourneyEvent` | 🟡 |
| `frontend/src/App.tsx` | Roteamento, lazy loading, `LegacyStoreRedirect` | 🟢 |
