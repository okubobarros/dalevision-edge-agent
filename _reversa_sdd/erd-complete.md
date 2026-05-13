# ERD Completo

Escala: 🟢 CONFIRMADO | 🟡 INFERIDO | 🔴 LACUNA

```mermaid
erDiagram
    USER ||--o{ ORG_MEMBER : belongs_to
    ORGANIZATION ||--o{ ORG_MEMBER : has
    ORGANIZATION ||--o{ STORE : owns
    STORE ||--o{ STORE_ZONE : has
    STORE ||--o{ CAMERA : has
    STORE ||--o{ EMPLOYEE : employs
    STORE ||--o{ DETECTION_EVENT : receives
    STORE ||--o{ EDGE_DEVICE : has
    STORE ||--o{ EDGE_TOKEN : has
    STORE ||--o{ ACTIVATION_TOKEN : issues
    STORE ||--o{ EDGE_EVENT_MINUTE_STATS : aggregates
    STORE ||--o{ EDGE_EVENT_RAW : stores
    STORE ||--o{ STORE_DAILY_METRICS : summarizes
    STORE ||--o{ ALERT_RULE : configures
    STORE ||--o{ NOTIFICATION_LOG : emits
    STORE ||--o{ COPILOT_OPERATIONAL_INSIGHT : receives
    STORE ||--o{ ACTION_OUTCOME : tracks
    STORE ||--o{ VALUE_LEDGER_DAILY : values
    CAMERA ||--o{ CAMERA_HEALTH : has
    CAMERA ||--o{ CAMERA_SNAPSHOT : captures
    CAMERA ||--o{ CAMERA_ROI_CONFIG : configures
    CAMERA ||--o{ DETECTION_EVENT : produces
    DETECTION_EVENT ||--o{ EVENT_MEDIA : has
    EMPLOYEE ||--o{ SHIFT : assigned
    EMPLOYEE ||--o{ TIME_CLOCK_ENTRY : clocks
    BILLING_CUSTOMER ||--o{ SUBSCRIPTION : owns
    EDGE_RELEASE ||--o{ EDGE_UPDATE_POLICY : selected_by
    EDGE_DEVICE ||--o{ EDGE_UPDATE_EVENT : reports
    COPILOT_CONVERSATION ||--o{ COPILOT_MESSAGE : contains

    STORE {
      uuid id PK
      uuid organization_id FK
      string name
      string status
      string blocked_reason
    }
    CAMERA {
      uuid id PK
      uuid store_id FK
      string name
      string rtsp_url
      string status
    }
    DETECTION_EVENT {
      uuid id PK
      uuid store_id FK
      uuid camera_id FK
      string event_id
      string event_type
      datetime occurred_at
      json payload
    }
    EDGE_DEVICE {
      uuid id PK
      uuid store_id FK
      string agent_id
      string version
      string status
      datetime last_seen_at
    }
    EDGE_TOKEN {
      uuid id PK
      uuid store_id FK
      string token_hash
      bool active
    }
    ACTIVATION_TOKEN {
      uuid id PK
      uuid store_id FK
      string token_hash
      datetime expires_at
      datetime used_at
    }
```

🟡 INFERIDO: O diagrama mostra as entidades e atributos principais para leitura arquitetural. O dicionario operacional completo esta em `data-dictionary.md`.

🔴 LACUNA: Confirmar constraints, indices e modelos `managed = False` diretamente no banco antes de migracoes destrutivas.
