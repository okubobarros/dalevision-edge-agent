# Accounts, Tasks

## Status da Unit

🟢 CONFIRMADO: A implementação principal de accounts existe no backend e frontend, com testes para login por identifier/email, Supabase provisioning, setup-state, me-status e admin control tower.

## Tarefas Funcionais Documentadas

| ID | Tarefa | Status | Evidência | Critério de Pronto | Confiança |
|----|--------|--------|-----------|--------------------|-----------|
| T-01 | Documentar endpoints de accounts e compat `/api/v1/accounts`. | [X] | `backend/urls.py`, `apps/accounts/urls.py` | Rotas listadas em requirements/design. | 🟢 |
| T-02 | Documentar login/register Knox legado. | [X] | `serializers.py`, `views.py` | Regras de username/email/senha/token descritas. | 🟢 |
| T-03 | Documentar autenticação Supabase JWT. | [X] | `auth_supabase.py` | Config, cache, timeout e erros descritos. | 🟢 |
| T-04 | Documentar provisionamento de usuário Supabase. | [X] | `provision_user_from_supabase_info()` | Criação/update User e user_id_map descritos. | 🟢 |
| T-05 | Documentar membership e criação de org trial. | [X] | `ensure_org_membership()` | Criação/recovery/fallback descritos. | 🟢 |
| T-06 | Documentar `/accounts/me`. | [X] | `MeView` | Retorno user/orgs descrito. | 🟢 |
| T-07 | Documentar `/v1/me/status`. | [X] | `MeStatusView` | Trial/subscription/admin descritos. | 🟢 |
| T-08 | Documentar `/me/setup-state`. | [X] | `SetupStateView` | Auth manual e estados descritos. | 🟢 |
| T-09 | Documentar `/v1/me/data-maturity`. | [X] | `MeDataMaturityView` | Níveis M0..M3 descritos. | 🟢 |
| T-10 | Documentar admin control tower. | [X] | `AdminControlTowerSummaryView`, `AdminControlTowerDrilldownView` | Permissão e métricas descritas. | 🟢 |
| T-11 | Documentar sessão frontend Supabase. | [X] | `auth.ts`, `authSession.ts`, `authStorage.ts`, `AuthContext.tsx` | Login/bootstrap/logout/storage descritos. | 🟢 |
| T-12 | Documentar rotas protegidas frontend. | [X] | `PrivateRoute.tsx`, `App.tsx` | `/app/*` protegido e `/onboarding` público registrado. | 🟢 |
| T-13 | Documentar callback e recovery de senha. | [X] | `AuthCallback`, `ForgotPassword`, `ResetPassword` | Confirmação/reenvio/reset descritos. | 🟢 |

## Tarefas de Correção Recomendadas

| ID | Tarefa | Status | Justificativa | Prioridade |
|----|--------|--------|---------------|------------|
| V-01 | Importar `settings` em `apps/accounts/views.py` ou remover uso de `settings.DEBUG`. | [ ] | Branch de database error do Supabase bootstrap pode lançar `NameError`. | Must |
| V-02 | Decidir e documentar status oficial de Knox endpoints. | [ ] | Dois tokens ativos aumentam superfície de suporte e segurança. | Should |
| V-03 | Proteger `/onboarding` no frontend ou documentar por que é público. | [ ] | Router marca "público por enquanto"; APIs internas podem bloquear, mas UI fica exposta. | Should |
| V-04 | Adicionar teste para `SupabaseBootstrapView` com `DatabaseError`. | [ ] | Cobrir lacuna de `settings.DEBUG` e formato de erro. | Must |
| V-05 | Adicionar teste de `SetupStateView` usando Knox fallback. | [ ] | Fluxo existe, mas testes atuais focam missing auth e Supabase mockado. | Should |
| V-06 | Avaliar armazenamento de JWT em `localStorage` contra alternativa httpOnly/session. | [ ] | Reduz impacto de XSS. | Should |
| V-07 | Criar job de limpeza/relatório de orgs trial sem store após período definido. | [ ] | Provisionamento automático pode gerar dados órfãos. | Could |
| V-08 | Padronizar envelope de erro entre Supabase bootstrap, auth class e setup-state. | [ ] | Facilita suporte e frontend. | Should |

## Testes Existentes

| Teste | Cobertura | Confiança |
|-------|-----------|-----------|
| `LoginIdentifierTests::test_login_with_username_ok` | Login Knox por username. | 🟢 |
| `LoginIdentifierTests::test_login_with_email_ok` | Login Knox por email. | 🟢 |
| `LoginIdentifierTests::test_login_invalid_email_same_error_as_wrong_password` | Anti-enumeração de login. | 🟢 |
| `SupabaseProvisionTests::test_upsert_user_id_map_creates_uuid_mapping` | Mapeamento user UUID. | 🟢 |
| `SupabaseProvisionTests::test_provision_creates_user_and_user_id_map` | Provisionamento idempotente Supabase. | 🟢 |
| `SupabaseProvisionTests::test_provision_reuses_existing_user_after_integrity_race` | Race de criação de usuário. | 🟢 |
| `SupabaseAuthFailureTests::test_auth_missing_config_returns_authentication_failed` | Config ausente no auth Supabase. | 🟢 |
| `SetupStateUnauthenticatedTests` | 401 JSON sem auth. | 🟢 |
| `SetupStateProvisioningTests` | Supabase auth mockado e estado no_store. | 🟢 |
| `MeStatusViewTests` | Trial flags e bypass admin interno. | 🟢 |
| `AdminControlTowerSummaryViewTests` | Permissão e payload staff. | 🟢 |
| `AdminControlTowerDrilldownViewTests` | Permissão, métrica válida e métrica inválida. | 🟢 |
| `AuthContext.test.tsx` | Rehydrate e Authorization header no frontend. | 🟢 |
| `Login.test.tsx`, `ForgotPassword.test.tsx` | Fluxos visuais de login/recovery. | 🟢 |

## Checklist de Reimplementação

- [ ] Preservar `SupabaseJWTAuthentication` como primeira auth class DRF.
- [ ] Preservar Knox token enquanto endpoints legados existirem.
- [ ] Preservar `user_id_map` como ponte entre Django user e UUID Supabase/OrgMember.
- [ ] Preservar criação automática de org/membership para usuário novo.
- [ ] Preservar recovery por `stores.owner_email`.
- [ ] Preservar setup-state `no_store`/`ready`.
- [ ] Preservar bypass de trial para staff/superuser/allowlist.
- [ ] Preservar anti-enumeração de login e forgot password.
- [ ] Preservar header `Authorization: Bearer` no frontend.
- [ ] Preservar decisão pós-login admin/dashboard/onboarding.

## Ordem Recomendada de Migração

1. Escrever testes de contrato para `/accounts/supabase`, `/accounts/me`, `/me/setup-state`, `/v1/me/status`.
2. Corrigir lacuna de import `settings` (TAS-01).
3. Separar autenticação Supabase e provisionamento em serviços menores.
4. Formalizar status de Knox e plano de depreciação se aplicável.
5. Revisar proteção de `/onboarding`.
6. Avaliar estratégia de armazenamento de token frontend.

## Tarefas Estratégicas (0 a 10 Users)

- [ ] TAS-01 — Corrigir import de `settings` em `SupabaseBootstrapView`
  - Origem no legado: Validação de estabilidade da API.
  - Critério de pronto: Importar `django.conf.settings`; Erro 500 em falhas de banco convertido em resposta elegante.
  - Confiança: 🟢

## Lacunas Pendentes
- Nenhuma lacuna 🔴 remanescente. Todas as decisões estratégicas foram validadas.
