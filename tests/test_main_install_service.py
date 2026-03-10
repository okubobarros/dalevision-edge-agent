from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace

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


def test_create_startup_shortcut_uses_hidden_powershell_launcher(monkeypatch, tmp_path: Path) -> None:
    logger = logging.getLogger("test-startup-shortcut")
    logger.addHandler(logging.NullHandler())

    install_root = tmp_path / "install"
    scripts_internal = install_root / "scripts" / "internal"
    scripts_internal.mkdir(parents=True)
    run_cmd = install_root / "run_agent.cmd"
    run_cmd.write_text("@echo off", encoding="utf-8")
    launcher = scripts_internal / "Start_DaleVision_Agent.ps1"
    launcher.write_text("Write-Host 'ok'", encoding="utf-8")
    (install_root / "dalevision-edge-agent.exe").write_text("stub", encoding="utf-8")

    appdata = tmp_path / "appdata"
    startup_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True)
    (startup_dir / "DaleVision Edge Agent.lnk").write_text("stub", encoding="utf-8")

    windir = tmp_path / "windows"
    powershell = windir / "System32" / "WindowsPowerShell" / "v1.0"
    powershell.mkdir(parents=True)
    (powershell / "powershell.exe").write_text("stub", encoding="utf-8")

    captured: dict[str, list[str]] = {}

    def _fake_run(cmd, capture_output, text):
        captured["cmd"] = cmd
        return SimpleNamespace(returncode=0, stderr="", stdout="")

    monkeypatch.setattr(agent_main, "_resolve_run_agent_cmd", lambda: (run_cmd, [run_cmd]))
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("WINDIR", str(windir))
    monkeypatch.setattr(agent_main.subprocess, "run", _fake_run)

    ok, _msg = agent_main._create_startup_shortcut(logger=logger)

    assert ok is True
    command = captured["cmd"]
    assert command[0].lower().startswith("powershell")
    assert "Start_DaleVision_Agent.ps1" in command[-1]
    assert "-WindowStyle Hidden" in command[-1]
