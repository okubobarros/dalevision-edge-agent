# cameras - Tasks

- [ ] 🟢 Implementar CRUD com permissões por store.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: leitura e gestão respeitam roles `ALLOWED_READ_ROLES`/`ALLOWED_MANAGE_ROLES`.

- [ ] 🟢 Implementar serializer seguro.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\serializers.py`.
  - Critério de pronto: senha/RTSP são write-only e RTSP mascarado é exibido.

- [ ] 🟢 Implementar limite de câmeras por plano.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\limits.py`.
  - Critério de pronto: trial/start/pro bloqueiam acima do limite.

- [ ] 🟢 Implementar auditoria e journey events.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: create/update/delete/ROI e validações registram eventos quando aplicável.

- [ ] 🟢 Implementar ROI versionado.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\roi.py`, `views.py`.
  - Critério de pronto: GET/PUT funcionam com draft/validated/published/archived.

- [ ] 🟢 Implementar validação antes de republicar ROI.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: falta de calibration run aprovada retorna `ROI_VALIDATION_REQUIRED`.

- [ ] 🟢 Implementar health de câmera por usuário ou Edge Token.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: cria `CameraHealthLog` e atualiza campos da câmera.

- [ ] 🟢 Implementar teste RTSP com hard timeout.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\services.py`.
  - Critério de pronto: timeout retorna sem travar worker.

- [ ] 🟢 Implementar upload/consulta de snapshot backend.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: upload gera storage_key, signed URL e atualiza câmera.

- [ ] 🟢 Implementar upload de snapshot pelo edge.
  - Fonte: `C:\workspace\dale-vision\apps\edge\views_snapshot.py`.
  - Critério de pronto: Edge Token só atualiza câmera da mesma store.

- [ ] 🟡 Otimizar listagem de câmeras.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\serializers.py`.
  - Critério de pronto: evitar N+1 de health/latency em listas.

- [ ] 🟡 Remover ou isolar `test-snapshot` demo.
  - Fonte: `C:\workspace\dale-vision\apps\cameras\views.py`.
  - Critério de pronto: não persistir caminho local temporário em produção.
