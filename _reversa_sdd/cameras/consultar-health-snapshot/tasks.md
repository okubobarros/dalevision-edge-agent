# consultar-health-snapshot - Tasks

- [ ] 🟢 Implementar POST health.
  - Fonte: `views.py`.
  - Critério de pronto: usuário/edge autenticado atualiza câmera e log.

- [ ] 🟢 Implementar probe RTSP.
  - Fonte: `services.py`.
  - Critério de pronto: OpenCV/TCP fallback e hard timeout funcionam.

- [ ] 🟢 Implementar test_connection.
  - Fonte: `views.py`.
  - Critério de pronto: sucesso/falha atualizam câmera e health log.

- [ ] 🟢 Implementar snapshot upload backend.
  - Fonte: `views.py`.
  - Critério de pronto: Supabase recebe arquivo, catálogo é criado e signed URL retornada.

- [ ] 🟢 Implementar snapshot GET.
  - Fonte: `views.py`.
  - Critério de pronto: retorna signed URL ou fallback/erro.

- [ ] 🟢 Implementar snapshot edge.
  - Fonte: `apps\edge\views_snapshot.py`.
  - Critério de pronto: Edge Token só altera câmera da própria store.

- [ ] 🟡 Unificar política signed/public URL.
  - Fonte: diferença entre `views.py` e `views_snapshot.py`.
  - Critério de pronto: snapshots têm regra única de exposição.
