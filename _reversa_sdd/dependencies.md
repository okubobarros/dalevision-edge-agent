# Dependencias - DaleVision

Gerado em: 2026-05-06T19:44:13.1241613Z

## dalevision-edge-agent

Fonte: C:\workspace\dalevision-edge-agent\pyproject.toml

### Runtime Python

- Python >=3.10.
- requests>=2.31.0 - chamadas HTTP para cloud/backend.
- python-dotenv>=1.0.1 - carregamento de .env.
- pydantic>=2.6.0 - validacao/modelos de configuracao.
- pyyaml>=6.0.1 - configuracao YAML/ROI.

### Extras

- dev: pytest>=7.4.0.
- vision: ultralytics>=8.3.0, opencv-python>=4.8.1.78, numpy>=1.26.4, lap>=0.5.12, charset_normalizer>=3.3.0.

### Ferramentas/ambiente detectados

- PyInstaller/spec: dalevision-edge-agent.spec.
- PowerShell/Batch para instalacao, release e update.
- ffmpeg opcional via PATH para snapshot quando OpenCV nao esta disponivel.

## dale-vision backend

Fontes: C:\workspace\dale-vision\requirements.txt e requirements.prod.txt

### Principais dependencias de producao

- Django==4.2.11.
- djangorestframework==3.14.0.
- django-cors-headers==4.2.0.
- django-filter==23.5.
- django-rest-knox==4.2.0.
- drf-yasg==1.21.7.
- gunicorn==21.2.0.
- whitenoise==6.6.0.
- psycopg2-binary==2.9.9.
- python-dotenv==1.0.0.
- requests==2.31.0.
- opencv-python-headless==4.10.0.84.
- numpy==1.26.4.
- dj-database-url==2.2.0.

### Dependencias adicionais no requirements completo

- Supabase stack: supabase==2.3.1, gotrue, postgrest, realtime, storage3, supafunc.
- Cloud/storage: boto3, botocore, django-storages.
- Dados/analytics/CV: pandas, polars, plotly, matplotlib, scipy, torch, torchvision, ultralytics.
- Observabilidade/runtime: sentry-sdk, redis, django-redis, psutil.
- Google APIs: google-api-python-client, google-auth, google-auth-httplib2.

## dale-vision frontend

Fonte: C:\workspace\dale-vision\frontend\package.json

### Runtime

- react ^19.2.0.
- react-dom ^19.2.0.
- react-router-dom ^7.12.0.
- @tanstack/react-query ^5.90.16.
- @supabase/supabase-js ^2.50.0.
- axios ^1.13.2.
- recharts ^3.6.0.
- react-hot-toast ^2.6.0.
- @heroicons/react ^2.2.0.

### Desenvolvimento/build

- vite ^7.2.4.
- typescript ~5.9.3.
- vitest ^3.2.4.
- @testing-library/react ^16.3.0.
- eslint ^9.39.1.
- tailwindcss ^3.4.19.
- Package manager declarado: pnpm@10.26.2.

## Gerenciadores e deploy

- Backend: pip/requirements, Render scripts em bin/.
- Frontend: pnpm/Vite, Vercel configurado por vercel.json.
- Agente: setuptools/PyInstaller + scripts PowerShell para release Windows.
