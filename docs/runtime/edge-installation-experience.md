# Edge Installation Experience (Frictionless)

## Comportamento esperado
- Ao iniciar: mensagem "DaleVision Agent iniciado" + "Conectando...".
- Em sucesso: "Conectado com sucesso. Volte ao app para continuar".
- Em erro: mensagem clara + retry automático com backoff; log detalhado.
- Não abrir navegador automaticamente; usuário volta ao app por conta própria.

## Estados
- Starting → Connecting → Connected | Error (retrying).
- Heartbeat envia `{store_id, edge_version, status:"online", timestamp}` para destravar onboarding.

## Mensagens
- Start: "DaleVision Agent iniciado"
- Progress: "Conectando..."
- Sucesso: "Conectado com sucesso. Volte ao app para continuar"
- Erro: incluir causa (HTTP/timeout) + instrução de retry automático.

## Fallback
- Retry automático de heartbeat com backoff.
- Log visível em console e arquivo.
- Se falhar autostart, registrar erro no log de instalação.
