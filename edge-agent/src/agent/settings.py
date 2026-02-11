from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
import os
import sys


@dataclass
class CameraConfig:
    camera_id: str
    name: str
    rtsp_url: str
    roi_config: str


@dataclass
class Settings:
    agent_id: str
    store_id: str
    timezone: str

    cloud_base_url: str
    cloud_token: str
    cloud_timeout: int
    send_interval_seconds: int
    heartbeat_interval_seconds: int

    target_width: int
    fps_limit: int
    frame_skip: int
    queue_path: str
    buffer_sqlite_path: str
    max_queue_size: int
    log_level: str
    vision_enabled: bool

    yolo_weights_path: str
    conf: float
    iou: float
    device: str

    cameras: List[CameraConfig]


def _pick_env(primary: str, fallback: str) -> tuple[Optional[str], Optional[str]]:
    val = os.getenv(primary)
    if val is not None and val.strip() != "":
        return val.strip(), primary
    val = os.getenv(fallback)
    if val is not None and val.strip() != "":
        return val.strip(), fallback
    return None, None


def _resolve_env_sources() -> Dict[str, Optional[str]]:
    base, base_src = _pick_env("CLOUD_BASE_URL", "DALE_CLOUD_BASE_URL")
    store_id, store_src = _pick_env("STORE_ID", "DALE_STORE_ID")
    agent_id, agent_src = _pick_env("AGENT_ID", "DALE_AGENT_ID")
    edge_token, edge_token_src = _pick_env("EDGE_TOKEN", "DALE_EDGE_TOKEN")

    edge_cloud_token = os.getenv("EDGE_CLOUD_TOKEN")
    if not edge_token and edge_cloud_token is not None and edge_cloud_token.strip() != "":
        edge_token = edge_cloud_token.strip()
        edge_token_src = "EDGE_CLOUD_TOKEN"

    return {
        "base": base,
        "base_src": base_src,
        "store_id": store_id,
        "store_src": store_src,
        "agent_id": agent_id,
        "agent_src": agent_src,
        "edge_token": edge_token,
        "edge_token_src": edge_token_src,
    }


def _mask_secret(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if len(v) <= 8:
        return "*" * len(v)
    return f"{v[:4]}...{v[-4:]}"


def _env_override(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Permite override via env (útil pra Docker depois).
    Ex: CLOUD_BASE_URL, EDGE_TOKEN, STORE_ID, AGENT_ID (com fallback DALE_*).
    """
    # mantenha simples no v1; expanda conforme precisar
    envs = _resolve_env_sources()
    base = envs.get("base")
    token = envs.get("edge_token")
    store_id = envs.get("store_id")
    agent_id = envs.get("agent_id")
    heartbeat = os.getenv("HEARTBEAT_INTERVAL_SECONDS")
    heartbeat_timeout = os.getenv("HEARTBEAT_TIMEOUT_SECONDS")
    vision_env = os.getenv("EDGE_VISION_ENABLED")
    vision_enabled = None
    if vision_env is not None:
        v = vision_env.strip().lower()
        if v in ("1", "true", "yes", "y", "on"):
            vision_enabled = True
        elif v in ("0", "false", "no", "n", "off"):
            vision_enabled = False
    if base:
        d.setdefault("cloud", {})
        d["cloud"]["base_url"] = base
    if token:
        d.setdefault("cloud", {})
        d["cloud"]["token"] = token
    if store_id:
        d.setdefault("agent", {})
        d["agent"]["store_id"] = store_id
    if agent_id:
        d.setdefault("agent", {})
        d["agent"]["agent_id"] = agent_id
    if heartbeat:
        d.setdefault("cloud", {})["heartbeat_interval_seconds"] = int(heartbeat)
    if heartbeat_timeout:
        d.setdefault("cloud", {})["timeout_seconds"] = int(heartbeat_timeout)
    if vision_enabled is not None:
        d.setdefault("runtime", {})["vision_enabled"] = vision_enabled
    return d


def load_settings(path: str) -> Settings:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    raw = _env_override(raw)
    envs = _resolve_env_sources()

    agent = raw.get("agent", {})
    cloud = raw.get("cloud", {})
    runtime = raw.get("runtime", {})
    model = raw.get("model", {})
    cams = raw.get("cameras", []) or []

    cameras = [
        CameraConfig(
            camera_id=c["camera_id"],
            name=c.get("name", c["camera_id"]),
            rtsp_url=c["rtsp_url"],
            roi_config=c["roi_config"],
        )
        for c in cams
    ]

    base_dir = Path(__file__).resolve().parents[2]
    queue_path_raw = runtime.get("queue_path") or runtime.get("buffer_sqlite_path") or "./data/edge_queue.sqlite"
    queue_path = Path(queue_path_raw)
    if not queue_path.is_absolute():
        queue_path = base_dir / queue_path
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    base_url = (cloud.get("base_url") or "").strip()
    if not base_url:
        base_url = os.getenv("CLOUD_BASE_URL") or os.getenv("DALE_CLOUD_BASE_URL") or "http://127.0.0.1:8000"

    missing = []
    if not agent.get("store_id"):
        missing.append("STORE_ID")
    if not cloud.get("token"):
        missing.append("EDGE_TOKEN")
    if not base_url:
        missing.append("CLOUD_BASE_URL")
    if missing:
        print(
            "[EDGE] Missing required env/config: "
            + ", ".join(missing)
            + " (prefer STORE_ID, EDGE_TOKEN, CLOUD_BASE_URL)"
        )
        sys.exit(1)

    base_src = envs.get("base_src")
    store_src = envs.get("store_src")
    agent_src = envs.get("agent_src")
    token_src = envs.get("edge_token_src")

    if base_src:
        print(f"[EDGE] CLOUD_BASE_URL={base_url} (env:{base_src})")
    else:
        print(f"[EDGE] CLOUD_BASE_URL={base_url} (config/default)")

    if store_src:
        print(f"[EDGE] STORE_ID={agent.get('store_id')} (env:{store_src})")
    else:
        print(f"[EDGE] STORE_ID={agent.get('store_id')} (config)")

    if agent_src:
        print(f"[EDGE] AGENT_ID={agent.get('agent_id')} (env:{agent_src})")
    else:
        print(f"[EDGE] AGENT_ID={agent.get('agent_id')} (config)")

    if token_src:
        print(f"[EDGE] EDGE_TOKEN={_mask_secret(cloud.get('token', ''))} (env:{token_src})")
    else:
        print(f"[EDGE] EDGE_TOKEN={_mask_secret(cloud.get('token', ''))} (config)")

    return Settings(
        agent_id=agent["agent_id"],
        store_id=agent["store_id"],
        timezone=agent.get("timezone", "America/Sao_Paulo"),

        cloud_base_url=base_url.rstrip("/"),
        cloud_token=cloud["token"],
        cloud_timeout=int(cloud.get("timeout_seconds", 15)),
        send_interval_seconds=int(cloud.get("send_interval_seconds", 2)),
        heartbeat_interval_seconds=int(cloud.get("heartbeat_interval_seconds", 30)),

        target_width=int(runtime.get("target_width", 960)),
        fps_limit=int(runtime.get("fps_limit", 8)),
        frame_skip=int(runtime.get("frame_skip", 2)),
        queue_path=str(queue_path),
        buffer_sqlite_path=str(queue_path),
        max_queue_size=int(runtime.get("max_queue_size", 50000)),
        log_level=str(runtime.get("log_level", "INFO")),
        vision_enabled=(
            str(runtime.get("vision_enabled", True)).strip().lower() in ("1", "true", "yes", "y", "on")
            if isinstance(runtime.get("vision_enabled", True), str)
            else bool(runtime.get("vision_enabled", True))
        ),

        yolo_weights_path=str(model.get("yolo_weights_path", "./models/yolov8n.pt")),
        conf=float(model.get("conf", 0.35)),
        iou=float(model.get("iou", 0.45)),
        device=str(model.get("device", "cpu")),

        cameras=cameras,
    )
