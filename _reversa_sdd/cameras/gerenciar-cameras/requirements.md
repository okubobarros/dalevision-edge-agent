# gerenciar-cameras - Requirements

## Escopo

- 🟢 Caso de uso de CRUD de câmeras por usuários da loja.

## Requisitos

- 🟢 Listar câmeras por store com papel de leitura.
- 🟢 Criar câmera com papel de gestão.
- 🟢 Exigir `store_id`.
- 🟢 Validar entitlement/trial.
- 🟢 Aplicar limite por plano.
- 🟢 Atualizar câmera com papel de gestão.
- 🟢 Revalidar limite ao ativar câmera.
- 🟢 Remover câmera com papel de gestão.
- 🟢 Remover dados associados em cascata operacional controlada.
- 🟢 Não expor `password` e `rtsp_url` em resposta pública.

## Critérios de Aceitação

- 🟢 Usuário viewer consegue listar, mas não criar/editar/remover.
- 🟢 Manager consegue criar se plano permitir.
- 🟢 Store sem assinatura ativa recebe paywall.
- 🟢 Delete remove health, ROI, snapshots e câmera.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\serializers.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\limits.py`.
