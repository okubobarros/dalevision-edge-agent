from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import time


def _safe_component(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip())
    cleaned = cleaned.strip("-._")
    return cleaned or fallback


def _resolve_local_appdata() -> Path:
    raw = os.getenv("LOCALAPPDATA")
    if raw:
        return Path(raw)
    profile = os.getenv("USERPROFILE")
    if profile:
        return Path(profile) / "AppData" / "Local"
    return Path.cwd()


def _resolve_roaming_appdata() -> Path:
    raw = os.getenv("APPDATA")
    if raw:
        return Path(raw)
    profile = os.getenv("USERPROFILE")
    if profile:
        return Path(profile) / "AppData" / "Roaming"
    return Path.cwd()


@dataclass(frozen=True)
class RuntimePaths:
    app_dir: Path
    config_dir: Path
    log_dir: Path
    cache_dir: Path
    runtime_tmp_root: Path
    runtime_tmp_dir: Path


def resolve_runtime_paths(*, version: str = "unknown") -> RuntimePaths:
    local_root = _resolve_local_appdata() / "DaleVision"
    roaming_root = _resolve_roaming_appdata() / "DaleVision"

    app_dir = Path(os.getenv("DALE_APP_DIR") or (local_root / "app"))
    config_dir = Path(os.getenv("DALE_CONFIG_DIR") or roaming_root)
    log_dir = Path(os.getenv("DALE_LOG_DIR") or (local_root / "logs"))
    cache_dir = Path(os.getenv("DALE_CACHE_DIR") or (local_root / "cache"))
    runtime_tmp_root = cache_dir / "runtime"
    runtime_tmp_dir = runtime_tmp_root / _safe_component(version, "unknown") / str(int(time.time()))

    for path in (app_dir, config_dir, log_dir, cache_dir, runtime_tmp_root, runtime_tmp_dir):
        path.mkdir(parents=True, exist_ok=True)

    return RuntimePaths(
        app_dir=app_dir,
        config_dir=config_dir,
        log_dir=log_dir,
        cache_dir=cache_dir,
        runtime_tmp_root=runtime_tmp_root,
        runtime_tmp_dir=runtime_tmp_dir,
    )


def cleanup_old_runtime_tmp(
    *,
    runtime_tmp_root: Path,
    keep_latest: int = 3,
    max_age_seconds: int = 7 * 24 * 3600,
) -> list[str]:
    if not runtime_tmp_root.exists():
        return []
    now = time.time()
    errors: list[str] = []
    for version_dir in runtime_tmp_root.iterdir():
        if not version_dir.is_dir():
            continue
        candidates = [item for item in version_dir.iterdir() if item.is_dir()]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        for idx, path in enumerate(candidates):
            if idx < keep_latest:
                continue
            try:
                age = now - path.stat().st_mtime
            except Exception:
                age = max_age_seconds + 1
            if age < max_age_seconds:
                continue
            try:
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_file():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                path.rmdir()
            except Exception as exc:
                errors.append(f"{path}: {exc}")
    return errors
