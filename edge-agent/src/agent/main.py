import argparse
import sys
import threading
from datetime import datetime
from pathlib import Path

from .settings import load_settings
from .lifecycle import run_agent


BASE_DIR = Path(__file__).resolve().parents[2]
LOG_FILE = None


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        return False


def _rotate_logs(logs_dir: Path, max_size_bytes: int = 5 * 1024 * 1024, keep: int = 10) -> Path:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "edge-agent.log"
    if log_path.exists() and log_path.stat().st_size > max_size_bytes:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        rotated = logs_dir / f"edge-agent.{ts}.log"
        try:
            log_path.rename(rotated)
        except Exception:
            pass

    rotated_logs = sorted(logs_dir.glob("edge-agent.*.log"), key=lambda p: p.stat().st_mtime)
    if len(rotated_logs) > keep:
        for p in rotated_logs[:-keep]:
            try:
                p.unlink()
            except Exception:
                pass
    return log_path


def _setup_logging():
    global LOG_FILE
    log_path = _rotate_logs(BASE_DIR / "logs")
    LOG_FILE = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = _Tee(sys.stdout, LOG_FILE)
    sys.stderr = _Tee(sys.stderr, LOG_FILE)
    print(f"[DALE Vision] logging to {log_path}")


def _run_setup_server():
    try:
        import uvicorn
    except Exception as e:
        print(f"WARN: uvicorn not available; setup server disabled: {e}")
        return

    try:
        config = uvicorn.Config(
            "src.agent.setup_server:app",
            host="0.0.0.0",
            port=7860,
            log_level="info",
            use_colors=False,
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        print(f"WARN: setup server failed (ignored): {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to agent.yaml")
    parser.add_argument(
        "--heartbeat-only",
        action="store_true",
        help="Run only heartbeat loop (skip vision pipeline)",
    )
    args = parser.parse_args()

    _setup_logging()

    setup_thread = threading.Thread(target=_run_setup_server, daemon=True)
    setup_thread.start()

    settings = load_settings(args.config)
    print(f"[DALE Vision] cloud_base_url = {settings.cloud_base_url}")
    run_agent(settings, heartbeat_only=args.heartbeat_only)


if __name__ == "__main__":
    main()
