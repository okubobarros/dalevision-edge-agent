# stores - Questions

## Lacunas

1. 🟡 `EdgeToken.token_plaintext` é persistido para permitir reexibir credenciais. Confirmar se isso é aceitável pelo modelo de segurança ou se deve migrar para exibição única.

2. 🟡 Existem múltiplos caminhos para obter token (`edge_token`, `edge_credentials`, `edge_setup`, activation token moderno). Confirmar qual é o caminho oficial para onboarding novo.

3. 🟡 `StoreEdgeAccessControlView` só suporta desabilitar edge. Confirmar fluxo operacional para reabilitar loja bloqueada.

4. 🟡 `StoreActivationStatusService` usa fallback `v1.0.22` quando não há release stable. Confirmar se esse fallback ainda é válido.

5. 🟡 Endpoint de câmeras para Edge Token retorna `password` e `rtsp_url` completos. Confirmar se frontend/logs nunca expõem essa resposta para usuário indevido.

6. 🟡 Canary batch usa `random.sample` sem seed/auditoria prévia. Confirmar se seleção aleatória sem preview atende ao processo operacional.
