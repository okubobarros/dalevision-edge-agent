# Runtime Architecture

- Processo principal: `dalevision_edge_agent.main:main` (Windows service ou console).
- Módulos chave: ingest (heartbeat/camera health), vision worker (opcional), outbox (offline-first), updater.
- Dados locais: `.env` para credenciais, cache/outbox SQLite, logs em `%PROGRAMDATA%` ou `./logs` quando dev.
- Comunicações: HTTPS com `CLOUD_BASE_URL` para policy, update, ingest; sem streaming completo para cloud.
- Threads/services: scheduler de heartbeat, watcher de câmera, updater, vision loop quando habilitado.
