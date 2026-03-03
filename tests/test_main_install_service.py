from __future__ import annotations

import logging
from pathlib import Path

from dalevision_edge_agent import main as agent_main


def test_resolve_install_service_script_finds_scripts_subdir(monkeypatch, tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    script_path = scripts_dir / "install-service.ps1"
    script_path.write_text("Write-Host 'ok'", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent_main.sys, "executable", str(tmp_path / "dalevision-edge-agent.exe"))
    monkeypatch.setattr(agent_main.sys, "_MEIPASS", None, raising=False)

    resolved, _checked, install_root = agent_main._resolve_install_service_script()

    assert resolved == script_path
    assert install_root == tmp_path


def test_run_install_service_fallback_when_script_missing_and_not_admin(monkeypatch) -> None:
    logger = logging.getLogger("test-main-install-service")
    logger.addHandler(logging.NullHandler())

    monkeypatch.setattr(agent_main, "_resolve_install_service_script", lambda: (None, [], Path.cwd()))
    monkeypatch.setattr(agent_main, "_is_windows_admin", lambda: False)
    monkeypatch.setattr(agent_main, "_create_startup_shortcut", lambda logger: (True, "startup ok"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")

    rc = agent_main._run_install_service_command(logger=logger)

    assert rc == 0
