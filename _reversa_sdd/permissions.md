# Permissoes e RBAC - DaleVision

Gerado em: 2026-05-06T20:09:09.572994Z

## Papeis

- internal_admin: Django is_staff ou is_superuser.
- owner/admin/manager/viewer: roles de OrgMember.
- support_grant: acesso temporario por SupportAccessGrant; viewer com grant ativo e tratado como manager para loja.
- edge_device: agente autenticado por Edge Token, escopado a uma store.
- anonymous: permitido em endpoints publicos especificos como health, login/register, demo lead, activate device, signed download e edge release latest.

## Matriz de permissoes

| Area | Anonymous | Edge device | Viewer | Manager | Admin | Owner | Internal admin |
|---|---:|---:|---:|---:|---:|---:|---:|
| Login/register/bootstrap publico | Sim | N/A | N/A | N/A | N/A | N/A | Sim |
| Ver dados da propria loja | Nao | Nao | Sim | Sim | Sim | Sim | Sim |
| Gerenciar cameras/ROI | Nao | Nao | Nao | Sim | Sim | Sim | Sim |
| Enviar camera health/eventos edge | Nao | Sim, somente store do token | Nao | Nao | Nao | Nao | N/A |
| Buscar cameras para edge | Nao | Sim, somente store do token | Nao | Nao | Nao | Nao | N/A |
| Emitir activation token | Nao | Nao | Nao | Sim | Sim | Sim | Sim |
| Baixar instalador assinado | Link assinado publico temporario | N/A | Sim para gerar link | Sim | Sim | Sim | Sim |
| Revogar device edge | Nao | Nao | Nao | Sim | Sim | Sim | Sim |
| Desabilitar edge da loja | Nao | Nao | Nao | Sim | Sim | Sim | Sim |
| Admin analytics/control tower | Nao | Nao | Nao | Nao | Nao | Nao | Sim |
| Gerenciar releases edge | Nao | Nao | Nao | Nao | Nao | Nao | Sim |
| Bypass trial/paywall | Nao | Whitelist /api/edge | Nao | Nao | Nao | Nao | Sim |
| Suporte temporario | Nao | Nao | Via grant ativo vira manager | Via grant | Via grant | Via grant | Sim |

## Regras de acesso confirmadas

1. 🟢 CONFIRMADO - require_store_role aceita ALLOWED_READ_ROLES owner/admin/manager/viewer e ALLOWED_MANAGE_ROLES owner/admin/manager.
2. 🟢 CONFIRMADO - is_staff/is_superuser bypassam require_store_role e TrialEnforcementMiddleware.
3. 🟢 CONFIRMADO - Edge token e validado por hash e escopo de store; mismatch retorna 403 edge_store_mismatch.
4. 🟢 CONFIRMADO - Store bloqueada por edge_disabled/subscription_inactive/store_suspended/security_revoked impede auth edge.
5. 🟢 CONFIRMADO - Trial expirado bloqueia endpoints /api com HTTP 402, exceto whitelist incluindo /api/edge.
6. 🟢 CONFIRMADO - StoreDownloadAgentFileView e publico, mas exige token assinado com TTL.
7. 🟢 CONFIRMADO - EdgeReleaseLatestView e publico para facilitar instalador/onboarding.
8. 🟡 INFERIDO - SupportAccessGrant foi desenhado para suporte remoto operacional, nao para administracao comercial permanente.

## Riscos de permissao

- 🔴 LACUNA - A matriz completa por endpoint deve ser validada contra todos ViewSets e decorators, principalmente stores/views.py por ser extenso.
- 🟡 INFERIDO - Alguns endpoints AllowAny dependem de validacoes internas; testes de abuso devem cobrir token ausente, token de outra loja e link expirado.
