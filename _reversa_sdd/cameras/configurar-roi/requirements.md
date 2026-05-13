# configurar-roi - Requirements

## Escopo

- 🟢 Caso de uso de configuração e publicação de ROI por câmera.

## Requisitos

- 🟢 GET deve retornar ROI latest, active/published e history.
- 🟢 PUT deve aceitar dict ou lista em `config_json`.
- 🟢 Status deve ser `draft`, `validated`, `published` ou `archived`.
- 🟢 Published deve conter ao menos uma zona ou linha.
- 🟢 Nova publicação após versão publicada deve exigir validação aprovada/validated da versão anterior.
- 🟢 Deve versionar automaticamente.
- 🟢 Deve gravar meta com workflow state, autor, mudança, snapshot e timestamp.
- 🟢 Staff deve registrar marcação em meta.
- 🟢 Publicação deve completar onboarding `roi_published`.
- 🟢 `roi/latest` deve retornar apenas published e aceitar Edge Token.

## Critérios de Aceitação

- 🟢 Sem ROI, GET retorna versão 0.
- 🟢 Publicar sem geometria retorna 400.
- 🟢 Publicar nova versão sem validação retorna 409.
- 🟢 ROI latest com Edge Token inválido retorna 401.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\roi.py`.
