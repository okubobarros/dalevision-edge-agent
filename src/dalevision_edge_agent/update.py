from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

import requests
from .cameras import build_auth_headers

UPDATE_POLICY_ENDPOINT = "/api/edge/update-policy/"
UPDATE_REPORT_ENDPOINT = "/api/edge/update-report/"
UPDATE_LOCK_FILE = "update.lock"


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value or "")
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def _is_newer(current: str, incoming: str) -> bool:
    return _version_tuple(incoming) > _version_tuple(current)


def _is_version_supported(current: str, min_supported: str) -> bool:
    if not min_supported:
        return True
    return _version_tuple(current) >= _version_tuple(min_supported)


def _parse_hhmm(value: str) -> tuple[int, int] | None:
    if not value or ":" not in value:
        return None
    try:
        hh, mm = value.split(":", 1)
        h = int(hh)
        m = int(mm)
        if h < 0 or h > 23 or m < 0 or m > 59:
            return None
        return h, m
    except Exception:
        return None


def _is_within_rollout_window(start_local: str, end_local: str, tz_name: str) -> bool:
    parsed_start = _parse_hhmm(start_local)
    parsed_end = _parse_hhmm(end_local)
    if not parsed_start or not parsed_end:
        # invalid policy window: fail-open to avoid bricking updates.
        return True
    try:
        now_local = datetime.now(ZoneInfo(tz_name))
    except Exception:
        now_local = datetime.utcnow()
    now_m = now_local.hour * 60 + now_local.minute
    start_m = parsed_start[0] * 60 + parsed_start[1]
    end_m = parsed_end[0] * 60 + parsed_end[1]

    if start_m == end_m:
        return True
    if start_m < end_m:
        return start_m <= now_m <= end_m
    # overnight window (e.g., 23:00 -> 03:00)
    return now_m >= start_m or now_m <= end_m


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _build_update_report_idempotency_key(payload: dict[str, Any]) -> str:
    """
    Stable key for dedupe on backend update-report.
    Must not include timestamp to remain stable across retries.
    """
    base = {
        "store_id": payload.get("store_id"),
        "agent_id": payload.get("agent_id"),
        "from_version": payload.get("from_version"),
        "to_version": payload.get("to_version"),
        "channel": payload.get("channel"),
        "event": payload.get("event"),
        "status": payload.get("status"),
        "phase": payload.get("phase"),
        "attempt": payload.get("attempt") or 1,
        "reason_code": payload.get("reason_code"),
    }
    raw = json.dumps(base, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def acquire_update_lock(*, logger: logging.Logger, version: str, ttl_seconds: int = 1800) -> tuple[bool, Optional[Path], Optional[str]]:
    updates_dir = Path.cwd() / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    lock_path = updates_dir / UPDATE_LOCK_FILE

    if lock_path.exists():
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
            created_at = int(payload.get("created_at_epoch", 0))
            age = max(0, int(time.time()) - created_at)
            if created_at and age <= ttl_seconds:
                return False, None, "UPDATE_LOCKED"
        except Exception:
            # unknown lock format; treat as stale and replace.
            pass
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            return False, None, "UPDATE_LOCKED"

    payload = {
        "pid": os.getpid(),
        "version": version,
        "created_at_epoch": int(time.time()),
    }
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return True, lock_path, None
    except FileExistsError:
        return False, None, "UPDATE_LOCKED"
    except Exception as exc:
        logger.info("UPD013 lock create failed: %s", exc)
        return False, None, "UPDATE_LOCKED"


def release_update_lock(*, logger: logging.Logger, lock_path: Optional[Path]) -> None:
    if not lock_path:
        return
    try:
        lock_path.unlink(missing_ok=True)
    except Exception as exc:
        logger.info("UPD014 lock cleanup failed: %s", exc)


def check_for_update(
    *,
    logger: logging.Logger,
    current_version: str,
    update_check_url: str,
    auto_update_enabled: bool,
    cloud_base_url: str = "",
    edge_token: str = "",
    store_id: str = "",
    agent_id: str = "",
) -> Optional[dict[str, Any]]:
    payload = None
    if cloud_base_url and edge_token:
        policy_url = f"{cloud_base_url.rstrip('/')}{UPDATE_POLICY_ENDPOINT}"
        headers = build_auth_headers(edge_token)
        if agent_id:
            headers["X-AGENT-ID"] = agent_id
        try:
            response = requests.get(policy_url, headers=headers, timeout=8)
            if response.status_code == 200:
                payload = response.json()
            else:
                logger.info("UPD001 policy check status=%s", response.status_code)
        except Exception as exc:
            logger.info("UPD001 policy check failed: %s", exc)

    if payload is None:
        if not update_check_url:
            return None
        try:
            response = requests.get(update_check_url, timeout=8)
            if response.status_code != 200:
                logger.info("UPD001 update check status=%s", response.status_code)
                return None
            payload = response.json()
        except Exception as exc:
            logger.info("UPD001 update check failed: %s", exc)
            return None

    package = payload.get("package") if isinstance(payload.get("package"), dict) else payload
    latest_version = str(payload.get("target_version") or payload.get("version") or "")
    download_url = str(package.get("url") or payload.get("url") or "")
    checksum = str(package.get("sha256") or payload.get("sha256") or "")
    channel = str(payload.get("channel") or "stable")
    current_min_supported = str(payload.get("current_min_supported") or "").strip()
    rollout_window = payload.get("rollout_window") if isinstance(payload.get("rollout_window"), dict) else {}
    rollout_start_local = str(rollout_window.get("start_local") or "02:00")
    rollout_end_local = str(rollout_window.get("end_local") or "05:00")
    rollout_tz = str(rollout_window.get("timezone") or "America/Sao_Paulo")
    health_gate = payload.get("health_gate") if isinstance(payload.get("health_gate"), dict) else {}
    health_max_boot_seconds = int(health_gate.get("max_boot_seconds") or 120)
    health_require_heartbeat_seconds = int(health_gate.get("require_heartbeat_seconds") or 180)
    health_require_camera_health_count = int(health_gate.get("require_camera_health_count") or 3)
    if not latest_version or not download_url:
        logger.info("UPD002 invalid update payload")
        return None

    if not _is_newer(current_version, latest_version):
        return None

    if not _is_version_supported(current_version, current_min_supported):
        logger.info(
            "UPD015 update blocked unsupported current=%s min_supported=%s",
            current_version,
            current_min_supported,
        )
        return {
            "version": latest_version,
            "url": download_url,
            "sha256": checksum,
            "channel": channel,
            "store_id": store_id,
            "agent_id": agent_id,
            "auto_apply": False,
            "blocked_reason_code": "UNSUPPORTED_VERSION",
            "blocked_phase": "policy_check",
            "blocked_detail": f"current_version={current_version} below min_supported={current_min_supported}",
        }

    if not _is_within_rollout_window(rollout_start_local, rollout_end_local, rollout_tz):
        logger.info(
            "UPD016 update blocked outside window now_tz=%s window=%s-%s",
            rollout_tz,
            rollout_start_local,
            rollout_end_local,
        )
        return {
            "version": latest_version,
            "url": download_url,
            "sha256": checksum,
            "channel": channel,
            "store_id": store_id,
            "agent_id": agent_id,
            "auto_apply": False,
            "blocked_reason_code": "ROLLOUT_WINDOW_CLOSED",
            "blocked_phase": "policy_check",
            "blocked_detail": f"window={rollout_start_local}-{rollout_end_local} tz={rollout_tz}",
        }

    logger.info("UPD010 update available: %s", latest_version)
    if not auto_update_enabled:
        logger.info("UPD011 auto-update disabled; configure AUTO_UPDATE_ENABLED=1")
        return {
            "version": latest_version,
            "url": download_url,
            "sha256": checksum,
            "channel": channel,
            "store_id": store_id,
            "agent_id": agent_id,
            "auto_apply": False,
        }

    return {
        "version": latest_version,
        "url": download_url,
        "sha256": checksum,
        "channel": channel,
        "health_gate": {
            "max_boot_seconds": health_max_boot_seconds,
            "require_heartbeat_seconds": health_require_heartbeat_seconds,
            "require_camera_health_count": health_require_camera_health_count,
        },
        "store_id": store_id,
        "agent_id": agent_id,
        "auto_apply": True,
    }


def send_update_report(
    *,
    logger: logging.Logger,
    cloud_base_url: str,
    edge_token: str,
    payload: dict[str, Any],
) -> tuple[bool, Optional[int], Optional[str]]:
    if not cloud_base_url or not edge_token:
        return False, None, "missing_cloud_base_url_or_edge_token"
    url = f"{cloud_base_url.rstrip('/')}{UPDATE_REPORT_ENDPOINT}"
    headers = build_auth_headers(edge_token)
    payload_to_send = dict(payload)
    if not payload_to_send.get("idempotency_key"):
        payload_to_send["idempotency_key"] = _build_update_report_idempotency_key(payload_to_send)
    try:
        response = requests.post(url, json=payload_to_send, headers=headers, timeout=10)
        ok = 200 <= response.status_code < 300
        if ok:
            return True, response.status_code, None
        detail = None
        try:
            detail = response.json()
        except Exception:
            detail = response.text.strip()[:500] if response.text else None
        return False, response.status_code, f"HTTP {response.status_code}: {detail}"
    except Exception as exc:
        logger.info("UPD050 update report failed: %s", exc)
        return False, None, str(exc)


def download_update(
    *,
    logger: logging.Logger,
    update: dict[str, Any],
) -> Optional[Path]:
    url = update.get("url")
    if not url:
        return None
    updates_dir = Path.cwd() / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)
    target = updates_dir / f"update-{update['version']}"
    try:
        with requests.get(url, stream=True, timeout=15) as response:
            response.raise_for_status()
            with target.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
    except Exception as exc:
        logger.info("UPD020 download failed: %s", exc)
        return None

    checksum = update.get("sha256")
    if checksum:
        actual = _sha256_file(target)
        if actual.lower() != str(checksum).lower():
            logger.info("UPD021 checksum mismatch")
            target.unlink(missing_ok=True)
            return None

    if url.lower().endswith(".zip"):
        import zipfile

        extract_dir = updates_dir / f"update-{update['version']}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "r") as zf:
            zf.extractall(extract_dir)
        exe_candidates = list(extract_dir.rglob("*.exe"))
        if not exe_candidates:
            logger.info("UPD022 zip sem exe")
            return None
        logger.info("UPD022 download ok: %s", exe_candidates[0])
        return exe_candidates[0]

    exe_target = target.with_suffix(".exe")
    target.rename(exe_target)
    logger.info("UPD022 download ok: %s", exe_target)
    return exe_target


def apply_update_if_possible(
    *,
    logger: logging.Logger,
    current_version: str,
    update: dict[str, Any],
    downloaded_path: Path,
) -> bool:
    executable = Path(sys.argv[0])
    if not executable.exists() or executable.suffix.lower() != ".exe":
        logger.info("UPD030 update apply skipped (not exe)")
        return False

    backup = executable.with_suffix(".exe.bak")
    script = executable.parent / "apply_update.bat"
    payload = {
        "from": current_version,
        "to": update["version"],
        "channel": update.get("channel") or "stable",
        "downloaded": str(downloaded_path),
        "health_gate": update.get("health_gate") or {},
    }
    (Path.cwd() / "updates" / "pending.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    script.write_text(
        "\r\n".join(
            [
                "@echo off",
                "setlocal",
                "timeout /t 2 /nobreak >nul",
                f"if exist \"{backup}\" del /f /q \"{backup}\"",
                f"move /y \"{executable}\" \"{backup}\"",
                f"move /y \"{downloaded_path}\" \"{executable}\"",
                f"start \"\" \"{executable}\" --updated-from {current_version}",
                "exit /b 0",
            ]
        ),
        encoding="utf-8",
    )
    try:
        subprocess.Popen(
            ["cmd", "/c", str(script)],
            close_fds=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    except Exception as exc:
        logger.info("UPD031 failed to launch updater: %s", exc)
        return False
    logger.info("UPD032 update applied; restarting")
    return True
