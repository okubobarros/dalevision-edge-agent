from __future__ import annotations

import argparse
import ctypes
import importlib.metadata
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import sys
import time
import threading
import traceback
from typing import Any

from .cameras import (
    AuthFailureTracker,
    CAMERA_SYNC_INTERVAL_SECONDS,
    build_camera_heartbeat_fields,
    build_rtsp_candidates,
    capture_snapshot_if_possible,
    check_camera_health,
    detect_snapshot_support,
    fetch_cameras,
    fetch_roi,
    mask_rtsp_url,
    send_camera_health_event,
)
from .diagnostics import run_doctor
from .env import InvalidTokenError, load_env_from_cwd, load_settings
from .heartbeat import REQUEST_TIMEOUT_SECONDS, send_heartbeat
from .rtsp_test import test_rtsp, test_rtsp_channels
from .scan import run_scan
from .update import apply_update_if_possible, check_for_update, download_update
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

    target = str(run_cmd.resolve())
    workdir = str(run_cmd.resolve().parent)
    icon = str((run_cmd.resolve().parent / "dalevision-edge-agent.exe"))

    def _ps_quote(value: str) -> str:
        return value.replace("'", "''")

    script = (
        f"$ws=New-Object -ComObject WScript.Shell;"
        f"$sc=$ws.CreateShortcut('{_ps_quote(str(link_path))}');"
        f"$sc.TargetPath='{_ps_quote(target)}';"
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


def _run_install_service_command(*, logger: logging.Logger) -> int:
    script_path, checked, install_root = _resolve_install_service_script()
    checked_text = ", ".join(str(p) for p in checked)
    if script_path is None:
        print("Nao foi possivel localizar o instalador de servico.")
        print("Verifique se a pasta scripts foi extraida junto do agente.")
        print(f"Caminhos verificados: {checked_text}")
        logger.warning("install-service script missing; checked=%s", checked_text)
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
        if not camera_id or not rtsp_url:
            return [], f"CAMERAS_JSON item {idx} missing id/rtsp_url"
        cameras.append(
            {
                "id": camera_id,
                "name": str(item.get("name") or "").strip(),
                "rtsp_url": rtsp_url,
            }
        )

    if not cameras:
        logger.warning("CAMERAS_JSON parsed but contained no valid cameras")
    return cameras, None


def _auto_set_vision_model_path(logger: logging.Logger) -> None:
    if os.getenv("VISION_MODEL_PATH"):
        return
    model_path = Path("C:\\ProgramData\\DaleVision\\models\\yolov8n.pt")
    if model_path.exists():
        os.environ["VISION_MODEL_PATH"] = str(model_path)
        logger.info("VISION_MODEL_PATH auto-set to %s", model_path)
        return
    logger.warning("modelo nao encontrado localmente; pode baixar da internet.")


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


def _camera_health_loop(
    *,
    cloud_base_url: str,
    edge_token: str,
    cameras: list[dict[str, Any]],
    interval_seconds: int,
    perform_describe: bool,
    logger: logging.Logger,
) -> None:
    while True:
        for camera in cameras:
            camera_id = str(camera.get("id") or "").strip()
            rtsp_url = str(camera.get("rtsp_url") or "").strip()
            if not camera_id or not rtsp_url:
                continue
            try:
                health = check_camera_health(
                    {"id": camera_id, "rtsp_url": rtsp_url},
                    timeout_seconds=3,
                    perform_describe=perform_describe,
                    rtsp_url_override=rtsp_url,
                )
                health["camera_id"] = camera_id
                ok_evt, status_evt, err_evt = send_camera_health_event(
                    cloud_base_url=cloud_base_url,
                    edge_token=edge_token,
                    camera_health=health,
                    timeout_seconds=10,
                    logger=logger,
                )
                if ok_evt:
                    logger.info(
                        "camera_id=%s health sent status=%s latency_ms=%s",
                        camera_id,
                        health.get("status"),
                        health.get("latency_ms"),
                    )
                else:
                    logger.warning(
                        "camera_id=%s health send failed status=%s error=%s",
                        camera_id,
                        status_evt,
                        err_evt,
                    )
            except Exception as exc:
                logger.exception("camera_id=%s health loop error: %s", camera_id, exc)
        time.sleep(interval_seconds)


def main() -> int:
    args = _parse_args()
    env_path = load_env_from_cwd()
    logger = _setup_logging()

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
        )
        return 0

    if args.command == "install-service":
        return _run_install_service_command(logger=logger)

    if args.command == "scan":
        results = run_scan(logger=logger)
        print("Scan results:")
        for item in results:
            print(f"- {item['ip']} ports={item['ports']} confidence={item['confidence']}")
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
        backup = Path(sys.argv[0]).with_suffix(".exe.bak")
        pending = Path.cwd() / "updates" / "pending.json"
        if backup.exists():
            backup.unlink(missing_ok=True)
        if pending.exists():
            pending.unlink(missing_ok=True)
        logger.info("UPD040 update finalized from %s", args.updated_from)
    detect_snapshot_support(logger)
    _auto_set_vision_model_path(logger)

    url = f"{settings.cloud_base_url}/api/edge/events/"
    version = _get_version()

    vision_source = (os.getenv("VISION_SOURCE") or "rtsp").strip().lower()
    camera_sync_enabled_raw = os.getenv("CAMERA_SYNC_ENABLED")
    camera_sync_enabled = _parse_bool_env("CAMERA_SYNC_ENABLED", True)
    if vision_source == "video" and (camera_sync_enabled_raw is None or camera_sync_enabled_raw.strip() == ""):
        camera_sync_enabled = False
    camera_sync_fatal = _parse_bool_env("CAMERA_SYNC_FATAL", True)
    logger.info(
        "Camera sync config enabled=%s fatal=%s vision_source=%s",
        camera_sync_enabled,
        camera_sync_fatal,
        vision_source,
    )
    cameras_json_raw = os.getenv("CAMERAS_JSON") or ""
    cameras_json_list, cameras_json_error = _parse_cameras_json(cameras_json_raw, logger)
    if cameras_json_error:
        logger.error("[CAMERA_HEALTH] %s", cameras_json_error)
        cameras_json_list = []

    camera_health_interval_seconds = _parse_int_env(
        "CAMERA_HEALTH_INTERVAL_SECONDS",
        settings.camera_heartbeat_interval_seconds or 30,
    )
    camera_health_loop_started = False

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
    camera_states: dict[str, dict[str, Any]] = {}
    camera_auth_tracker = AuthFailureTracker(max_failures=MAX_CONSECUTIVE_AUTH_FAILURES)
    camera_sync_interval = max(
        CAMERA_SYNC_INTERVAL_SECONDS,
        settings.camera_heartbeat_interval_seconds,
    )

    if not camera_sync_enabled and cameras_json_list:
        logger.info(
            "[CAMERA_HEALTH] using CAMERAS_JSON source (sync disabled) cameras=%s",
            len(cameras_json_list),
        )
        t = threading.Thread(
            target=_camera_health_loop,
            kwargs={
                "cloud_base_url": settings.cloud_base_url,
                "edge_token": settings.edge_token,
                "cameras": cameras_json_list,
                "interval_seconds": camera_health_interval_seconds,
                "perform_describe": settings.rtsp_describe_enabled,
                "logger": logger,
            },
            daemon=True,
        )
        t.start()
        camera_health_loop_started = True

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
                            "cameras": cameras_json_list,
                            "interval_seconds": camera_health_interval_seconds,
                            "perform_describe": settings.rtsp_describe_enabled,
                            "logger": logger,
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
            if now - last_update_check_at >= settings.update_interval_seconds:
                update = check_for_update(
                    logger=logger,
                    current_version=version,
                    update_check_url=settings.update_check_url,
                    auto_update_enabled=settings.auto_update_enabled,
                )
                if update and update.get("auto_apply"):
                    service_mode = os.getenv("SERVICE_MODE") or os.getenv("DALE_SERVICE_MODE")
                    downloaded = download_update(logger=logger, update=update)
                    if downloaded:
                        if service_mode:
                            logger.info("UPD012 update scheduled (service mode)")
                        else:
                            if apply_update_if_possible(
                                logger=logger,
                                current_version=version,
                                update=update,
                                downloaded_path=downloaded,
                            ):
                                return 0
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
