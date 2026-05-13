# configurar-roi - Tasks

- [ ] 🟢 Implementar consultas latest/published/history.
  - Fonte: `roi.py`.
  - Critério de pronto: retorna versões corretas.

- [ ] 🟢 Implementar PUT ROI.
  - Fonte: `views.py`.
  - Critério de pronto: valida status, geometria e meta.

- [ ] 🟢 Implementar bloqueio por validação.
  - Fonte: `views.py`.
  - Critério de pronto: nova published exige calibration run aprovada.

- [ ] 🟢 Implementar endpoint ROI latest para edge.
  - Fonte: `views.py`.
  - Critério de pronto: usuário ou Edge Token podem ler published.

- [ ] 🟡 Criar contrato JSON formal para `zones` e `lines`.
  - Fonte: lacuna de schema.
  - Critério de pronto: validar coordenadas, tipos e IDs de ROI.
