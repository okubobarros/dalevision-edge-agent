import os
import time
import json
import uuid
import sqlite3
import hashlib
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configurações Mínimas (Ambiente Opcional no .env) ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
EDGE_TOKEN = os.getenv("EDGE_TOKEN", "edge_token_dev_123")
STORE_ID = os.getenv("STORE_ID", "6663f7d1-e9bf-4375-bebe-0d35eade90f0")
CAMERA_ID = os.getenv("CAMERA_ID", "cam_checkout_01")

# Constantes de Estado
SQLITE_DB = "mvp_events.db"
INTERVAL_SECONDS = 60

# --- 1. Inicialização do Banco Local ---
def init_db():
    print(f"[*] Inicializando Banco Local: {SQLITE_DB}")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    # Tabela para retry de eventos falhos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_events (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            retries INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# --- 2. Geração Controlada de Eventos de Fila ---
def generate_queue_event():
    # Simulando contagem (mock para o MVP end-to-end)
    # Na vida real: model_inference.count_people()
    import random
    count = random.randint(1, 8) 
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    event_type = "queue_count"
    
    # Idempotency Hash (Garante que nunca haverá duplicação no envio)
    raw_str = f"{STORE_ID}:{CAMERA_ID}:{timestamp}:{event_type}"
    event_id = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
    
    payload = {
        "event_id": event_id,
        "camera_id": CAMERA_ID,
        "store_id": STORE_ID,
        "timestamp": timestamp,
        "event_type": event_type,
        "data": {
            "count": count
        }
    }
    return event_id, payload

# --- 3. Motor de Envio com Tolerância a Falhas ---
def send_payload(event_id, payload):
    url = f"{API_BASE_URL}/v1/ingest/events/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {EDGE_TOKEN}"
    }
    
    print(f"[>] Enviando Evento {event_id[:8]}... (Count: {payload['data']['count']})")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # 200/201 é sucesso (INCLUSIVE se for duplicado ignorado pelo backend ON CONFLICT)
        if response.status_code in [200, 201]:
            print(f"[V] Evento sincronizado com sucesso (Status: {response.status_code})")
            return True
        else:
            print(f"[X] Servidor recusou o payload (Status: {response.status_code}). Descartando via regra de MVP para evitar loop.")
            # Para o MVP vamos assumir que 400s não tem retry local, só 500s ou timeouts
            if response.status_code >= 500:
                return False
            return True # Descartado intencionalmente
            
    except requests.exceptions.RequestException as e:
        print(f"[!] Falha na rede: {str(e)}")
        return False

# --- 4. Gerenciamento Local SQLite ---
def save_to_queue(event_id, payload):
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO pending_events (id, payload) VALUES (?, ?)",
        (event_id, json.dumps(payload))
    )
    conn.commit()
    conn.close()
    print(f"[*] Evento armazenado em disco (Queue Local)")

def flush_queue():
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, payload FROM pending_events ORDER BY created_at ASC LIMIT 10")
    rows = cursor.fetchall()
    
    for row in rows:
        event_id = row[0]
        payload = json.loads(row[1])
        print(f"[>] Retentando evento antigo {event_id[:8]}...")
        
        if send_payload(event_id, payload):
            cursor.execute("DELETE FROM pending_events WHERE id = ?", (event_id,))
            conn.commit()
        else:
            # Incrementa tentativas
            cursor.execute("UPDATE pending_events SET retries = retries + 1 WHERE id = ?", (event_id,))
            conn.commit()
            break # Caiu a rede de novo, espera próximo ciclo
            
    conn.close()

# --- 5. Ping Central ---
def send_heartbeat():
    try:
        url = f"{API_BASE_URL}/v1/edge/ping/"
        headers = {"Authorization": f"Bearer {EDGE_TOKEN}"}
        requests.get(url, headers=headers, timeout=5)
    except Exception:
        pass # Silencioso, heartbeat não trava a fila de eventos principais

# --- Loop Principal ---
def run_minimal_agent():
    print("====================================")
    print("DaleVision - Minimal Edge Agent MVP")
    print("====================================")
    
    init_db()
    
    while True:
        # 1. Avisa que tá vivo
        send_heartbeat()
        
        # 2. Tenta esvaziar fila offline
        flush_queue()
        
        # 3. Gera e envia novo evento (se falhar, vai pro banco)
        event_id, payload = generate_queue_event()
        success = send_payload(event_id, payload)
        
        if not success:
            save_to_queue(event_id, payload)
            
        print(f"[Z] Aguardando {INTERVAL_SECONDS}s para o próximo frame logico...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_minimal_agent()
