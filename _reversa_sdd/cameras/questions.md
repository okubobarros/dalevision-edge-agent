# cameras - Questions

## Lacunas

1. 🟡 `test-snapshot` persiste caminho temporário local em `last_snapshot_url`. Confirmar se endpoint é apenas demo/dev ou se precisa ser removido/protegido em produção.

2. 🟡 Backend snapshot usa signed URL, enquanto edge snapshot usa public URL. Confirmar política desejada de privacidade dos snapshots.

3. 🟡 `CameraSerializer` faz queries por câmera para latency/health; confirmar volume esperado e necessidade de otimização.

4. 🟡 `CameraROIConfig` e `CameraSnapshot` são unmanaged. Confirmar se migrations/tabelas Supabase estão versionadas fora do Django.

5. 🟡 ROI exige validação da versão anterior para publicar nova, mas a primeira publicação não exige validação. Confirmar regra de negócio.

6. 🟡 Senhas RTSP ficam no banco em texto recuperável. Confirmar estratégia de criptografia/segredo em repouso.
