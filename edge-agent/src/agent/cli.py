import argparse
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = "./config/agent.yaml"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m src.agent")
    sub = parser.add_subparsers(dest="command")

    setup_p = sub.add_parser("setup", help="Start the local setup server")
    setup_p.add_argument("--reload", action="store_true", help="Enable auto-reload")

    run_p = sub.add_parser("run", help="Run the agent")
    run_p.add_argument("--config", default=DEFAULT_CONFIG, help="Path to agent.yaml")
    run_p.add_argument(
        "--heartbeat-only",
        action="store_true",
        help="Run only heartbeat loop (skip vision pipeline)",
    )

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "setup":
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.agent.setup_server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "7860",
        ]
        if args.reload:
            cmd.append("--reload")
        return subprocess.call(cmd, cwd=BASE_DIR)

    if args.command == "run":
        cmd = [
            sys.executable,
            "-m",
            "src.agent.main",
            "--config",
            args.config,
        ]
        if args.heartbeat_only:
            cmd.append("--heartbeat-only")
        return subprocess.call(cmd, cwd=BASE_DIR)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
