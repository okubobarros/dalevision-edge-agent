from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import logging
import os
from pathlib import Path
import re
import socket
import uuid

from dotenv import dotenv_values
from .paths import resolve_runtime_paths

REQUIRED_ENV = {
    "CLOUD_BASE_URL": ["DALE_CLOUD_BASE_URL"],
    "STORE_ID": ["DALE_STORE_ID"],
    "EDGE_TOKEN": ["DALE_EDGE_TOKEN"],
}
OPTIONAL_ENV = {
    "AGENT_ID": ["DALE_AGENT_ID"],
}

DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 60
DEFAULT_CAMERA_HEARTBEAT_INTERVAL_SECONDS = 60
DEFAULT_MAX_ACTIVE_CAMERAS = 3
DEFAULT_UPDATE_INTERVAL_SECONDS = 21600


@dataclass(frozen=True)
class Settings:
    cloud_base_url: str
    store_id: str
    edge_token: str
    agent_id: str
    heartbeat_interval_seconds: int
    camera_heartbeat_interval_seconds: int
    max_active_cameras: int
    rtsp_describe_enabled: bool
    update_check_url: str
    update_interval_seconds: int
    auto_update_enabled: bool


class InvalidTokenError(ValueError):
    pass


def _sanitize_agent_id(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", cleaned)
    cleaned = cleaned.strip("-._")
    return cleaned[:64]


def _default_agent_id(store_id: str) -> str:
    host = os.getenv("COMPUTERNAME") or socket.gethostname() or "host"
    host = _sanitize_agent_id(host.lower()) or "host"
    suffix = _sanitize_agent_id(store_id)[:8] or "store"
    return f"edge-{host}-{suffix}"[:64]


def _read_env_text(env_path: Path) -> str:
    data = env_path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("latin-1", errors="replace")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.lstrip("\ufeff")


def describe_env_file(env_path: Path) -> dict:
    info = {
        "path": str(env_path),
        "exists": False,
        "mtime_utc": None,
        "size_bytes": None,
        "sha256": None,
        "error": None,
    }
    try:
        if env_path.exists():
            stat = env_path.stat()
            info["exists"] = True
            info["size_bytes"] = int(stat.st_size)
            info["mtime_utc"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            info["sha256"] = hashlib.sha256(env_path.read_bytes()).hexdigest()
    except Exception as exc:
        info["error"] = str(exc)
    return info


def load_env_from_cwd() -> Path:
    runtime_paths = resolve_runtime_paths()
    explicit_env = os.getenv("DALE_ENV_PATH")
    candidates = []
    if explicit_env:
        candidates.append(Path(explicit_env))
    candidates.extend(
        [
            runtime_paths.config_dir / ".env",
            Path.cwd() / ".env",
        ]
    )

    selected = candidates[0]
    for env_path in candidates:
        if env_path.exists():
            selected = env_path
            break
    if selected.exists():
        text = _read_env_text(selected)
        values = dotenv_values(stream=io.StringIO(text))
        for key, value in values.items():
            if value is None:
                continue
            if key not in os.environ:
                os.environ[key] = value
    return selected


def _get_env_value(name: str, legacy_names: list[str], *, strip: bool = True) -> str:
    value = os.getenv(name)
    if value:
        return value.strip() if strip else value
    for legacy in legacy_names:
        legacy_value = os.getenv(legacy)
        if legacy_value:
            return legacy_value.strip() if strip else legacy_value
    return ""


def _parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}: {raw}") from exc


def _parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean for {name}: {raw}")


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def _normalize_token(value: str) -> str:
    if value is None:
        return ""
    invisible = {
        "\ufeff": None,
        "\u200b": None,
        "\u200c": None,
        "\u200d": None,
        "\u2060": None,
    }
    cleaned = value.translate(str.maketrans(invisible))
    return cleaned.strip()


def _looks_like_placeholder(value: str) -> bool:
    text = (value or "").strip().lower()
    if not text:
        return True
    if "<" in text or ">" in text:
        return True
    hints = (
        "token-do-edge",
        "edge-token",
        "your-token",
        "your_store_id",
        "uuid-da-store",
        "seu_token",
        "seu_store_id",
        "changeme",
    )
    return any(hint in text for hint in hints)


def load_settings() -> Settings:
    missing = []
    values = {}
    for name, legacy_names in REQUIRED_ENV.items():
        value = _get_env_value(name, legacy_names, strip=name != "EDGE_TOKEN")
        if not value:
            missing.append(name)
        else:
            values[name] = value

    if missing:
        raise ValueError("Missing required env vars: " + ", ".join(missing))

    logger = logging.getLogger("dalevision-edge-agent")
    store_id = (values["STORE_ID"] or "").strip()
    if _looks_like_placeholder(store_id):
        raise ValueError("STORE_ID inválido. Cole o UUID real da loja gerado no Wizard.")
    try:
        uuid.UUID(store_id)
    except Exception as exc:
        raise ValueError("STORE_ID deve ser um UUID válido.") from exc
    values["STORE_ID"] = store_id

    agent_id = _sanitize_agent_id(
        _get_env_value("AGENT_ID", OPTIONAL_ENV["AGENT_ID"], strip=True)
    )
    if not agent_id:
        agent_id = _default_agent_id(values["STORE_ID"])
        logger.warning(
            "AGENT_ID ausente no .env; usando fallback seguro: %s",
            agent_id,
        )
    values["AGENT_ID"] = agent_id

    token = _normalize_token(values["EDGE_TOKEN"])
    if _looks_like_placeholder(token):
        raise InvalidTokenError("EDGE_TOKEN inválido. Cole o token real do Wizard.")
    values["EDGE_TOKEN"] = token
    prefix = token[:6]
    suffix = token[-4:] if len(token) >= 4 else token
    logger.info(
        "EDGE_TOKEN(len)=%s prefix=%s... suffix=...%s",
        len(token),
        prefix,
        suffix,
    )

    if not token:
        logger.error("EDGE_TOKEN vazio. Refaça o .env copiando do Wizard.")
        raise InvalidTokenError("EDGE_TOKEN vazio.")
    if len(token) < 20:
        logger.warning(
            "EDGE_TOKEN com tamanho incomum (%s). O backend validará a credencial.",
            len(token),
        )

    heartbeat_interval = _parse_int_env(
        "HEARTBEAT_INTERVAL_SECONDS",
        DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    )
    camera_heartbeat_interval = _parse_int_env(
        "CAMERA_HEARTBEAT_INTERVAL_SECONDS",
        DEFAULT_CAMERA_HEARTBEAT_INTERVAL_SECONDS,
    )
    max_active_cameras = _parse_int_env(
        "MAX_ACTIVE_CAMERAS",
        DEFAULT_MAX_ACTIVE_CAMERAS,
    )
    rtsp_describe_enabled = _parse_bool_env("RTSP_DESCRIBE_ENABLED", False)
    update_interval_seconds = _parse_int_env(
        "UPDATE_INTERVAL_SECONDS",
        DEFAULT_UPDATE_INTERVAL_SECONDS,
    )
    # Default profissional: auto-update ligado sem necessidade de toggle local.
    auto_update_enabled = _parse_bool_env("AUTO_UPDATE_ENABLED", True) or _parse_bool_env(
        "ENABLE_AUTO_UPDATE",
        False,
    )
    update_check_url = _get_env_value("UPDATE_CHECK_URL", [], strip=True)

    if heartbeat_interval <= 0:
        raise ValueError("HEARTBEAT_INTERVAL_SECONDS must be > 0")
    if camera_heartbeat_interval <= 0:
        raise ValueError("CAMERA_HEARTBEAT_INTERVAL_SECONDS must be > 0")
    if max_active_cameras <= 0:
        raise ValueError("MAX_ACTIVE_CAMERAS must be > 0")
    if update_interval_seconds <= 0:
        raise ValueError("UPDATE_INTERVAL_SECONDS must be > 0")

    return Settings(
        cloud_base_url=_normalize_base_url(values["CLOUD_BASE_URL"]),
        store_id=values["STORE_ID"],
        edge_token=values["EDGE_TOKEN"],
        agent_id=values["AGENT_ID"],
        heartbeat_interval_seconds=heartbeat_interval,
        camera_heartbeat_interval_seconds=camera_heartbeat_interval,
        max_active_cameras=max_active_cameras,
        rtsp_describe_enabled=rtsp_describe_enabled,
        update_check_url=update_check_url,
        update_interval_seconds=update_interval_seconds,
        auto_update_enabled=auto_update_enabled,
    )
