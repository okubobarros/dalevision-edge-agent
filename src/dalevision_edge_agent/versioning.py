from __future__ import annotations

import importlib.metadata
import os
import re
from pathlib import Path

from .activation import ConfigManager


def _looks_like_version(value: str) -> bool:
    return bool(re.fullmatch(r"v?\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9._-]+)?", str(value or "").strip()))


def _version_from_path(path: Path) -> str:
    for candidate in (path, Path.cwd()):
        name = candidate.name.strip()
        if _looks_like_version(name):
            return name.lstrip("v")
    return ""


def resolve_agent_version() -> str:
    """
    Resolve runtime version with precedence that favors the active installed app:
    1) versioned DALE_APP_DIR / VERSION file
    2) launcher/runtime env version
    3) persisted activation config installed_version
    4) package metadata
    """
    app_dir = str(os.getenv("DALE_APP_DIR") or "").strip()
    if app_dir:
        app_dir_path = Path(app_dir)
        path_version = _version_from_path(app_dir_path)
        if path_version:
            return path_version
        try:
            version_file = app_dir_path / "VERSION"
            version_value = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else ""
            if version_value:
                return version_value
        except Exception:
            pass

    env_version = str(
        os.getenv("DALEVISION_EDGE_AGENT_VERSION")
        or os.getenv("EDGE_AGENT_VERSION")
        or ""
    ).strip()
    if env_version:
        return env_version

    installed_version = str(ConfigManager.from_default().load().get("installed_version") or "").strip()
    if installed_version:
        return installed_version

    try:
        return importlib.metadata.version("dalevision-edge-agent")
    except Exception:
        return "unknown"
