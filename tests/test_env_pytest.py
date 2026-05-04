from __future__ import annotations

import logging

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


def test_env_logs_token_length_without_token_fragments(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    token = "tok_" + "x" * 30
    monkeypatch.setenv("CLOUD_BASE_URL", "https://api.example.com")
    monkeypatch.setenv("STORE_ID", "123e4567-e89b-12d3-a456-426614174000")
    monkeypatch.setenv("EDGE_TOKEN", token)

    with caplog.at_level(logging.INFO):
        load_settings()

    logs = "\n".join(record.getMessage() for record in caplog.records)
    assert token not in logs
    assert token[:6] not in logs
    assert token[-4:] not in logs
    assert "EDGE_TOKEN carregado" in logs
