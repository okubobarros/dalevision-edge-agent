# gerenciar-cameras - Tasks

- [ ] 🟢 Implementar queryset filtrado por usuário.
  - Fonte: `permissions.py`, `views.py`.
  - Critério de pronto: usuário só vê câmeras de org permitida.

- [ ] 🟢 Implementar criação com store obrigatória.
  - Fonte: `views.py`.
  - Critério de pronto: sem store retorna erro claro.

- [ ] 🟢 Implementar paywall/limite.
  - Fonte: `limits.py`, `views.py`.
  - Critério de pronto: bloqueia criação/ativação acima do limite.

- [ ] 🟢 Implementar atualização protegida.
  - Fonte: `views.py`, `serializers.py`.
  - Critério de pronto: senha vazia não apaga senha existente.

- [ ] 🟢 Implementar exclusão com limpeza associada.
  - Fonte: `views.py`.
  - Critério de pronto: health/ROI/snapshots são removidos.

- [ ] 🟡 Criptografar segredos RTSP em repouso.
  - Fonte: lacuna de segurança.
  - Critério de pronto: senha/RTSP recuperáveis não ficam em texto claro no banco.
