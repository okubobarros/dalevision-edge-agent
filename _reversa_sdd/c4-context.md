# C4 Contexto

Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

```mermaid
flowchart TB
    Owner["Pessoa: Owner/Admin/Manager\nOpera lojas, cameras, alertas e billing"]
    Viewer["Pessoa: Viewer\nConsulta dashboards e cameras"]
    Support["Pessoa: Suporte DaleVision\nDiagnostico remoto com grant"]
    ClientNetwork["Ambiente Cliente\nNVR, Cameras IP, rede local"]
    System["Sistema DaleVision\nPlataforma cloud + edge para visao operacional de varejo"]
    Supabase["Supabase\nAuth/JWT/Storage"]
    Postgres["Postgres\nDados operacionais"]
    Redis["Redis\nCache/coordernacao"]
    Vercel["Vercel\nFrontend SPA"]
    Render["Render\nBackend Django API"]
    OpenRouter["OpenRouter/LLM\nCopilot e insights"]
    Google["Google APIs\nRelatorios/automacoes"]
    Meta["WhatsApp/Meta\nCompartilhamento/alertas inferidos"]

    Owner -->|HTTPS Web| System
    Viewer -->|HTTPS Web| System
    Support -->|HTTPS Web + grants| System
    ClientNetwork -->|RTSP/HTTP local| System
    System -->|Hospeda frontend| Vercel
    System -->|Hospeda API| Render
    System -->|SQL| Postgres
    System -->|JWT/Storage HTTPS| Supabase
    System -->|TCP/TLS| Redis
    System -->|HTTPS| OpenRouter
    System -->|HTTPS| Google
    System -->|HTTPS| Meta
```

## Relacionamentos

| Origem | Destino | Protocolo | Descricao | Confianca |
|---|---|---|---|---|
| Browser | Frontend Vercel | HTTPS | SPA de operacao. | 🟢 CONFIRMADO |
| Frontend | Backend Django | HTTPS REST | APIs `/api/` e `/api/v1/`. | 🟢 CONFIRMADO |
| Edge Agent | Backend Django | HTTPS REST | Activation, heartbeat, camera health, update, events. | 🟢 CONFIRMADO |
| Edge Agent | NVR/Cameras | RTSP/HTTP | Captura e health local. | 🟢 CONFIRMADO |
| Backend | Postgres | SQL | Persistencia. | 🟢 CONFIRMADO |
| Backend/Frontend | Supabase | HTTPS/JWT | Auth/storage. | 🟢 CONFIRMADO |
| Backend | Redis | TCP/TLS | Cache/coordernacao. | 🟢 CONFIRMADO como config |
| Backend | LLM/Google/Meta | HTTPS | Copilot/relatorios/mensageria. | 🟡 INFERIDO |
