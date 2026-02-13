from __future__ import annotations

import argparse
import importlib.metadata
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time

from .env import InvalidTokenError, load_env_from_cwd, load_settings
from .heartbeat import REQUEST_TIMEOUT_SECONDS, send_heartbeat

BACKOFF_SECONDS = [2, 5, 10, 20, 30]
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 5
AUTH_FAILURE_STATUSES = {401, 403}
MAX_CONSECUTIVE_FAILURES = 10
EXIT_CONFIG_ERROR = 2
EXIT_AUTH_ERROR = 3
EXIT_NETWORK_ERROR = 4


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DALE Vision Edge Agent")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Send a single heartbeat and exit",
    )
    return parser.parse_args()


def _run_once(
    *,
    settings,
    url: str,
    version: str,
    logger: logging.Logger,
) -> int:
    ok, status, error = send_heartbeat(
        url=url,
        edge_token=settings.edge_token,
        store_id=settings.store_id,
        agent_id=settings.agent_id,
        version=version,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )

    if status is None:
        message = f"ERRO: Falha de conexao/timeout: {error or 'erro desconhecido'}"
        print(message)
        logger.error("Heartbeat -> %s status=ERROR error=%s", url, error)
        return EXIT_NETWORK_ERROR

    print(f"Heartbeat -> {url} status={status}")

    if ok and status == 201:
        logger.info("Heartbeat -> %s status=%s", url, status)
        return 0

    if status in AUTH_FAILURE_STATUSES:
        message = f"HTTP {status} - Token inválido/expirado"
        print(message)
        logger.error(
            "Auth rejected by backend (status=%s, store_id=%s, cloud_base_url=%s): %s",
            status,
            settings.store_id,
            settings.cloud_base_url,
            error or "auth_failed",
        )
        return EXIT_AUTH_ERROR

    detail = error or f"HTTP {status}"
    message = f"ERRO: Heartbeat falhou: {detail}"
    print(message)
    logger.error(
        "Heartbeat failed once (status=%s, error=%s)",
        status,
        error,
    )
    return 1


def main() -> int:
    args = _parse_args()
    env_path = load_env_from_cwd()
    logger = _setup_logging()

    try:
        settings = load_settings()
    except InvalidTokenError as exc:
        message = f"ERRO: {exc}"
        print(message)
        logger.error(message)
        return EXIT_CONFIG_ERROR
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

    if args.once:
        return _run_once(
            settings=settings,
            url=url,
            version=version,
            logger=logger,
        )

    backoff_index = 0
    consecutive_failures = 0
    last_failure_status = None
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
            consecutive_failures = 0
            last_failure_status = None
            time.sleep(settings.heartbeat_interval_seconds)
            continue

        consecutive_failures += 1
        last_failure_status = status

        if status in AUTH_FAILURE_STATUSES:
            logger.error(
                "Auth rejected by backend (status=%s, store_id=%s, cloud_base_url=%s): %s",
                status,
                settings.store_id,
                settings.cloud_base_url,
                error or "auth_failed",
            )
            print(
                "ERRO: token/store inválido ou ambiente incorreto. "
                "Regenere o .env no Wizard e execute novamente."
            )
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            message = (
                f"ERRO FATAL: {MAX_CONSECUTIVE_FAILURES} falhas consecutivas. "
                f"Ultimo status={last_failure_status if last_failure_status is not None else 'ERROR'}. Encerrando."
            )
            print(message)
            logger.error(message)
            if last_failure_status in AUTH_FAILURE_STATUSES:
                return EXIT_AUTH_ERROR
            if last_failure_status is None:
                return EXIT_NETWORK_ERROR
            return 1

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
