import json

from dalevision_edge_agent.versioning import resolve_agent_version


def test_resolve_agent_version_prefers_versioned_app_dir_over_stale_config(monkeypatch, tmp_path):
    app_dir = tmp_path / "DaleVision" / "app" / "1.0.51"
    app_dir.mkdir(parents=True)
    config_path = tmp_path / "agent_config.json"
    config_path.write_text(json.dumps({"installed_version": "1.0.30"}), encoding="utf-8")

    monkeypatch.setenv("DALE_APP_DIR", str(app_dir))
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DALEVISION_EDGE_AGENT_VERSION", "1.0.30")

    assert resolve_agent_version() == "1.0.51"


def test_resolve_agent_version_uses_env_when_app_dir_not_set(monkeypatch, tmp_path):
    config_path = tmp_path / "agent_config.json"
    config_path.write_text(json.dumps({"installed_version": "1.0.30"}), encoding="utf-8")

    monkeypatch.delenv("DALE_APP_DIR", raising=False)
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("DALEVISION_EDGE_AGENT_VERSION", "1.0.51")

    assert resolve_agent_version() == "1.0.51"


def test_resolve_agent_version_falls_back_to_metadata(monkeypatch, tmp_path):
    config_path = tmp_path / "missing_agent_config.json"
    monkeypatch.delenv("DALE_APP_DIR", raising=False)
    monkeypatch.delenv("DALEVISION_EDGE_AGENT_VERSION", raising=False)
    monkeypatch.delenv("EDGE_AGENT_VERSION", raising=False)
    monkeypatch.setenv("DALE_AGENT_CONFIG_PATH", str(config_path))
    monkeypatch.setattr("importlib.metadata.version", lambda _: "1.0.51")

    assert resolve_agent_version() == "1.0.51"
