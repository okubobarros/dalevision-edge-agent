from __future__ import annotations

import importlib.metadata
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time

from .env import load_env_from_cwd, load_settings
from .heartbeat import REQUEST_TIMEOUT_SECONDS, send_heartbeat

BACKOFF_SECONDS = [2, 5, 10, 20, 30]
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 5


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("dalevision-edge-agent")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "agent.log"

    handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def _get_version() -> str:
    try:
        return importlib.metadata.version("dalevision-edge-agent")
    except Exception:
        return "unknown"


def main() -> int:
    env_path = load_env_from_cwd()
    logger = _setup_logging()

    try:
        settings = load_settings()
    except ValueError as exc:
        message = f"ERRO: {exc}"
        print(message)
        logger.error(message)
        return 1

    print("Loaded env OK")
    logger.info(
        "Loaded env OK (env_path=%s)",
        env_path if env_path.exists() else "not found",
    )

    url = f"{settings.cloud_base_url}/api/edge/events/"
    version = _get_version()

    backoff_index = 0
    while True:
        ok, status, error = send_heartbeat(
            url=url,
            edge_token=settings.edge_token,
            store_id=settings.store_id,
            agent_id=settings.agent_id,
            version=version,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        )

        if status is None:
            print(f"Heartbeat -> {url} status=ERROR")
        else:
            print(f"Heartbeat -> {url} status={status}")

        if ok:
            logger.info("Heartbeat -> %s status=%s", url, status)
            backoff_index = 0
            time.sleep(settings.heartbeat_interval_seconds)
            continue

        if error:
            logger.warning("Heartbeat failure: %s", error)
        else:
            logger.warning("Heartbeat failure status=%s", status)

        wait_seconds = BACKOFF_SECONDS[min(backoff_index, len(BACKOFF_SECONDS) - 1)]
        print(f"Retry in {wait_seconds}s ...")
        logger.info("Retry in %ss", wait_seconds)
        time.sleep(wait_seconds)
        backoff_index += 1


if __name__ == "__main__":
    raise SystemExit(main())
