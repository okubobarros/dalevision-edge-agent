from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import importlib.metadata
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import threading
import traceback
from typing import Any, Optional

from .cameras import (
    AuthFailureTracker,
    CAMERA_SYNC_INTERVAL_SECONDS,
    build_camera_heartbeat_fields,
    build_rtsp_candidates,
    capture_snapshot_if_possible,
    check_camera_health,
    detect_snapshot_support,
    estimate_snapshot_quality,
    fetch_cameras,
    fetch_roi,
    mask_rtsp_url,
    send_camera_health_event,
    send_vision_metrics_event,
)
from .diagnostics import run_doctor
from .env import InvalidTokenError, describe_env_file, load_env_from_cwd, load_settings
from .heartbeat import REQUEST_TIMEOUT_SECONDS, send_heartbeat
from .onboarding_readiness import (
    build_onboarding_readiness,
    export_onboarding_readiness_report,
)
from .rtsp_test import test_rtsp, test_rtsp_channels
from .scan import build_onboarding_blueprint, run_discovery, run_scan
from .setup_api import serve_setup_api
from .update import (
    apply_update_if_possible,
    acquire_update_lock,
    check_for_update,
    download_update,
    release_update_lock,
    send_update_report,
)
from .vision.worker import VisionWorker

BACKOFF_SECONDS = [2, 5, 10, 20, 30]
LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 5
AUTH_FAILURE_STATUSES = {401, 403}
MAX_CONSECUTIVE_AUTH_FAILURES = 5
MAX_CONSECUTIVE_FAILURES = 10
EXIT_CONFIG_ERROR = 2
EXIT_AUTH_ERROR = 3
EXIT_NETWORK_ERROR = 4
WATCHDOG_DEFAULT_HEARTBEAT_GRACE_SECONDS = 120
WATCHDOG_DEFAULT_CAMERA_HEALTH_GRACE_SECONDS = 180
WATCHDOG_DEFAULT_RESTART_WINDOW_SECONDS = 600
WATCHDOG_DEFAULT_RESTART_MAX = 3
VISION_PROXY_DEFAULT_BUCKET_SECONDS = 30
VISION_PROXY_DEFAULT_BUCKET_SECONDS = 30


def _candidate_install_roots() -> list[Path]:
    roots: list[Path] = []
    cwd = Path.cwd()
    roots.append(cwd)
    try:
        exe_dir = Path(sys.executable).resolve().parent
        if exe_dir not in roots:
            roots.append(exe_dir)
    except Exception:
        pass
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(str(meipass))
        if mp not in roots:
            roots.append(mp)
    return roots


def _resolve_install_service_script() -> tuple[Path | None, list[Path], Path]:
    checked: list[Path] = []
    for root in _candidate_install_roots():
        for rel in (
            "install-service.ps1",
            "install_service.ps1",
            "scripts/install-service.ps1",
            "scripts/install_service.ps1",
        ):
            candidate = root / rel
            checked.append(candidate)
            if candidate.exists():
                install_root = candidate.parent.parent if candidate.parent.name.lower() == "scripts" else root
                return candidate, checked, install_root
    return None, checked, Path.cwd()


def _resolve_run_agent_cmd() -> tuple[Path | None, list[Path]]:
    checked: list[Path] = []
    for root in _candidate_install_roots():
        candidate = root / "run_agent.cmd"
        checked.append(candidate)
        if candidate.exists():
            return candidate, checked
    return None, checked


def _resolve_agent_executable() -> tuple[Path | None, list[Path]]:
    checked: list[Path] = []
    names = (
        "dalevision-edge-agent.exe",
        "DaleVisionEdge.exe",
        "DaleVision Edge Agent.exe",
    )
    for root in _candidate_install_roots():
        for name in names:
            candidate = root / name
            checked.append(candidate)
            if candidate.exists():
                return candidate, checked
    return None, checked


def _is_windows_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _create_startup_shortcut(*, logger: logging.Logger) -> tuple[bool, str]:
    run_cmd, checked = _resolve_run_agent_cmd()
    if run_cmd is None:
        searched = ", ".join(str(p) for p in checked)
        return False, f"Fallback autostart indisponivel: run_agent.cmd nao encontrado. Procurado em: {searched}"

    appdata = os.getenv("APPDATA") or ""
    if not appdata:
        return False, "Fallback autostart indisponivel: APPDATA nao definido."
    startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    link_path = startup_dir / "DaleVision Edge Agent.lnk"

    install_root = run_cmd.resolve().parent
    launcher_script = install_root / "scripts" / "internal" / "Start_DaleVision_Agent.ps1"
    if not launcher_script.exists():
        return False, f"Fallback autostart indisponivel: launcher nao encontrado em {launcher_script}"

    powershell = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    if not powershell.exists():
        return False, f"Fallback autostart indisponivel: powershell nao encontrado em {powershell}"

    target = str(powershell.resolve())
    workdir = str(install_root)
    icon_path = install_root / "dalevision-edge-agent.exe"
    icon = str(icon_path if icon_path.exists() else powershell.resolve())
    args = (
        f'-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass '
        f'-File "{launcher_script}" -InstallDir "{install_root}"'
    )

    def _ps_quote(value: str) -> str:
        return value.replace("'", "''")

    script = (
        f"$ws=New-Object -ComObject WScript.Shell;"
        f"$sc=$ws.CreateShortcut('{_ps_quote(str(link_path))}');"
        f"$sc.TargetPath='{_ps_quote(target)}';"
        f"$sc.Arguments='{_ps_quote(args)}';"
        f"$sc.WorkingDirectory='{_ps_quote(workdir)}';"
        f"$sc.IconLocation='{_ps_quote(icon)},0';"
        "$sc.Save();"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "erro desconhecido").strip()
        logger.warning("Startup shortcut create failed: %s", detail)
        return False, f"Fallback autostart falhou: {detail}"
    if not link_path.exists():
        return False, f"Fallback autostart falhou: atalho nao encontrado em {link_path}"
    logger.info("Startup shortcut ready at %s", link_path)
    return True, f"Fallback autostart configurado em: {link_path}"


def _create_logon_scheduled_task(*, logger: logging.Logger) -> tuple[bool, str]:
    agent_exe, checked = _resolve_agent_executable()
    run_target: Optional[Path] = agent_exe
    if run_target is None:
        run_cmd, checked_cmd = _resolve_run_agent_cmd()
        checked.extend(checked_cmd)
        run_target = run_cmd
    if run_target is None:
        searched = ", ".join(str(p) for p in checked)
        return False, (
            "Fallback schtasks indisponivel: executavel/run_agent.cmd nao encontrado. "
            f"Procurado em: {searched}"
        )

    install_dir = run_target.parent
    task_name = "DaleVisionEdgeAgentUser"
    run_target_escaped = str(run_target).replace('"', '""')
    install_dir_escaped = str(install_dir).replace('"', '""')
    task_cmd = f'cmd.exe /c "cd /d ""{install_dir_escaped}"" && ""{run_target_escaped}"""'
    create_cmd = [
        "schtasks",
        "/Create",
        "/SC",
        "ONLOGON",
        "/TN",
        task_name,
        "/TR",
        task_cmd,
        "/F",
    ]
    result = subprocess.run(create_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "erro desconhecido").strip()
        logger.warning("Scheduled task fallback failed: %s", detail)
        return False, f"Fallback schtasks falhou: {detail}"
    logger.info(
        "Scheduled task fallback ready task=%s install_dir=%s target=%s",
        task_name,
        install_dir,
        run_target,
    )
    return True, f"Fallback schtasks configurado: {task_name} (logon do usuario atual)"


def _run_install_service_command(*, logger: logging.Logger) -> int:
    script_path, checked, install_root = _resolve_install_service_script()
    checked_text = ", ".join(str(p) for p in checked)
    if script_path is None:
        print("Nao foi possivel localizar o instalador de servico.")
        print("Verifique se a pasta scripts foi extraida junto do agente.")
        print(f"Caminhos verificados: {checked_text}")
        logger.warning("install-service script missing; checked=%s", checked_text)
        answer = "s"
        if sys.stdin is not None and sys.stdin.isatty():
            answer = input("Deseja criar fallback de autostart via Scheduled Task no logon? (s/N): ").strip().lower()
        if answer in {"s", "sim", "y", "yes"}:
            ok, msg = _create_logon_scheduled_task(logger=logger)
            print(msg)
            if ok:
                return 0
            ok_startup, msg_startup = _create_startup_shortcut(logger=logger)
            print(msg_startup)
            return 0 if ok_startup else 1
        if not _is_windows_admin():
            ok, msg = _create_startup_shortcut(logger=logger)
            print(msg)
            return 0 if ok else 1
        return 1

    if not _is_windows_admin():
        print("Permissao de administrador nao detectada.")
        print("Aplicando fallback de autostart no Startup do usuario atual...")
        ok, msg = _create_startup_shortcut(logger=logger)
        print(msg)
        return 0 if ok else 1

    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path), "-InstallDir", str(install_root)],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        detail = result.stderr.strip() or "falha ao instalar servico."
        print(detail)
        logger.error("install-service command failed rc=%s detail=%s", result.returncode, detail)
        return result.returncode or 1
    return 0


def _rollback_update_if_needed(updated_from: str, logger: logging.Logger) -> None:
    backup = Path(sys.argv[0]).with_suffix(".exe.bak")
    executable = Path(sys.argv[0])
    if not backup.exists():
        return
    try:
        if executable.exists():
            executable.unlink(missing_ok=True)
        backup.replace(executable)
        logger.error("UPD050 rollback aplicado (from=%s)", updated_from)
    except Exception as exc:
        logger.error("UPD051 rollback falhou: %s", exc)


def _load_pending_update_payload() -> dict[str, Any]:
    pending = Path.cwd() / "updates" / "pending.json"
    if not pending.exists():
        return {}
    try:
        return json.loads(pending.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _run_post_update_health_gate(
    *,
    logger: logging.Logger,
    settings,
    version: str,
    pending_payload: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """
    v1 health gate after update:
    - require a successful heartbeat within configured timeout.
    Camera-health threshold is recorded as pending when not yet measured in this stage.
    """
    gate = pending_payload.get("health_gate") if isinstance(pending_payload.get("health_gate"), dict) else {}
    max_boot_seconds = int(gate.get("max_boot_seconds") or 120)
    require_heartbeat_seconds = int(gate.get("require_heartbeat_seconds") or 180)
    require_camera_health_count = int(gate.get("require_camera_health_count") or 3)
    deadline = time.time() + max(5, min(max_boot_seconds, require_heartbeat_seconds))
    heartbeat_ok = False
    last_status = None
    last_error = None
    url = f"{settings.cloud_base_url}/api/edge/events/"

    while time.time() < deadline:
        ok, status_code, error = send_heartbeat(
            url=url,
            edge_token=settings.edge_token,
            store_id=settings.store_id,
            agent_id=settings.agent_id,
            version=version,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            extra_data={},
        )
        last_status = status_code
        last_error = error
        if ok:
            heartbeat_ok = True
            break
        time.sleep(3)

    meta = {
        "source": "boot_after_update",
        "health_gate": {
            "heartbeat_ok": heartbeat_ok,
            "last_heartbeat_status": last_status,
            "last_heartbeat_error": last_error,
            "require_camera_health_count": require_camera_health_count,
            "camera_health_gate_evaluated": False,
        },
    }
    if not heartbeat_ok:
        logger.error(
            "UPD041 health gate failed heartbeat status=%s error=%s",
            last_status,
            last_error,
        )
        return False, meta
    return True, meta


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("dalevision-edge-agent")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_root = os.getenv("DALE_LOG_DIR")
    if log_root:
        log_dir = Path(log_root)
    else:
        program_data = os.getenv("PROGRAMDATA")
        if program_data:
            log_dir = Path(program_data) / "DaleVision" / "logs"
        else:
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
    parser.add_argument(
        "--updated-from",
        dest="updated_from",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--smoke",
        type=int,
        default=0,
        help="Run smoke test for N seconds (heartbeat + camera_health from CAMERAS_JSON) and exit",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run edge agent")

    diag_parser = subparsers.add_parser("diagnostics", help="Run network diagnostics")
    diag_parser.add_argument(
        "--nvr-ip",
        dest="nvr_ip",
        help="Optional NVR IP for segmentation check",
    )
    diag_parser.add_argument(
        "--share",
        action="store_true",
        help="Generate a zip with logs and diagnostics",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Run diagnostics (doctor)")
    doctor_parser.add_argument("--nvr-ip", dest="nvr_ip", help="Optional NVR IP")
    doctor_parser.add_argument("--share", action="store_true", help="Generate share ZIP")

    scan_parser = subparsers.add_parser("scan", help="Scan local network for NVRs")
    scan_parser.add_argument("--mode", default="nvr", choices=["nvr"])
    scan_parser.add_argument("--range", default="auto", choices=["auto"])

    onboarding_parser = subparsers.add_parser(
        "onboarding-blueprint",
        help="Build onboarding payload with camera limit and indicator catalog",
    )
    onboarding_parser.add_argument("--plan", default="trial")
    onboarding_parser.add_argument("--json", action="store_true")

    onboarding_readiness_parser = subparsers.add_parser(
        "onboarding-readiness",
        help="Validate onboarding readiness (env, config and optional scan)",
    )
    onboarding_readiness_parser.add_argument("--plan", default="trial")
    onboarding_readiness_parser.add_argument("--scan", action="store_true")
    onboarding_readiness_parser.add_argument("--json", action="store_true")
    onboarding_readiness_parser.add_argument(
        "--export-json",
        dest="export_json",
        default="",
        help="Optional output path for readiness JSON report",
    )
    onboarding_readiness_parser.add_argument(
        "--export-md",
        dest="export_md",
        default="",
        help="Optional output path for readiness Markdown report",
    )

    setup_api_parser = subparsers.add_parser("setup-api", help="Run local setup API for onboarding")
    setup_api_parser.add_argument("--host", default="127.0.0.1")
    setup_api_parser.add_argument("--port", type=int, default=8787)

    rtsp_parser = subparsers.add_parser("test-rtsp", help="Test RTSP connection")
    rtsp_parser.add_argument("--ip", required=True)
    rtsp_parser.add_argument("--user", required=True)
    rtsp_parser.add_argument("--pass", dest="password", required=True)
    rtsp_parser.add_argument("--channel", type=int, default=1)
    rtsp_parser.add_argument("--subtype", type=int, default=1)
    rtsp_parser.add_argument("--timeout", type=int, default=5)
    rtsp_parser.add_argument("--scan-channels", action="store_true")

    parser.set_defaults(command="run")
    return parser.parse_args()


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean for {name}: {raw}")


def _parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}: {raw}") from exc


def _parse_cameras_json(
    raw: str,
    logger: logging.Logger,
) -> tuple[list[dict[str, Any]], str | None]:
    if not raw or raw.strip() == "":
        return [], None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"CAMERAS_JSON invalid JSON: {exc}"
    if not isinstance(payload, list):
        return [], "CAMERAS_JSON must be a JSON array"

    cameras: list[dict[str, Any]] = []
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            return [], f"CAMERAS_JSON item {idx} must be an object"
        camera_id = str(item.get("id") or item.get("camera_id") or "").strip()
        rtsp_url = str(item.get("rtsp_url") or "").strip()
        ip = str(item.get("ip") or item.get("host") or "").strip()
        has_connection_hint = bool(rtsp_url or ip)
        if not camera_id or not has_connection_hint:
            return [], f"CAMERAS_JSON item {idx} missing id and (rtsp_url or ip)"

        normalized = dict(item)
        normalized["id"] = camera_id
        normalized["camera_id"] = camera_id
        normalized["name"] = str(item.get("name") or "").strip()
        if rtsp_url:
            normalized["rtsp_url"] = rtsp_url
        if ip:
            normalized["ip"] = ip
        cameras.append(normalized)

    if not cameras:
        logger.warning("CAMERAS_JSON parsed but contained no valid cameras")
    return cameras, None


def _resolve_camera_source_mode() -> str:
    """
    Source-of-truth selector for cameras.

    - api_first (default): backend API is the primary source; CAMERAS_JSON is fallback.
    - local_only: CAMERAS_JSON only (no remote camera sync).
    """
    raw = (os.getenv("CAMERA_SOURCE_MODE") or "").strip().lower()
    if raw in {"", "api_first"}:
        return "api_first"
    if raw in {"local_only", "env_only"}:
        return "local_only"
    raise ValueError(
        f"Invalid CAMERA_SOURCE_MODE: {raw}. Use 'api_first' or 'local_only'."
    )


def _restart_self(
    *,
    reason: str,
    logger: logging.Logger,
    restart_enabled: bool,
    restart_max: int,
    restart_window_seconds: int,
) -> None:
    if not restart_enabled:
        logger.warning("[WATCHDOG] restart disabled (reason=%s)", reason)
        return

    now = int(time.time())
    raw_count = os.getenv("EDGE_RESTART_COUNT") or "0"
    raw_last = os.getenv("EDGE_RESTART_LAST_TS") or "0"
    try:
        count = int(raw_count)
    except Exception:
        count = 0
    try:
        last_ts = int(raw_last)
    except Exception:
        last_ts = 0

    if last_ts and now - last_ts > restart_window_seconds:
        count = 0

    if count >= restart_max:
        logger.error(
            "[WATCHDOG] restart limit reached count=%s window=%ss reason=%s",
            count,
            restart_window_seconds,
            reason,
        )
        return

    count += 1
    os.environ["EDGE_RESTART_COUNT"] = str(count)
    os.environ["EDGE_RESTART_LAST_TS"] = str(now)

    argv = sys.argv[:]
    if not argv:
        argv = [sys.executable, "-m", "dalevision_edge_agent.main"]
    elif argv[0].endswith(".py"):
        argv = [sys.executable] + argv

    logger.error("[WATCHDOG] restarting self reason=%s count=%s argv=%s", reason, count, argv)
    try:
        subprocess.Popen(argv, cwd=os.getcwd())
    except Exception as exc:
        logger.error("[WATCHDOG] restart failed: %s", exc)
        return
    os._exit(1)


def _watchdog_loop(
    *,
    logger: logging.Logger,
    state: dict[str, Any],
    lock: threading.Lock,
    heartbeat_grace_seconds: int,
    camera_health_grace_seconds: int,
    restart_enabled: bool,
    restart_max: int,
    restart_window_seconds: int,
) -> None:
    while True:
        time.sleep(5)
        now = time.time()
        with lock:
            hb_ok_at = state.get("last_heartbeat_ok_at")
            hb_status = state.get("last_heartbeat_status")
            hb_error = state.get("last_heartbeat_error")
            ch_ok_at = state.get("last_camera_health_ok_at")
            has_cameras = bool(state.get("has_cameras"))
            auth_fail = hb_status in AUTH_FAILURE_STATUSES

        if hb_ok_at and now - hb_ok_at > heartbeat_grace_seconds:
            if auth_fail:
                logger.warning(
                    "[WATCHDOG] heartbeat stale but auth failed (status=%s error=%s)",
                    hb_status,
                    hb_error,
                )
            else:
                _restart_self(
                    reason="heartbeat_stale",
                    logger=logger,
                    restart_enabled=restart_enabled,
                    restart_max=restart_max,
                    restart_window_seconds=restart_window_seconds,
                )
                continue

        if has_cameras and ch_ok_at and now - ch_ok_at > camera_health_grace_seconds:
            _restart_self(
                reason="camera_health_stale",
                logger=logger,
                restart_enabled=restart_enabled,
                restart_max=restart_max,
                restart_window_seconds=restart_window_seconds,
            )


def _auto_set_vision_model_path(logger: logging.Logger) -> None:
    if os.getenv("VISION_MODEL_PATH"):
        return
    model_path = Path("C:\\ProgramData\\DaleVision\\models\\yolov8n.pt")
    if model_path.exists():
        os.environ["VISION_MODEL_PATH"] = str(model_path)
        logger.info("VISION_MODEL_PATH auto-set to %s", model_path)
        return
    logger.warning("modelo nao encontrado localmente; pode baixar da internet.")


def _normalize_vision_model_path(logger: logging.Logger) -> None:
    raw = os.getenv("VISION_MODEL_PATH")
    if raw is None:
        return
    current = raw.strip()
    if not current:
        return

    normalized = current.strip().strip('"').strip("'")
    markdown_match = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", normalized)
    if markdown_match:
        label = markdown_match.group(1).strip()
        link = markdown_match.group(2).strip()
        if label:
            normalized = label
        elif link:
            normalized = Path(link.split("?", 1)[0]).name

    lower = normalized.lower()
    if lower.startswith(("http://", "https://")):
        normalized = Path(normalized.split("?", 1)[0]).name

    if not normalized:
        return

    if normalized != current:
        os.environ["VISION_MODEL_PATH"] = normalized
        logger.warning(
            "VISION_MODEL_PATH ajustado automaticamente de '%s' para '%s'",
            current,
            normalized,
        )


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
        message = f"⚠️ Sem internet ou timeout: {error or 'erro desconhecido'}"
        print(message)
        print("Proximo passo: verifique internet e tente novamente.")
        logger.error("Heartbeat -> %s status=ERROR error=%s", url, error)
        return EXIT_NETWORK_ERROR

    print(f"Heartbeat -> {url} status={status}")

    if ok and status == 201:
        print("✅ Conectado. Volte ao site e clique em 'Adicionar câmera'.")
        logger.info("Heartbeat -> %s status=%s", url, status)
        return 0

    if status in AUTH_FAILURE_STATUSES:
        message = f"❌ Token inválido/expirado (HTTP {status})"
        print(message)
        print("Proximo passo: gere um novo token no Wizard e atualize o .env.")
        logger.error(
            "Auth rejected by backend (status=%s, store_id=%s, cloud_base_url=%s): %s",
            status,
            settings.store_id,
            settings.cloud_base_url,
            error or "auth_failed",
        )
        return EXIT_AUTH_ERROR

    detail = error or f"HTTP {status}"
    message = f"❌ Falha ao conectar: {detail}"
    print(message)
    print("Proximo passo: verifique internet e o CLOUD_BASE_URL.")
    logger.error(
        "Heartbeat failed once (status=%s, error=%s)",
        status,
        error,
    )
    return 1


def _is_camera_active(camera: dict[str, Any]) -> bool:
    for key in ("active", "is_active", "enabled", "isEnabled"):
        if key in camera:
            return bool(camera.get(key))
    return True


def _normalize_local_health(raw_health: dict[str, Any]) -> dict[str, Any]:
    error_raw = str(raw_health.get("error") or "").strip().lower()
    status_raw = str(raw_health.get("status") or "").strip().lower()
    latency_ms = raw_health.get("latency_ms")

    status = "online" if status_raw in {"online", "degraded"} and not error_raw else "error"
    if status == "online":
        error = None
    elif "unauthorized" in error_raw or "auth" in error_raw or "401" in error_raw or "403" in error_raw:
        error = "auth_failed"
    elif error_raw in {"timeout", "timed out"} or "timeout" in error_raw:
        error = "rtsp_timeout"
    else:
        error = "connect_failed"

    return {
        "camera_id": raw_health.get("camera_id"),
        "status": status,
        "latency_ms": latency_ms if isinstance(latency_ms, int) else None,
        "error": error,
        "checked_at": raw_health.get("checked_at"),
    }


def _run_camera_health_once(
    *,
    cloud_base_url: str,
    edge_token: str,
    store_id: str,
    agent_id: str,
    cameras: list[dict[str, Any]],
    logger: logging.Logger,
    state_store: Optional[dict[str, dict[str, Any]]] = None,
    watchdog_state: Optional[dict[str, Any]] = None,
    watchdog_lock: Optional[threading.Lock] = None,
) -> int:
    posted = 0
    cycle_started_at = time.time()
    logger.info("[CAMERA_HEALTH] cycle_start cameras=%s", len(cameras))
    for camera in cameras:
        camera_id = str(camera.get("id") or camera.get("camera_id") or "").strip()
        rtsp_url = str(camera.get("rtsp_url") or "").strip()
        if not camera_id or not rtsp_url:
            logger.warning("[CAMERA_HEALTH] skipping invalid camera camera_id=%s", camera_id or "missing")
            continue
        raw_health = check_camera_health(
            {"id": camera_id, "rtsp_url": rtsp_url},
            timeout_seconds=6,
            perform_describe=False,
            rtsp_url_override=rtsp_url,
        )
        raw_health["camera_id"] = camera_id
        health = _normalize_local_health(raw_health)
        logger.info(
            "[CAMERA_HEALTH] camera_id=%s status=%s latency_ms=%s error=%s",
            camera_id,
            health.get("status"),
            health.get("latency_ms"),
            health.get("error"),
        )
        ok_evt, status_evt, err_evt = send_camera_health_event(
            cloud_base_url=cloud_base_url,
            edge_token=edge_token,
            store_id=store_id,
            agent_id=agent_id,
            camera_health=health,
            timeout_seconds=10,
            logger=logger,
        )
        logger.info(
            "[CAMERA_HEALTH] POST camera_id=%s status_code=%s ok=%s error=%s",
            camera_id,
            status_evt,
            ok_evt,
            err_evt,
        )
        if ok_evt:
            posted += 1
        if state_store is not None:
            state_store[camera_id] = {
                "status": "online" if health.get("status") == "online" else "offline",
                "roi_version": "local",
                "error": health.get("error"),
                "latency_ms": health.get("latency_ms"),
            }
    elapsed_ms = int((time.time() - cycle_started_at) * 1000)
    logger.info(
        "[CAMERA_HEALTH] cycle_end cameras=%s posted=%s elapsed_ms=%s",
        len(cameras),
        posted,
        elapsed_ms,
    )
    if posted > 0 and watchdog_state is not None and watchdog_lock is not None:
        with watchdog_lock:
            watchdog_state["last_camera_health_ok_at"] = time.time()
            watchdog_state["has_cameras"] = True
    return posted


def _camera_health_loop(
    *,
    cloud_base_url: str,
    edge_token: str,
    store_id: str,
    agent_id: str,
    cameras: list[dict[str, Any]],
    interval_seconds: int,
    logger: logging.Logger,
    state_store: Optional[dict[str, dict[str, Any]]] = None,
    watchdog_state: Optional[dict[str, Any]] = None,
    watchdog_lock: Optional[threading.Lock] = None,
) -> None:
    while True:
        try:
            _run_camera_health_once(
                cloud_base_url=cloud_base_url,
                edge_token=edge_token,
                store_id=store_id,
                agent_id=agent_id,
                cameras=cameras,
                logger=logger,
                state_store=state_store,
                watchdog_state=watchdog_state,
                watchdog_lock=watchdog_lock,
            )
        except Exception as exc:
            logger.exception("[CAMERA_HEALTH] loop error: %s", exc)
        time.sleep(interval_seconds)


def _run_smoke(
    *,
    seconds: int,
    settings,
    url: str,
    version: str,
    cameras: list[dict[str, Any]],
    logger: logging.Logger,
) -> int:
    logger.info("[SMOKE] starting duration_seconds=%s cameras=%s", seconds, len(cameras))
    hb_ok, hb_status, hb_error = send_heartbeat(
        url=url,
        edge_token=settings.edge_token,
        store_id=settings.store_id,
        agent_id=settings.agent_id,
        version=version,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
    )
    print(f"SMOKE heartbeat status={hb_status} ok={hb_ok} error={hb_error}")
    if not cameras:
        print("SMOKE erro: CAMERAS_JSON vazio ou invalido.")
        return 1

    posted = _run_camera_health_once(
        cloud_base_url=settings.cloud_base_url,
        edge_token=settings.edge_token,
        store_id=settings.store_id,
        agent_id=settings.agent_id,
        cameras=cameras,
        logger=logger,
    )
    print(f"OK: posted {posted} camera_health events")
    all_ok = bool(hb_ok) and posted == len(cameras)
    print(
        "SMOKE summary: "
        f"heartbeat_ok={hb_ok} heartbeat_status={hb_status} camera_health_posted={posted}/{len(cameras)} result={'OK' if all_ok else 'FAIL'}"
    )
    if seconds > 1:
        sleep_for = min(seconds, 5)
        time.sleep(sleep_for)
    return 0 if all_ok else 1


def _floor_bucket(ts: float, bucket_seconds: int) -> tuple[str, str]:
    bucket_start = int(ts // bucket_seconds) * bucket_seconds
    start_dt = datetime.fromtimestamp(bucket_start, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(bucket_start + bucket_seconds, tz=timezone.utc)
    return (
        start_dt.isoformat().replace("+00:00", "Z"),
        end_dt.isoformat().replace("+00:00", "Z"),
    )


def main() -> int:
    args = _parse_args()
    env_path = load_env_from_cwd()
    logger = _setup_logging()
    env_meta = describe_env_file(env_path)
    logger.info(
        "ENV file path=%s cwd=%s exists=%s mtime_utc=%s size_bytes=%s sha256=%s",
        env_meta.get("path"),
        Path.cwd(),
        env_meta.get("exists"),
        env_meta.get("mtime_utc"),
        env_meta.get("size_bytes"),
        env_meta.get("sha256"),
    )
    if env_meta.get("error"):
        logger.warning("ENV file metadata error: %s", env_meta.get("error"))

    if len(sys.argv) == 1:
        while True:
            print("DALE Vision Edge Agent")
            print("1) Conectar (Teste rapido)")
            print("2) Iniciar monitoramento (rodar sempre)")
            print("3) Instalar como servico (requer admin)")
            print("4) Abrir dashboard")
            choice = input("Escolha uma opcao (1-4): ").strip()
            if choice == "1":
                args.command = "run"
                args.once = True
                break
            if choice == "2":
                args.command = "run"
                break
            if choice == "3":
                _run_install_service_command(logger=logger)
                print("")
                continue
            if choice == "4":
                try:
                    url = os.getenv("DASHBOARD_URL") or "https://app.dalevision.com/app/cameras?onboarding=true"
                    os.startfile(url)
                except Exception:
                    print("Nao foi possivel abrir o navegador.")
                return 0
            print("Opcao invalida.")

    if args.command in {"diagnostics", "doctor"}:
        cloud_base_url = os.getenv("CLOUD_BASE_URL") or os.getenv("DALE_CLOUD_BASE_URL") or ""
        run_doctor(
            cloud_base_url=cloud_base_url,
            logger=logger,
            nvr_ip=args.nvr_ip,
            share=bool(args.share),
            store_id=os.getenv("STORE_ID") or os.getenv("DALE_STORE_ID"),
            edge_token=os.getenv("EDGE_TOKEN") or os.getenv("DALE_EDGE_TOKEN"),
        )
        return 0

    if args.command == "install-service":
        return _run_install_service_command(logger=logger)

    if args.command == "scan":
        results = run_discovery(logger=logger)
        print("Scan results:")
        for item in results:
            print(
                f"- {item['ip']} ports={item['ports']} confidence={item['confidence']} "
                f"status={item.get('status')} reason={item.get('reason_code')}"
            )
        return 0

    if args.command == "onboarding-blueprint":
        raw_scan_results = run_scan(logger=logger)
        payload = build_onboarding_blueprint(raw_scan_results, plan_code=args.plan)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"Plano={payload['plan_code']} limite={payload['camera_limit']} "
                f"candidatas={len(payload['candidates'])}"
            )
            print("Cameras recomendadas:")
            for ip in payload["selection_guidance"]["recommended_camera_ips"]:
                print(f"- {ip}")
            print("Indicadores disponiveis:")
            for indicator in payload["indicators"]:
                required_label = "required" if indicator.get("required") else "optional"
                print(
                    f"- {indicator['key']} ({indicator['roi_shape']}, {required_label})"
                )
        return 0

    if args.command == "onboarding-readiness":
        payload = build_onboarding_readiness(
            plan_code=args.plan,
            include_scan=bool(args.scan),
            discovery_provider=lambda: run_scan(logger=logger),
        )
        output_paths = export_onboarding_readiness_report(
            payload,
            export_json_path=str(args.export_json or ""),
            export_markdown_path=str(args.export_md or ""),
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            summary = payload.get("summary") or {}
            print(
                f"status={payload.get('status')} checks_ok={summary.get('checks_ok')} "
                f"warnings={summary.get('checks_warning')} fails={summary.get('checks_fail')}"
            )
            if summary.get("missing_required_env"):
                print("Missing env:")
                for key in summary.get("missing_required_env") or []:
                    print(f"- {key}")
            plan = payload.get("plan") or {}
            print(
                f"Plan={plan.get('plan_code')} camera_limit={plan.get('camera_limit')}"
            )
            discovery = payload.get("discovery") or {}
            if discovery.get("executed"):
                print(
                    f"Scan candidates={discovery.get('detected_count')} "
                    f"recommended={discovery.get('recommended_count')}"
                )
            if output_paths:
                print("Reports exported:")
                if output_paths.get("json"):
                    print(f"- json: {output_paths['json']}")
                if output_paths.get("markdown"):
                    print(f"- markdown: {output_paths['markdown']}")
        return 0

    if args.command == "setup-api":
        serve_setup_api(
            host=args.host,
            port=int(args.port),
            discovery_provider=lambda: run_scan(logger=logger),
            logger=logger,
        )
        return 0

    if args.command == "test-rtsp":
        if args.scan_channels:
            result = test_rtsp_channels(
                ip=args.ip,
                user=args.user,
                password=args.password,
                channels=list(range(1, 17)),
                subtype=args.subtype,
                timeout_seconds=args.timeout,
                logger=logger,
            )
            print("Resultados por canal:")
            for item in result["results"]:
                status = "OK" if item["ok"] else "FAIL"
                print(f"- canal {item['channel']}: {status} {item.get('message') or ''}".strip())
        else:
            result = test_rtsp(
                ip=args.ip,
                user=args.user,
                password=args.password,
                channel=args.channel,
                subtype=args.subtype,
                timeout_seconds=args.timeout,
                logger=logger,
            )
            if result.get("ok"):
                latency = result.get("health", {}).get("latency_ms")
                fps = result.get("fps")
                print(f"✅ RTSP OK canal {args.channel}")
                print(f"latency_ms={latency if latency is not None else 'N/A'} fps={fps if fps else 'N/A'}")
            else:
                print(f"❌ RTSP FAIL: {result.get('message')}")
        return 0

    try:
        settings = load_settings()
    except InvalidTokenError as exc:
        message = f"ERRO: {exc}"
        print(message)
        logger.error(message)
        if args.updated_from:
            _rollback_update_if_needed(args.updated_from, logger)
        return EXIT_CONFIG_ERROR
    except ValueError as exc:
        message = f"ERRO: {exc}"
        print(message)
        logger.error(message)
        if args.updated_from:
            _rollback_update_if_needed(args.updated_from, logger)
        return 1

    print("Loaded env OK")
    logger.info(
        "Loaded env OK (env_path=%s)",
        env_path if env_path.exists() else "not found",
    )
    logger.info("Logs at %s", next(iter(logger.handlers)).baseFilename)

    if args.updated_from:
        pending_payload = _load_pending_update_payload()
        to_version = str(pending_payload.get("to") or "")
        channel = str(pending_payload.get("channel") or "stable")
        update_attempt = int(pending_payload.get("attempt") or 1)
        health_ok, health_meta = _run_post_update_health_gate(
            logger=logger,
            settings=settings,
            version=_get_version(),
            pending_payload=pending_payload,
        )
        if not health_ok:
            send_update_report(
                logger=logger,
                cloud_base_url=settings.cloud_base_url,
                edge_token=settings.edge_token,
                payload={
                    "store_id": settings.store_id,
                    "agent_id": settings.agent_id,
                    "from_version": args.updated_from,
                    "to_version": to_version or _get_version(),
                    "channel": channel,
                    "status": "failed",
                    "phase": "health_check",
                    "event": "edge_update_failed",
                    "attempt": update_attempt,
                    "reason_code": "HEALTH_GATE_TIMEOUT",
                    "meta": health_meta,
                },
            )
            _rollback_update_if_needed(args.updated_from, logger)
            return EXIT_NETWORK_ERROR
        send_update_report(
            logger=logger,
            cloud_base_url=settings.cloud_base_url,
            edge_token=settings.edge_token,
            payload={
                "store_id": settings.store_id,
                "agent_id": settings.agent_id,
                "from_version": args.updated_from,
                "to_version": to_version or _get_version(),
                "channel": channel,
                "status": "healthy",
                "phase": "health_check",
                "event": "edge_update_healthy",
                "attempt": update_attempt,
                "meta": health_meta,
            },
        )
        backup = Path(sys.argv[0]).with_suffix(".exe.bak")
        pending = Path.cwd() / "updates" / "pending.json"
        if backup.exists():
            backup.unlink(missing_ok=True)
        if pending.exists():
            pending.unlink(missing_ok=True)
        logger.info("UPD040 update finalized from %s", args.updated_from)
    detect_snapshot_support(logger)
    _normalize_vision_model_path(logger)
    _auto_set_vision_model_path(logger)

    url = f"{settings.cloud_base_url}/api/edge/events/"
    version = _get_version()
    update_attempt_counter = 0

    vision_source = (os.getenv("VISION_SOURCE") or "rtsp").strip().lower()
    camera_sync_enabled_raw = os.getenv("CAMERA_SYNC_ENABLED")
    camera_sync_enabled = _parse_bool_env("CAMERA_SYNC_ENABLED", True)
    if vision_source == "video" and (camera_sync_enabled_raw is None or camera_sync_enabled_raw.strip() == ""):
        camera_sync_enabled = False
    # Keep edge online even when camera sync/auth is degraded; camera health is reported separately.
    camera_sync_fatal = _parse_bool_env("CAMERA_SYNC_FATAL", False)
    logger.info(
        "Camera sync config enabled=%s fatal=%s vision_source=%s",
        camera_sync_enabled,
        camera_sync_fatal,
        vision_source,
    )
    camera_source_mode = _resolve_camera_source_mode()
    cameras_json_raw = os.getenv("CAMERAS_JSON") or ""
    cameras_json_list, cameras_json_error = _parse_cameras_json(cameras_json_raw, logger)
    if cameras_json_error:
        logger.error("[CAMERA_HEALTH] %s", cameras_json_error)
        cameras_json_list = []

    local_cameras_mode = camera_source_mode == "local_only"
    if local_cameras_mode and camera_sync_enabled:
        logger.info(
            "[CAMERA_HEALTH] source=local_only; disabling remote camera sync"
        )
        camera_sync_enabled = False
    if local_cameras_mode:
        os.environ["VISION_LOCAL_CAMERAS_ONLY"] = "1"
        os.environ["VISION_REMOTE_CAMERA_SYNC_ENABLED"] = "0"
        os.environ["CAMERA_SYNC_ENABLED"] = "0"
    else:
        os.environ.setdefault("VISION_LOCAL_CAMERAS_ONLY", "0")
        # Keep current user/env flag if set; default to enabled for api_first.
        if "VISION_REMOTE_CAMERA_SYNC_ENABLED" not in os.environ:
            os.environ["VISION_REMOTE_CAMERA_SYNC_ENABLED"] = "1"
    logger.info(
        "[CAMERA_HEALTH] source_mode=%s local_mode=%s cameras_json=%s camera_sync_enabled=%s",
        camera_source_mode,
        local_cameras_mode,
        len(cameras_json_list),
        camera_sync_enabled,
    )

    camera_health_interval_seconds = _parse_int_env(
        "CAMERA_HEALTH_INTERVAL_SECONDS",
        settings.camera_heartbeat_interval_seconds or 30,
    )
    if camera_health_interval_seconds > 60:
        logger.warning(
            "[CAMERA_HEALTH] interval too high (%ss); clamping to 60s",
            camera_health_interval_seconds,
        )
        camera_health_interval_seconds = 60
    camera_health_loop_started = False
    camera_states: dict[str, dict[str, Any]] = {}

    watchdog_enabled = _parse_bool_env("WATCHDOG_ENABLED", True)
    watchdog_restart_enabled = _parse_bool_env("WATCHDOG_RESTART_ENABLED", True)
    watchdog_hb_grace = _parse_int_env(
        "WATCHDOG_HEARTBEAT_GRACE_SECONDS",
        WATCHDOG_DEFAULT_HEARTBEAT_GRACE_SECONDS,
    )
    watchdog_ch_grace = _parse_int_env(
        "WATCHDOG_CAMERA_HEALTH_GRACE_SECONDS",
        WATCHDOG_DEFAULT_CAMERA_HEALTH_GRACE_SECONDS,
    )
    watchdog_restart_window = _parse_int_env(
        "WATCHDOG_RESTART_WINDOW_SECONDS",
        WATCHDOG_DEFAULT_RESTART_WINDOW_SECONDS,
    )
    watchdog_restart_max = _parse_int_env(
        "WATCHDOG_RESTART_MAX",
        WATCHDOG_DEFAULT_RESTART_MAX,
    )

    watchdog_state: dict[str, Any] = {
        "last_heartbeat_ok_at": time.time(),
        "last_camera_health_ok_at": time.time(),
        "last_heartbeat_status": None,
        "last_heartbeat_error": None,
        "has_cameras": bool(local_cameras_mode and cameras_json_list),
    }
    watchdog_lock = threading.Lock()
    vision_proxy_enabled = _parse_bool_env("VISION_PROXY_ENABLED", False)
    vision_bucket_seconds = _parse_int_env(
        "VISION_BUCKET_SECONDS",
        VISION_PROXY_DEFAULT_BUCKET_SECONDS,
    )
    last_vision_bucket_at = 0.0
    if args.smoke and args.smoke > 0:
        return _run_smoke(
            seconds=args.smoke,
            settings=settings,
            url=url,
            version=version,
            cameras=cameras_json_list,
            logger=logger,
        )

    # --- Vision worker (optional) ---
    vision = None
    if os.getenv("VISION_ENABLED", "0") == "1":
        msg = (
            "[VISION] starting worker... "
            f"VISION_ENABLED={os.getenv('VISION_ENABLED','')} "
            f"VISION_SOURCE={os.getenv('VISION_SOURCE','')} "
            f"VISION_VIDEO_PATH={os.getenv('VISION_VIDEO_PATH','')} "
            f"VISION_ROI_PATH={os.getenv('VISION_ROI_PATH','')} "
            f"VISION_MODEL_PATH={os.getenv('VISION_MODEL_PATH','')} "
            f"VISION_FRAME_STRIDE={os.getenv('VISION_FRAME_STRIDE','')}"
        )
        print(msg)
        logger.info(msg)
    try:
        vision = VisionWorker(
            cloud_base_url=settings.cloud_base_url,
            store_id=settings.store_id,
            edge_token=settings.edge_token,
            logger=logger,
        )
        if vision.cfg.enabled:
            def _vision_runner():
                reason = "completed"
                try:
                    vision.run_forever()
                except Exception:
                    reason = "exception"
                    logger.error("[VISION] worker crashed:\n%s", traceback.format_exc())
                finally:
                    logger.warning("[VISION] worker thread exited reason=%s", reason)

            t = threading.Thread(target=_vision_runner, daemon=True)
            t.start()
            logger.info("VISION worker started")
    except Exception:
        logger.error("[VISION] worker failed to start:\n%s", traceback.format_exc())

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
    consecutive_auth_failures = 0
    last_camera_sync_at = 0.0
    last_update_check_at = 0.0
    camera_auth_tracker = AuthFailureTracker(max_failures=MAX_CONSECUTIVE_AUTH_FAILURES)
    camera_sync_interval = min(
        CAMERA_SYNC_INTERVAL_SECONDS,
        settings.camera_heartbeat_interval_seconds,
        settings.heartbeat_interval_seconds,
        60,
    )

    if local_cameras_mode:
        logger.info(
            "[CAMERA_HEALTH] using CAMERAS_JSON source cameras=%s interval=%ss",
            len(cameras_json_list),
            camera_health_interval_seconds,
        )
        t = threading.Thread(
            target=_camera_health_loop,
            kwargs={
                "cloud_base_url": settings.cloud_base_url,
                "edge_token": settings.edge_token,
                "store_id": settings.store_id,
                "agent_id": settings.agent_id,
                "cameras": cameras_json_list,
                "interval_seconds": camera_health_interval_seconds,
                "logger": logger,
                "state_store": camera_states,
                "watchdog_state": watchdog_state,
                "watchdog_lock": watchdog_lock,
            },
            daemon=True,
        )
        t.start()
        camera_health_loop_started = True
    elif (not camera_sync_enabled) and cameras_json_list:
        logger.info(
            "[CAMERA_HEALTH] camera sync disabled; using CAMERAS_JSON fallback cameras=%s interval=%ss",
            len(cameras_json_list),
            camera_health_interval_seconds,
        )
        t = threading.Thread(
            target=_camera_health_loop,
            kwargs={
                "cloud_base_url": settings.cloud_base_url,
                "edge_token": settings.edge_token,
                "store_id": settings.store_id,
                "agent_id": settings.agent_id,
                "cameras": cameras_json_list,
                "interval_seconds": camera_health_interval_seconds,
                "logger": logger,
                "state_store": camera_states,
                "watchdog_state": watchdog_state,
                "watchdog_lock": watchdog_lock,
            },
            daemon=True,
        )
        t.start()
        camera_health_loop_started = True

    if watchdog_enabled:
        t_watchdog = threading.Thread(
            target=_watchdog_loop,
            kwargs={
                "logger": logger,
                "state": watchdog_state,
                "lock": watchdog_lock,
                "heartbeat_grace_seconds": watchdog_hb_grace,
                "camera_health_grace_seconds": watchdog_ch_grace,
                "restart_enabled": watchdog_restart_enabled,
                "restart_max": watchdog_restart_max,
                "restart_window_seconds": watchdog_restart_window,
            },
            daemon=True,
        )
        t_watchdog.start()
        logger.info(
            "[WATCHDOG] enabled hb_grace=%ss ch_grace=%ss restart=%s",
            watchdog_hb_grace,
            watchdog_ch_grace,
            watchdog_restart_enabled,
        )

    while True:
        now = time.time()
        if camera_sync_enabled and now - last_camera_sync_at >= camera_sync_interval:
            cameras, cameras_error = fetch_cameras(
                cloud_base_url=settings.cloud_base_url,
                edge_token=settings.edge_token,
                store_id=settings.store_id,
                logger=logger,
                auth_tracker=camera_auth_tracker,
            )
            if cameras_error:
                logger.warning("Camera sync skipped: %s", cameras_error)
                if cameras_json_list and not camera_health_loop_started:
                    logger.warning(
                        "[CAMERA_HEALTH] camera sync failed; starting CAMERAS_JSON fallback cameras=%s",
                        len(cameras_json_list),
                    )
                    t = threading.Thread(
                        target=_camera_health_loop,
                        kwargs={
                            "cloud_base_url": settings.cloud_base_url,
                            "edge_token": settings.edge_token,
                            "store_id": settings.store_id,
                            "agent_id": settings.agent_id,
                            "cameras": cameras_json_list,
                            "interval_seconds": camera_health_interval_seconds,
                            "logger": logger,
                            "state_store": camera_states,
                            "watchdog_state": watchdog_state,
                            "watchdog_lock": watchdog_lock,
                        },
                        daemon=True,
                    )
                    t.start()
                    camera_health_loop_started = True
                if camera_auth_tracker.consecutive >= MAX_CONSECUTIVE_AUTH_FAILURES:
                    message = (
                        f"ERRO FATAL: {MAX_CONSECUTIVE_AUTH_FAILURES} falhas de autenticacao "
                        "consecutivas ao sincronizar cameras. Encerrando."
                    )
                    print(message)
                    logger.error(message)
                    if camera_sync_fatal:
                        return EXIT_AUTH_ERROR
                    logger.warning("Camera sync fatal disabled (CAMERA_SYNC_FATAL=0).")
                    camera_auth_tracker.reset()
            else:
                fresh_states: dict[str, dict[str, Any]] = {}
                active_cameras = [c for c in cameras if _is_camera_active(c)]
                if active_cameras:
                    with watchdog_lock:
                        watchdog_state["has_cameras"] = True
                if len(active_cameras) > settings.max_active_cameras:
                    ignored = active_cameras[settings.max_active_cameras :]
                    ignored_ids = [
                        str(c.get("camera_id") or c.get("id") or "")
                        for c in ignored
                    ]
                    logger.warning(
                        "Limite do plano: processando %s de %s cameras ativas. Ignorando %s: %s",
                        settings.max_active_cameras,
                        len(active_cameras),
                        len(ignored),
                        ", ".join([cid for cid in ignored_ids if cid]),
                    )
                    active_cameras = active_cameras[: settings.max_active_cameras]
                logger.info(
                    "Camera sync: %s cameras (ativas=%s)",
                    len(cameras),
                    len(active_cameras),
                )
                for camera in active_cameras:
                    camera_id = str(
                        camera.get("camera_id") or camera.get("id") or ""
                    ).strip()
                    if not camera_id:
                        logger.warning("Skipping camera with missing id: %s", camera)
                        continue

                    try:
                        candidates = build_rtsp_candidates(camera)
                        if not candidates:
                            logger.warning("CAMNF camera_id=%s no RTSP candidates", camera_id)
                        else:
                            logger.info(
                                "camera_id=%s RTSP candidates=%s",
                                camera_id,
                                len(candidates),
                            )
                        selected_rtsp_url = None
                        health = {
                            "camera_id": camera_id,
                            "status": "error",
                            "error": "rtsp_candidates_missing",
                            "latency_ms": None,
                            "checked_at": None,
                        }
                        for candidate in candidates:
                            health = check_camera_health(
                                camera,
                                perform_describe=settings.rtsp_describe_enabled,
                                rtsp_url_override=candidate,
                            )
                            if health.get("status") in {"online", "degraded"}:
                                logger.info(
                                    "camera_id=%s RTSP selected=%s",
                                    camera_id,
                                    mask_rtsp_url(candidate),
                                )
                                selected_rtsp_url = candidate
                                break
                        if not selected_rtsp_url and candidates:
                            selected_rtsp_url = candidates[-1]
                        if "snapshot_taken" not in health:
                            health["snapshot_taken"] = False
                        if "snapshot_status" not in health:
                            health["snapshot_status"] = "skip"
                        if selected_rtsp_url:
                            health["rtsp_url_used"] = selected_rtsp_url
                            snapshot_result = capture_snapshot_if_possible(
                                camera_id=camera_id,
                                rtsp_url=selected_rtsp_url,
                                logger=logger,
                            )
                            health["snapshot_status"] = snapshot_result.get("snapshot_status")
                            health["snapshot_local_path"] = snapshot_result.get(
                                "snapshot_local_path"
                            )
                            if snapshot_result.get("snapshot_local_path"):
                                health["snapshot_taken"] = True
                                health["snapshot_url"] = snapshot_result.get(
                                    "snapshot_local_path"
                                )
                                health.update(
                                    estimate_snapshot_quality(
                                        snapshot_result.get("snapshot_local_path"),
                                        logger=logger,
                                    )
                                )
                                logger.info(
                                    "camera_id=%s snapshot ready (upload pending)",
                                    camera_id,
                                )
                            else:
                                health["snapshot_taken"] = False
                        roi_blob = camera.get("roi")
                        roi_blob_version = (
                            roi_blob.get("version")
                            if isinstance(roi_blob, dict)
                            else None
                        )
                        roi_version_hint = (
                            camera.get("roi_version")
                            or camera.get("roiVersion")
                            or roi_blob_version
                        )
                        _, roi_version, cached, roi_error = fetch_roi(
                            camera_id,
                            cloud_base_url=settings.cloud_base_url,
                            edge_token=settings.edge_token,
                            expected_version=str(roi_version_hint)
                            if roi_version_hint
                            else None,
                            logger=logger,
                            auth_tracker=camera_auth_tracker,
                        )
                        if roi_error:
                            logger.warning("camera_id=%s roi_error=%s", camera_id, roi_error)
                        if camera_auth_tracker.consecutive >= MAX_CONSECUTIVE_AUTH_FAILURES:
                            message = (
                                f"ERRO FATAL: {MAX_CONSECUTIVE_AUTH_FAILURES} falhas de "
                                "autenticacao consecutivas ao buscar ROI. Encerrando."
                            )
                            print(message)
                            logger.error(message)
                            if camera_sync_fatal:
                                return EXIT_AUTH_ERROR
                            logger.warning("Camera sync fatal disabled (CAMERA_SYNC_FATAL=0).")
                            camera_auth_tracker.reset()
                        health["roi_version"] = roi_version
                        health["roi_cached"] = cached
                        fresh_states[camera_id] = health
                        logger.info(
                            "camera_id=%s status=%s latency_ms=%s roi_version=%s cached=%s",
                            camera_id,
                            health.get("status"),
                            health.get("latency_ms"),
                            roi_version,
                            cached,
                        )
                        ok_evt, status_evt, err_evt = send_camera_health_event(
                            cloud_base_url=settings.cloud_base_url,
                            edge_token=settings.edge_token,
                            store_id=settings.store_id,
                            agent_id=settings.agent_id,
                            camera_health=health,
                            logger=logger,
                            auth_tracker=camera_auth_tracker,
                        )
                        if not ok_evt:
                            logger.warning(
                                "camera_id=%s health event failed status=%s error=%s",
                                camera_id,
                                status_evt,
                                err_evt,
                            )
                        else:
                            with watchdog_lock:
                                watchdog_state["last_camera_health_ok_at"] = time.time()
                                watchdog_state["has_cameras"] = True
                        if camera_auth_tracker.consecutive >= MAX_CONSECUTIVE_AUTH_FAILURES:
                            message = (
                                f"ERRO FATAL: {MAX_CONSECUTIVE_AUTH_FAILURES} falhas de "
                                "autenticacao consecutivas ao enviar eventos. Encerrando."
                            )
                            print(message)
                            logger.error(message)
                            if camera_sync_fatal:
                                return EXIT_AUTH_ERROR
                            logger.warning("Camera sync fatal disabled (CAMERA_SYNC_FATAL=0).")
                            camera_auth_tracker.reset()
                    except Exception as exc:
                        logger.exception("camera_id=%s unexpected failure: %s", camera_id, exc)
                        fresh_states[camera_id] = {
                            "camera_id": camera_id,
                            "status": "offline",
                            "error": str(exc),
                            "latency_ms": None,
                            "roi_version": None,
                        }
                camera_states = fresh_states
            last_camera_sync_at = now
        elif not camera_sync_enabled and now - last_camera_sync_at >= camera_sync_interval:
            logger.info("Camera sync disabled (CAMERA_SYNC_ENABLED=0)")
            last_camera_sync_at = now

        camera_fields = build_camera_heartbeat_fields(camera_states)
        ok, status, error = send_heartbeat(
            url=url,
            edge_token=settings.edge_token,
            store_id=settings.store_id,
            agent_id=settings.agent_id,
            version=version,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            extra_data=camera_fields,
        )

        with watchdog_lock:
            watchdog_state["last_heartbeat_status"] = status
            watchdog_state["last_heartbeat_error"] = error
            if ok:
                watchdog_state["last_heartbeat_ok_at"] = time.time()

        if status is None:
            print(f"Heartbeat -> {url} status=ERROR")
        else:
            print(f"Heartbeat -> {url} status={status}")

        if ok:
            logger.info("Heartbeat -> %s status=%s", url, status)
            backoff_index = 0
            consecutive_failures = 0
            last_failure_status = None
            consecutive_auth_failures = 0
            now = time.time()
            if vision_proxy_enabled and now - last_vision_bucket_at >= vision_bucket_seconds:
                online_cameras = sum(
                    1 for state in camera_states.values() if state.get("status") == "online"
                )
                footfall = online_cameras * 2
                engaged = max(0, footfall - 1)
                bucket_start, bucket_end = _floor_bucket(now, vision_bucket_seconds)
                payload = {
                    "store_id": settings.store_id,
                    "agent_id": settings.agent_id,
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "proxy": True,
                    "bucket": {
                        "start": bucket_start,
                        "end": bucket_end,
                        "seconds": vision_bucket_seconds,
                    },
                    "traffic": {
                        "footfall": footfall,
                        "engaged": engaged,
                        "dwell_seconds_avg": 30 if footfall > 0 else 0,
                    },
                    "conversion": {
                        "queue_avg_seconds": 15 if footfall > 0 else 0,
                        "staff_active_est": 1 if footfall > 0 else 0,
                    },
                }
                ok_evt, status_evt, err_evt = send_vision_metrics_event(
                    cloud_base_url=settings.cloud_base_url,
                    edge_token=settings.edge_token,
                    payload=payload,
                    timeout_seconds=REQUEST_TIMEOUT_SECONDS,
                    logger=logger,
                )
                if ok_evt:
                    last_vision_bucket_at = now
                    logger.info(
                        "[VISION_PROXY] bucket sent footfall=%s engaged=%s",
                        footfall,
                        engaged,
                    )
                else:
                    logger.warning(
                        "[VISION_PROXY] bucket failed status=%s error=%s",
                        status_evt,
                        err_evt,
                    )
            if now - last_update_check_at >= settings.update_interval_seconds:
                update = check_for_update(
                    logger=logger,
                    current_version=version,
                    update_check_url=settings.update_check_url,
                    auto_update_enabled=settings.auto_update_enabled,
                    cloud_base_url=settings.cloud_base_url,
                    edge_token=settings.edge_token,
                    store_id=settings.store_id,
                    agent_id=settings.agent_id,
                )
                if update and update.get("blocked_reason_code"):
                    update_attempt_counter += 1
                    blocked_attempt = update_attempt_counter
                    send_update_report(
                        logger=logger,
                        cloud_base_url=settings.cloud_base_url,
                        edge_token=settings.edge_token,
                        payload={
                            "store_id": settings.store_id,
                            "agent_id": settings.agent_id,
                            "from_version": version,
                            "to_version": update.get("version"),
                            "channel": update.get("channel") or "stable",
                            "status": "failed",
                            "phase": update.get("blocked_phase") or "policy_check",
                            "event": "edge_update_failed",
                            "attempt": blocked_attempt,
                            "reason_code": update.get("blocked_reason_code"),
                            "reason_detail": update.get("blocked_detail"),
                        },
                    )
                if update and update.get("auto_apply"):
                    update_attempt_counter += 1
                    update_attempt = update_attempt_counter
                    update["attempt"] = update_attempt
                    lock_ok, lock_path, lock_reason = acquire_update_lock(
                        logger=logger,
                        version=str(update.get("version") or ""),
                    )
                    if not lock_ok:
                        send_update_report(
                            logger=logger,
                            cloud_base_url=settings.cloud_base_url,
                            edge_token=settings.edge_token,
                            payload={
                                "store_id": settings.store_id,
                                "agent_id": settings.agent_id,
                                "from_version": version,
                                "to_version": update.get("version"),
                                "channel": update.get("channel") or "stable",
                                "status": "failed",
                                "phase": "policy_check",
                                "event": "edge_update_failed",
                                "attempt": update_attempt,
                                "reason_code": lock_reason or "UPDATE_LOCKED",
                            },
                        )
                        last_update_check_at = now
                        time.sleep(settings.heartbeat_interval_seconds)
                        continue
                    send_update_report(
                        logger=logger,
                        cloud_base_url=settings.cloud_base_url,
                        edge_token=settings.edge_token,
                        payload={
                            "store_id": settings.store_id,
                            "agent_id": settings.agent_id,
                            "from_version": version,
                            "to_version": update.get("version"),
                            "channel": update.get("channel") or "stable",
                            "status": "started",
                            "phase": "policy_check",
                            "event": "edge_update_started",
                            "attempt": update_attempt,
                        },
                    )
                    try:
                        service_mode = os.getenv("SERVICE_MODE") or os.getenv("DALE_SERVICE_MODE")
                        downloaded = download_update(logger=logger, update=update)
                        if downloaded:
                            send_update_report(
                                logger=logger,
                                cloud_base_url=settings.cloud_base_url,
                                edge_token=settings.edge_token,
                                payload={
                                    "store_id": settings.store_id,
                                    "agent_id": settings.agent_id,
                                    "from_version": version,
                                    "to_version": update.get("version"),
                                    "channel": update.get("channel") or "stable",
                                    "status": "downloaded",
                                    "phase": "download",
                                    "event": "edge_update_downloaded",
                                    "attempt": update_attempt,
                                },
                            )
                            send_update_report(
                                logger=logger,
                                cloud_base_url=settings.cloud_base_url,
                                edge_token=settings.edge_token,
                                payload={
                                    "store_id": settings.store_id,
                                    "agent_id": settings.agent_id,
                                    "from_version": version,
                                    "to_version": update.get("version"),
                                    "channel": update.get("channel") or "stable",
                                    "status": "verified",
                                    "phase": "checksum",
                                    "event": "edge_update_verified",
                                    "attempt": update_attempt,
                                },
                            )
                            if service_mode:
                                logger.info("UPD012 update scheduled (service mode)")
                            else:
                                send_update_report(
                                    logger=logger,
                                    cloud_base_url=settings.cloud_base_url,
                                    edge_token=settings.edge_token,
                                    payload={
                                        "store_id": settings.store_id,
                                        "agent_id": settings.agent_id,
                                        "from_version": version,
                                        "to_version": update.get("version"),
                                        "channel": update.get("channel") or "stable",
                                        "status": "activated",
                                        "phase": "activation",
                                        "event": "edge_update_activated",
                                        "attempt": update_attempt,
                                    },
                                )
                                if apply_update_if_possible(
                                    logger=logger,
                                    current_version=version,
                                    update=update,
                                    downloaded_path=downloaded,
                                ):
                                    return 0
                                send_update_report(
                                    logger=logger,
                                    cloud_base_url=settings.cloud_base_url,
                                    edge_token=settings.edge_token,
                                    payload={
                                        "store_id": settings.store_id,
                                        "agent_id": settings.agent_id,
                                        "from_version": version,
                                        "to_version": update.get("version"),
                                        "channel": update.get("channel") or "stable",
                                        "status": "failed",
                                        "phase": "activation",
                                        "event": "edge_update_failed",
                                        "attempt": update_attempt,
                                        "reason_code": "ACTIVATION_FAILED",
                                    },
                                )
                        else:
                            send_update_report(
                                logger=logger,
                                cloud_base_url=settings.cloud_base_url,
                                edge_token=settings.edge_token,
                                payload={
                                    "store_id": settings.store_id,
                                    "agent_id": settings.agent_id,
                                    "from_version": version,
                                    "to_version": update.get("version"),
                                    "channel": update.get("channel") or "stable",
                                    "status": "failed",
                                    "phase": "download",
                                    "event": "edge_update_failed",
                                    "attempt": update_attempt,
                                    "reason_code": "DOWNLOAD_FAILED",
                                },
                            )
                    finally:
                        release_update_lock(logger=logger, lock_path=lock_path)
                last_update_check_at = now
            time.sleep(settings.heartbeat_interval_seconds)
            continue

        consecutive_failures += 1
        last_failure_status = status

        if status in AUTH_FAILURE_STATUSES:
            consecutive_auth_failures += 1
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
            if consecutive_auth_failures >= MAX_CONSECUTIVE_AUTH_FAILURES:
                message = (
                    f"ERRO FATAL: {MAX_CONSECUTIVE_AUTH_FAILURES} falhas "
                    "de autenticacao consecutivas. Encerrando."
                )
                print(message)
                logger.error(message)
                return EXIT_AUTH_ERROR
        elif status is not None:
            consecutive_auth_failures = 0
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
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Encerrado pelo usuario.")
        raise SystemExit(0)
