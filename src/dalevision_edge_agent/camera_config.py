from __future__ import annotations

from typing import Any

from .activation import ConfigManager

INDICATOR_ALIAS_MAP = {
    "flow": "flow",
    "entry": "flow",
    "entrada": "flow",
    "entry_flow": "flow",
    "queue": "queue",
    "fila": "queue",
    "queue_monitoring": "queue",
    "occupancy": "occupancy",
    "ocupacao": "occupancy",
    "occupancy_monitoring": "occupancy",
    "productivity": "productivity",
    "produtividade": "productivity",
    "staff": "productivity",
    "staff_presence": "productivity",
}


def normalize_indicator_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    values = raw if isinstance(raw, list) else [raw]
    normalized: list[str] = []
    for item in values:
        key = str(item or "").strip().lower()
        if not key:
            continue
        mapped = INDICATOR_ALIAS_MAP.get(key)
        if not mapped:
            continue
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def build_camera_processing_plan(camera: dict[str, Any]) -> dict[str, bool]:
    indicators = normalize_indicator_list(camera.get("indicators"))
    if not indicators:
        role = str(camera.get("role") or "").strip().lower()
        if role == "entrada":
            indicators = ["flow"]
        elif role == "balcao":
            indicators = ["queue", "productivity"]
        elif role == "salao":
            indicators = ["occupancy"]
    return {
        "flow": "flow" in indicators,
        "queue": "queue" in indicators,
        "occupancy": "occupancy" in indicators,
        "productivity": "productivity" in indicators,
    }


def load_cameras_from_agent_config() -> list[dict[str, Any]]:
    payload = ConfigManager.from_default().load()
    for key in ("cameras", "local_cameras"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []
