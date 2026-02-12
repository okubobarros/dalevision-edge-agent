from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

REQUIRED_ENV = {
    "CLOUD_BASE_URL": ["DALE_CLOUD_BASE_URL"],
    "STORE_ID": ["DALE_STORE_ID"],
    "EDGE_TOKEN": ["DALE_EDGE_TOKEN"],
    "AGENT_ID": ["DALE_AGENT_ID"],
}

DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30
DEFAULT_CAMERA_HEARTBEAT_INTERVAL_SECONDS = 30


@dataclass(frozen=True)
class Settings:
    cloud_base_url: str
    store_id: str
    edge_token: str
    agent_id: str
    heartbeat_interval_seconds: int
    camera_heartbeat_interval_seconds: int


def load_env_from_cwd() -> Path:
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    return env_path


def _get_env_value(name: str, legacy_names: list[str]) -> str:
    value = os.getenv(name)
    if value:
        return value.strip()
    for legacy in legacy_names:
        legacy_value = os.getenv(legacy)
        if legacy_value:
            return legacy_value.strip()
    return ""


def _parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}: {raw}") from exc


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def load_settings() -> Settings:
    missing = []
    values = {}
    for name, legacy_names in REQUIRED_ENV.items():
        value = _get_env_value(name, legacy_names)
        if not value:
            missing.append(name)
        else:
            values[name] = value

    if missing:
        raise ValueError("Missing required env vars: " + ", ".join(missing))

    logger = logging.getLogger("dalevision-edge-agent")
    token = values["EDGE_TOKEN"].strip()
    values["EDGE_TOKEN"] = token
    if token:
        logger.info("EDGE_TOKEN diagnostics len=%s prefix=%s", len(token), token[:6])
        if len(token) < 20:
            logger.error(
                "EDGE_TOKEN inválido (muito curto). Refaça o .env copiando do Wizard."
            )
            raise ValueError("EDGE_TOKEN inválido (muito curto).")

    heartbeat_interval = _parse_int_env(
        "HEARTBEAT_INTERVAL_SECONDS",
        DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    )
    camera_heartbeat_interval = _parse_int_env(
        "CAMERA_HEARTBEAT_INTERVAL_SECONDS",
        DEFAULT_CAMERA_HEARTBEAT_INTERVAL_SECONDS,
    )

    if heartbeat_interval <= 0:
        raise ValueError("HEARTBEAT_INTERVAL_SECONDS must be > 0")
    if camera_heartbeat_interval <= 0:
        raise ValueError("CAMERA_HEARTBEAT_INTERVAL_SECONDS must be > 0")

    return Settings(
        cloud_base_url=_normalize_base_url(values["CLOUD_BASE_URL"]),
        store_id=values["STORE_ID"],
        edge_token=values["EDGE_TOKEN"],
        agent_id=values["AGENT_ID"],
        heartbeat_interval_seconds=heartbeat_interval,
        camera_heartbeat_interval_seconds=camera_heartbeat_interval,
    )
