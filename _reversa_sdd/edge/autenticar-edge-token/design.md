# autenticar-edge-token - Design

## Sequência

1. 🟢 `_extract_store_token` lê headers/query/Authorization.
2. 🟢 Se token ausente, retorna `EdgeTokenAuthResult(ok=False, status_code=401)`.
3. 🟢 Calcula `hashlib.sha256(token).hexdigest()`.
4. 🟢 Busca `EdgeToken.objects.filter(token_hash=..., active=True).first()`.
5. 🟢 Se não encontrou e não parece JWT de usuário, loga warning com `_mask_token`.
6. 🟢 Se `requested_store_id` diverge, retorna `403`.
7. 🟢 Busca store e chama `_store_edge_access_error`.
8. 🟢 Se store bloqueada, retorna `403`.
9. 🟢 Atualiza `last_used_at`.
10. 🟢 Anexa store ao request.

## Máscara de Token

- 🟢 `_mask_token` retorna `absent` para token vazio.
- 🟢 Para token presente, retorna prefixo `sha256:` com os 12 primeiros caracteres do digest.

## EdgeAwareJWTAuthentication

- 🟢 Se `X-EDGE-TOKEN` existe, retorna `None` para deixar validação edge vencer.
- 🟢 Só tenta Supabase JWT quando Authorization é Bearer e contém formato JWT com ao menos dois pontos.

## Riscos

- 🟡 Query param `edge_token` é compatível, mas expõe token em URL/logs de infraestrutura se usado fora de ambiente controlado.
- 🟡 `token_plaintext` existe no modelo; garantir que não seja usado em logs ou respostas.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\edge\auth.py`.
