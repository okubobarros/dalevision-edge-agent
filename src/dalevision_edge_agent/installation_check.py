from __future__ import annotations

from pathlib import Path
from typing import Any


EXPECTED_SCRIPT_FILES = (
    "01_TESTE_RAPIDO.bat",
    "02_INSTALAR_AUTOSTART.bat",
    "03_VERIFICAR_STATUS.bat",
)
RUNNER_FILE_CANDIDATES = (
    "run_agent.cmd",
    "dalevision-edge-agent.exe",
    "DaleVisionEdge.exe",
    "DaleVision Edge Agent.exe",
)
SEARCH_DIR_CANDIDATES = (
    ".",
    "release",
)


def _existing_files(root: Path, names: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for rel in SEARCH_DIR_CANDIDATES:
        base = (root / rel).resolve()
        for name in names:
            candidate = (base / name).resolve()
            if candidate.exists():
                found.append(str(candidate))
    unique_sorted = sorted(set(found))
    return unique_sorted


def _summarize_status(checks: list[dict[str, Any]]) -> str:
    has_fail = any(item.get("status") == "fail" for item in checks)
    if has_fail:
        return "blocked"
    has_warning = any(item.get("status") == "warning" for item in checks)
    if has_warning:
        return "needs_attention"
    return "ready"


def build_installation_check_payload(*, cwd: Path | None = None) -> dict[str, Any]:
    root = (cwd or Path.cwd()).resolve()
    script_files = _existing_files(root, EXPECTED_SCRIPT_FILES)
    runner_files = _existing_files(root, RUNNER_FILE_CANDIDATES)

    scripts_status = "ok" if len(script_files) >= 2 else "fail"
    runner_status = "ok" if len(runner_files) >= 1 else "warning"

    checks = [
        {
            "key": "package_scripts",
            "status": scripts_status,
            "reason_code": "scripts_found" if scripts_status == "ok" else "scripts_missing",
            "message": f"{len(script_files)}/{len(EXPECTED_SCRIPT_FILES)} scripts detectados",
            "details": {"files": script_files},
        },
        {
            "key": "package_runner",
            "status": runner_status,
            "reason_code": "runner_found" if runner_status == "ok" else "runner_missing",
            "message": "Runner detectado" if runner_status == "ok" else "Nenhum runner detectado (cmd/exe)",
            "details": {"files": runner_files},
        },
    ]
    status = _summarize_status(checks)
    return {
        "ok": True,
        "method": {"id": "edge_installation_check", "version": "v1"},
        "status": status,
        "working_dir": str(root),
        "summary": {
            "checks_total": len(checks),
            "checks_ok": len([item for item in checks if item.get("status") == "ok"]),
            "checks_warning": len([item for item in checks if item.get("status") == "warning"]),
            "checks_fail": len([item for item in checks if item.get("status") == "fail"]),
        },
        "checks": checks,
    }

