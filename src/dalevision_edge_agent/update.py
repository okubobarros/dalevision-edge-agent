from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Optional

import requests


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", value or "")
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def _is_newer(current: str, incoming: str) -> bool:
    return _version_tuple(incoming) > _version_tuple(current)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def check_for_update(
    *,
    logger: logging.Logger,
    current_version: str,
    update_check_url: str,
    auto_update_enabled: bool,
) -> Optional[dict[str, Any]]:
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

    latest_version = str(payload.get("version") or "")
    download_url = str(payload.get("url") or "")
    checksum = str(payload.get("sha256") or "")
    if not latest_version or not download_url:
        logger.info("UPD002 invalid update payload")
        return None

    if not _is_newer(current_version, latest_version):
        return None

    logger.info("UPD010 update available: %s", latest_version)
    if not auto_update_enabled:
        logger.info("UPD011 auto-update disabled; configure AUTO_UPDATE_ENABLED=1")
        return {
            "version": latest_version,
            "url": download_url,
            "sha256": checksum,
            "auto_apply": False,
        }

    return {
        "version": latest_version,
        "url": download_url,
        "sha256": checksum,
        "auto_apply": True,
    }


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
        "downloaded": str(downloaded_path),
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
                f"start \"\" \"{executable}\" --updated-from {update['version']}",
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
