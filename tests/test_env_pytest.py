from __future__ import annotations

import pytest

from dalevision_edge_agent.env import load_settings


def test_env_missing_required_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUD_BASE_URL", raising=False)
    monkeypatch.delenv("STORE_ID", raising=False)
    monkeypatch.delenv("EDGE_TOKEN", raising=False)
    with pytest.raises(ValueError):
        load_settings()


def test_env_validates_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("STORE_ID", "123e4567-e89b-12d3-a456-426614174000")
    monkeypatch.setenv("EDGE_TOKEN", "tok_" + "x" * 30)
    settings = load_settings()
    assert settings.cloud_base_url == "https://api.example.com"
