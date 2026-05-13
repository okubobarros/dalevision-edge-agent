# configurar-roi - Design

## Modelo

- 🟢 ROI é append-only por versão em `camera_roi_configs`.
- 🟢 `create_roi_config` calcula próxima versão com base no latest.
- 🟢 Published mais recente é identificado por `config_json.status="published"`.

## Workflow

- 🟢 Draft pode ser salvo sem geometria publicada.
- 🟢 Published exige geometria.
- 🟢 Depois da primeira published, próxima published exige validação da versão anterior.
- 🟢 Meta guarda rastreabilidade da alteração.

## Consumidores

- 🟢 Frontend usa `roi` para edição/histórico.
- 🟢 Edge/agente pode usar `roi/latest` para published.

## Rastreabilidade

- 🟢 `C:\workspace\dale-vision\apps\cameras\views.py`.
- 🟢 `C:\workspace\dale-vision\apps\cameras\roi.py`.
