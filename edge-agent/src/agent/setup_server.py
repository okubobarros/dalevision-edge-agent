from fastapi import FastAPI, HTTPException, UploadFile, File, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yaml
import os
import subprocess
import base64
import uuid
import sys
from pathlib import Path
import re
from typing import Dict, Any

from .runtime_state import RUNTIME_STATE

APP_PORT = 7860

# BASE_DIR = pasta edge-agent
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "agent.yaml")

# ROIs no lugar que você já usa hoje: edge-agent/config/rois
ROIS_DIR = os.path.join(BASE_DIR, "config", "rois")
STATIC_DIR = Path(__file__).resolve().parent / "static"
FAVICON_PATH = STATIC_DIR / "favicon.ico"
LOGO_PATH = STATIC_DIR / "logo.png"

os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
os.makedirs(ROIS_DIR, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DALE Vision Edge Setup")

FILE_PREFIX = "file://"


# Optional dependency (setup must run without OpenCV)
def _try_import_cv2():
    try:
        import cv2
        return cv2
    except Exception:
        return None


CV2 = _try_import_cv2()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


MULTIPART_OK = True
try:
    import multipart  # noqa: F401
except Exception:
    MULTIPART_OK = False
    print("⚠️ python-multipart not installed; /roi/upload disabled")


# -------------------------
# Models
# -------------------------

class CloudConfig(BaseModel):
    cloud_base_url: str
    edge_token: str
    store_id: str


class CameraAddPayload(BaseModel):
    name: str
    rtsp_url: str


class CameraTestPayload(BaseModel):
    rtsp_url: str


# -------------------------
# Helpers
# -------------------------

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def _ensure_defaults(cfg: dict) -> dict:
    """
    Garante o contrato esperado por edge-agent/src/agent/settings.py
    """
    cfg.setdefault("agent", {})
    cfg.setdefault("cloud", {})
    cfg.setdefault("runtime", {})
    cfg.setdefault("model", {})
    cfg.setdefault("cameras", [])

    cfg["agent"].setdefault("agent_id", str(uuid.uuid4()))
    cfg["agent"].setdefault("timezone", "America/Sao_Paulo")

    cfg["cloud"].setdefault(
        "base_url",
        os.getenv("DALE_CLOUD_BASE_URL") or os.getenv("CLOUD_BASE_URL") or "http://127.0.0.1:8000",
    )
    cfg["cloud"].setdefault("timeout_seconds", 15)
    cfg["cloud"].setdefault("send_interval_seconds", 2)
    cfg["cloud"].setdefault("heartbeat_interval_seconds", 30)

    cfg["runtime"].setdefault("target_width", 960)
    cfg["runtime"].setdefault("fps_limit", 8)
    cfg["runtime"].setdefault("frame_skip", 2)
    cfg["runtime"].setdefault("queue_path", "./data/edge_queue.sqlite")
    cfg["runtime"].setdefault("buffer_sqlite_path", "./data/edge_queue.sqlite")
    cfg["runtime"].setdefault("max_queue_size", 50000)
    cfg["runtime"].setdefault("log_level", "INFO")

    cfg["model"].setdefault("yolo_weights_path", "./models/yolov8n.pt")
    cfg["model"].setdefault("conf", 0.35)
    cfg["model"].setdefault("iou", 0.45)
    cfg["model"].setdefault("device", "cpu")

    return cfg


def _normalize_source(src: str) -> str:
    """
    Aceita:
      - rtsp://...
      - file://C:\\...\\media\\cam01.mp4
      - file://..\\media\\cam01.mp4
      - C:\\...\\media\\cam01.mp4
      - ..\\media\\cam01.mp4

    Resolve paths relativos a BASE_DIR (edge-agent).
    """
    src = (src or "").strip()
    if src.lower().startswith(FILE_PREFIX):
        src = src[len(FILE_PREFIX):]

    # se for rtsp, retorna como está
    if src.lower().startswith("rtsp://"):
        return src

    p = Path(src)
    if not p.is_absolute():
        p = Path(BASE_DIR) / p
    return str(p)


def _looks_like_private_store_rtsp(rtsp_url: str) -> bool:
    m = re.search(
        r"rtsp://[^@]+@(?P<ip>\d+\.\d+\.\d+\.\d+)(:\d+)?",
        rtsp_url or "",
        re.IGNORECASE
    )
    if not m:
        return False
    ip = m.group("ip")
    return ip.startswith(("192.168.", "10.", "172."))


def test_rtsp_or_file(source: str):
    if CV2 is None:
        raise HTTPException(
            status_code=501,
            detail="OpenCV (cv2) não está instalado. Instale opencv-python para habilitar preview/snapshot.",
        )

    src = _normalize_source(source)

    cap = CV2.VideoCapture(src)

    try:
        cap.set(CV2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(CV2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)
    except Exception:
        pass

    if not cap.isOpened():
        cap.release()

        if (source or "").lower().startswith("rtsp://") and _looks_like_private_store_rtsp(source):
            raise RuntimeError(
                "Não foi possível abrir o RTSP. Esse IP parece ser da rede da loja (privado). "
                "Para testar RTSP, rode o setup no PC dentro da loja."
            )

        raise RuntimeError(f"Não foi possível abrir a fonte. Verifique caminho/URL: {source}")

    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        raise RuntimeError("Conectou, mas não conseguiu ler frame (stream/path/codec incorreto).")

    ok2, buffer = CV2.imencode(".jpg", frame)
    if not ok2:
        raise RuntimeError("Falha ao gerar snapshot JPG.")

    b64 = base64.b64encode(buffer).decode("utf-8")
    h, w = frame.shape[:2]
    return {"ok": True, "width": int(w), "height": int(h), "snapshot_base64": b64}


# -------------------------
# API Endpoints
# -------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def get_config():
    return load_config()


@app.post("/config")
def set_config(payload: CloudConfig):
    cfg = _ensure_defaults(load_config())

    # contrato do Settings (settings.py)
    cfg["agent"]["store_id"] = payload.store_id
    cfg["cloud"]["base_url"] = payload.cloud_base_url.rstrip("/")
    cfg["cloud"]["token"] = payload.edge_token

    save_config(cfg)
    return {"ok": True}


@app.post("/camera/test")
def camera_test(payload: CameraTestPayload):
    try:
        return test_rtsp_or_file(payload.rtsp_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/camera/add")
def camera_add(payload: CameraAddPayload):
    cfg = _ensure_defaults(load_config())

    cam_id = f"cam{len(cfg['cameras']) + 1:02d}"

    cfg["cameras"].append({
        "camera_id": cam_id,
        "name": payload.name,
        "rtsp_url": payload.rtsp_url,
        # contrato do Settings: roi_config é caminho do YAML
        "roi_config": f"./config/rois/{cam_id}.yaml",
    })

    save_config(cfg)
    return {"ok": True, "camera_id": cam_id}


@app.get("/favicon.ico")
def favicon():
    try:
        if FAVICON_PATH.exists() and FAVICON_PATH.stat().st_size > 0:
            return FileResponse(str(FAVICON_PATH), media_type="image/x-icon")
    except Exception:
        pass
    return Response(status_code=204)


if MULTIPART_OK:
    @app.post("/roi/upload")
    def roi_upload(camera_id: str, file: UploadFile = File(...)):
        if not file.filename.lower().endswith((".yaml", ".yml")):
            raise HTTPException(status_code=400, detail="Arquivo deve ser .yaml ou .yml")

        roi_path = os.path.join(ROIS_DIR, f"{camera_id}.yaml")
        content = file.file.read()

        # valida YAML e estrutura mínima de ROI (contrato do rtsp.py)
        try:
            roi_cfg = yaml.safe_load(content)
        except Exception:
            raise HTTPException(status_code=400, detail="YAML inválido")

        if not isinstance(roi_cfg, dict):
            raise HTTPException(status_code=400, detail="ROI inválido: YAML deve ser um objeto (dict).")

        has_zones = isinstance(roi_cfg.get("zones"), dict) and len(roi_cfg.get("zones")) > 0
        has_lines = isinstance(roi_cfg.get("lines"), dict) and len(roi_cfg.get("lines")) > 0
        has_params = isinstance(roi_cfg.get("params"), dict) and len(roi_cfg.get("params")) > 0
        has_role = isinstance(roi_cfg.get("role"), str) and len(roi_cfg.get("role")) > 0

        if not (has_zones or has_lines or has_params or has_role):
            raise HTTPException(
                status_code=400,
                detail="ROI inválido: esperado pelo menos uma das chaves 'zones', 'lines', 'params' ou 'role'. (isso evita upload do agent.yaml)",
            )

        with open(roi_path, "wb") as f:
            f.write(content)

        return {"ok": True, "roi_file": f"config/rois/{camera_id}.yaml"}
else:
    @app.get("/roi/upload-disabled")
    def roi_upload_disabled():
        return {"ok": False, "reason": "python-multipart not installed"}


@app.get("/status")
def status() -> Dict[str, Any]:
    cfg = _ensure_defaults(load_config())
    agent = cfg.get("agent") or {}
    cloud = cfg.get("cloud") or {}
    cams = cfg.get("cameras") or []
    runtime = RUNTIME_STATE.snapshot()

    cameras_out = []
    for c in cams:
        cid = c.get("camera_id")
        roi_cfg = c.get("roi_config")
        roi_abs = None
        has_roi = False

        if roi_cfg:
            # roi_config geralmente vem como "./config/rois/cam01.yaml"
            roi_abs = os.path.join(BASE_DIR, roi_cfg.replace("./", ""))
            has_roi = os.path.exists(roi_abs)

        cameras_out.append({
            "camera_id": cid,
            "name": c.get("name"),
            "has_roi": bool(has_roi),
            "roi_config": roi_cfg,
        })

    return {
        "config_exists": os.path.exists(CONFIG_PATH),
        "agent": {
            "agent_id": agent.get("agent_id"),
            "store_id": agent.get("store_id"),
            "timezone": agent.get("timezone"),
        },
        "cloud": {
            "base_url": cloud.get("base_url"),
            "token_set": bool(cloud.get("token")),
        },
        "agent_running": runtime.get("agent_running"),
        "heartbeat_only": runtime.get("heartbeat_only"),
        "last_heartbeat_sent_at": runtime.get("last_heartbeat_sent_at"),
        "last_heartbeat_ok": runtime.get("last_heartbeat_ok"),
        "last_heartbeat_http_status": runtime.get("last_heartbeat_http_status"),
        "last_heartbeat_error": runtime.get("last_heartbeat_error"),
        "last_backend_seen_ok_at": runtime.get("last_backend_seen_ok_at"),
        "counters": {
            "sent_ok": runtime.get("sent_ok"),
            "sent_fail": runtime.get("sent_fail"),
        },
        "cameras": cameras_out,
    }


@app.post("/agent/start")
def agent_start():
    """
    Inicia o agente em modo run usando o python do venv atual.
    Não depende de binário edge-agent ainda.
    """
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=400, detail="Config não encontrada. Salve a config antes de iniciar.")

    try:
        LOGS_DIR = os.path.join(BASE_DIR, "logs")
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_path = os.path.join(LOGS_DIR, "agent.log")
        logf = open(log_path, "a", encoding="utf-8")

        p = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.agent",
                "run",
                "--config",
                CONFIG_PATH,
            ],
            cwd=BASE_DIR,
            stdout=logf,
            stderr=logf,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        return {
            "started": True,
            "pid": p.pid,
            "config_path": CONFIG_PATH,
            "log_path": log_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# UI (HTML + JS)
# -------------------------

@app.get("/", response_class=HTMLResponse)
def ui():
    return f"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>DALE Vision — Edge Setup</title>
  <link rel="icon" href="/favicon.ico" />
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #0b0f14; color: #e6edf3; }}
    .wrap {{ max-width: 980px; margin: 0 auto; }}
    .card {{ background:#111826; border:1px solid #1f2a37; border-radius:12px; padding:16px; margin:12px 0; }}
    h1 {{ margin: 0 0 8px 0; font-size: 20px; }}
    h2 {{ margin: 0 0 8px 0; font-size: 16px; }}
    label {{ display:block; margin: 10px 0 6px; color:#b9c2cf; font-size: 12px; }}
    input {{ width:100%; padding:10px; border-radius:10px; border:1px solid #2a3a52; background:#0b1220; color:#e6edf3; }}
    button {{ padding:10px 12px; border-radius:10px; border:1px solid #2a3a52; background:#1f2a37; color:#e6edf3; cursor:pointer; }}
    button.primary {{ background:#2563eb; border-color:#1d4ed8; }}
    .row {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .small {{ font-size: 12px; color:#9aa5b1; }}
    .ok {{ color:#22c55e; }}
    .bad {{ color:#ef4444; }}
    pre {{ white-space: pre-wrap; background:#0b1220; border:1px solid #2a3a52; border-radius:10px; padding:10px; }}
    img {{ max-width: 100%; border-radius: 12px; border: 1px solid #2a3a52; }}
    .actions {{ display:flex; gap: 10px; align-items:center; flex-wrap: wrap; }}
    .pill {{ display:inline-block; padding:4px 8px; border-radius:999px; background:#0b1220; border:1px solid #2a3a52; font-size:12px; }}
  </style>
</head>
<body>
<div class="wrap">
  <h1>DALE Vision — Edge Setup (localhost:{APP_PORT})</h1>
  <div style="margin: 8px 0 12px;">
    <img src="/static/logo.png" alt="Dale Vision" style="height: 40px;" />
  </div>
  <div class="small">DEV em casa: use <code>file://videos/cam01_balcao.mp4</code> (os vídeos estão em edge-agent/videos).</div>

  <div class="card">
    <h2>1) Config Cloud</h2>
    <div class="row">
      <div>
        <label>Cloud Base URL</label>
        <input id="cloud_base_url" placeholder="http://127.0.0.1:8000" />
      </div>
      <div>
        <label>Store ID</label>
        <input id="store_id" placeholder="uuid da store" />
      </div>
    </div>
    <label>Edge Token (X-EDGE-TOKEN)</label>
    <input id="edge_token" placeholder="token do edge" />
    <div class="actions" style="margin-top:12px;">
      <button class="primary" onclick="saveConfig()">Salvar Config</button>
      <span id="config_msg" class="pill"></span>
    </div>
  </div>

  <div class="card">
    <h2>2) Testar câmera (RTSP ou file://)</h2>
    <div class="row">
      <div>
        <label>Nome (para adicionar)</label>
        <input id="cam_name" placeholder="Checkout 1" />
      </div>
      <div>
        <label>RTSP URL (ou file://..\\media\\cam01_balcao.mp4)</label>
        <input id="rtsp_url" placeholder="rtsp://user:pass@192.168.0.10:554/..." />
      </div>
    </div>
    <div class="actions" style="margin-top:12px;">
      <button onclick="testCamera()">Testar (preview)</button>
      <button class="primary" onclick="addCamera()">Adicionar câmera</button>
      <span id="cam_msg" class="pill"></span>
    </div>

    <div style="margin-top:12px;">
      <div class="small">Preview:</div>
      <img id="preview" style="display:none;" />
      <pre id="preview_meta" style="display:none;"></pre>
    </div>
  </div>

  <div class="card">
    <h2>3) Upload ROI (YAML)</h2>
    <div class="row">
      <div>
        <label>Camera ID (ex: cam01)</label>
        <input id="roi_camera_id" placeholder="cam01" />
      </div>
      <div>
        <label>Arquivo ROI (.yaml)</label>
        <input id="roi_file" type="file" accept=".yaml,.yml" />
      </div>
    </div>
    <div class="actions" style="margin-top:12px;">
      <button class="primary" onclick="uploadRoi()">Upload ROI</button>
      <span id="roi_msg" class="pill"></span>
    </div>
  </div>

  <div class="card">
    <h2>4) Status</h2>
    <div class="actions">
      <button onclick="refreshStatus()">Atualizar status</button>
      <button class="primary" onclick="startAgent()">Iniciar agente</button>
      <span id="status_msg" class="pill"></span>
    </div>
    <pre id="status_box"></pre>
  </div>
</div>

<script>
  async function api(method, path, body, isForm=false) {{
    const opts = {{ method, headers: {{}} }};
    if (body) {{
      if (isForm) {{
        opts.body = body;
      }} else {{
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
      }}
    }}
    const res = await fetch(path, opts);
    const text = await res.text();
    let data = null;
    try {{ data = JSON.parse(text); }} catch(e) {{ data = {{ raw: text }}; }}
    if (!res.ok) {{
      const msg = (data && data.detail) ? data.detail : ('HTTP ' + res.status);
      throw new Error(msg);
    }}
    return data;
  }}

  function setMsg(id, ok, msg) {{
    const el = document.getElementById(id);
    el.textContent = msg || '';
    el.className = 'pill ' + (ok ? 'ok' : 'bad');
  }}

  async function saveConfig() {{
    try {{
      const payload = {{
        cloud_base_url: document.getElementById('cloud_base_url').value.trim(),
        store_id: document.getElementById('store_id').value.trim(),
        edge_token: document.getElementById('edge_token').value.trim(),
      }};
      await api('POST', '/config', payload);
      setMsg('config_msg', true, 'Config salva ✅');
      await refreshStatus();
    }} catch(e) {{
      setMsg('config_msg', false, e.message);
    }}
  }}

  async function testCamera() {{
    try {{
      const rtsp_url = document.getElementById('rtsp_url').value.trim();
      const data = await api('POST', '/camera/test', {{ rtsp_url }});
      setMsg('cam_msg', true, 'Preview OK ✅');
      const img = document.getElementById('preview');
      img.src = 'data:image/jpeg;base64,' + data.snapshot_base64;
      img.style.display = 'block';
      const meta = document.getElementById('preview_meta');
      meta.style.display = 'block';
      meta.textContent = JSON.stringify({{ width: data.width, height: data.height }}, null, 2);
    }} catch(e) {{
      setMsg('cam_msg', false, e.message);
    }}
  }}

  async function addCamera() {{
    try {{
      const name = document.getElementById('cam_name').value.trim();
      const rtsp_url = document.getElementById('rtsp_url').value.trim();
      const data = await api('POST', '/camera/add', {{ name, rtsp_url }});
      setMsg('cam_msg', true, 'Câmera adicionada: ' + data.camera_id + ' ✅');
      document.getElementById('roi_camera_id').value = data.camera_id;
      await refreshStatus();
    }} catch(e) {{
      setMsg('cam_msg', false, e.message);
    }}
  }}

  async function uploadRoi() {{
    try {{
      const camera_id = document.getElementById('roi_camera_id').value.trim();
      const f = document.getElementById('roi_file').files[0];
      if (!camera_id) throw new Error('Informe camera_id (ex: cam01).');
      if (!f) throw new Error('Selecione um arquivo .yaml.');
      const form = new FormData();
      form.append('file', f);
      const data = await api('POST', '/roi/upload?camera_id=' + encodeURIComponent(camera_id), form, true);
      setMsg('roi_msg', true, 'ROI ok ✅');
      await refreshStatus();
    }} catch(e) {{
      setMsg('roi_msg', false, e.message);
    }}
  }}

  async function refreshStatus() {{
    try {{
      const data = await api('GET', '/status');
      document.getElementById('status_box').textContent = JSON.stringify(data, null, 2);
      setMsg('status_msg', true, 'Status atualizado ✅');
    }} catch(e) {{
      setMsg('status_msg', false, e.message);
    }}
  }}

  async function startAgent() {{
    try {{
      const data = await api('POST', '/agent/start');
      setMsg('status_msg', true, 'Agente iniciado ✅ PID: ' + data.pid + ' | Logs: logs/agent.log');
    }} catch(e) {{
      setMsg('status_msg', false, e.message);
    }}
  }}

  refreshStatus();
</script>
</body>
</html>
"""
