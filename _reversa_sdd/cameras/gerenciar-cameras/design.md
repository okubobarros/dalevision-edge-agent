# gerenciar-cameras - Design

## Pipeline de Criação

1. 🟢 Resolver store por URL/body.
2. 🟢 Validar store existente.
3. 🟢 Exigir papel de gestão.
4. 🟢 Validar entitlement do produto.
5. 🟢 Validar serializer.
6. 🟢 Aplicar limite de câmeras.
7. 🟢 Salvar com timestamps.
8. 🟢 Auditar ação staff e registrar journey.

## Pipeline de Exclusão

- 🟢 Coleta storage keys.
- 🟢 Em transação, remove `CameraSnapshot`, `CameraHealth`, `CameraHealthLog`, `CameraROIConfig` e `Camera`.
- 🟢 Depois tenta remover arquivos no Supabase.
- 🟢 Falha de storage é logada sem desfazer exclusão do banco.

## Segurança

- 🟢 Serializer público usa write-only para RTSP/credenciais.
- 🟢 Logs sanitizam payload.
- 🟢 Permissões são baseadas em store/org.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
