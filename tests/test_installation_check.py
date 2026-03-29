from dalevision_edge_agent.installation_check import build_installation_check_payload


def test_installation_check_ready_when_scripts_and_runner_exist(tmp_path):
    (tmp_path / "01_TESTE_RAPIDO.bat").write_text("echo ok", encoding="utf-8")
    (tmp_path / "02_INSTALAR_AUTOSTART.bat").write_text("echo ok", encoding="utf-8")
    (tmp_path / "run_agent.cmd").write_text("echo run", encoding="utf-8")

    payload = build_installation_check_payload(cwd=tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "ready"
    assert payload["summary"]["checks_ok"] == 2
    assert payload["summary"]["checks_fail"] == 0
    assert payload["summary"]["checks_warning"] == 0


def test_installation_check_blocked_when_scripts_missing(tmp_path):
    (tmp_path / "run_agent.cmd").write_text("echo run", encoding="utf-8")

    payload = build_installation_check_payload(cwd=tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "blocked"
    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["package_scripts"]["status"] == "fail"
    assert checks["package_scripts"]["reason_code"] == "scripts_missing"
    assert checks["package_runner"]["status"] == "ok"


def test_installation_check_needs_attention_when_runner_missing(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "01_TESTE_RAPIDO.bat").write_text("echo ok", encoding="utf-8")
    (release_dir / "02_INSTALAR_AUTOSTART.bat").write_text("echo ok", encoding="utf-8")

    payload = build_installation_check_payload(cwd=tmp_path)

    assert payload["ok"] is True
    assert payload["status"] == "needs_attention"
    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["package_scripts"]["status"] == "ok"
    assert checks["package_runner"]["status"] == "warning"
    assert checks["package_runner"]["reason_code"] == "runner_missing"
