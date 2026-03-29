from __future__ import annotations

import logging
from pathlib import Path

from dalevision_edge_agent.activation import (
    ActivationBootstrapOutcome,
    ActivationResult,
    AgentState,
    ConfigManager,
    bootstrap_activation,
)


class _ClientOk:
    def activate(self, **_kwargs):
        return ActivationResult(
            ok=True,
            status_code=200,
            error_code=None,
            error_detail=None,
            payload={
                "store_id": "123e4567-e89b-12d3-a456-426614174000",
                "device_id": "dev-123",
                "device_key": "edge-device-123",
                "installed_version": "1.0.0",
                "update_channel": "stable",
            },
            network_error=False,
        )


class _ClientInvalidToken:
    def activate(self, **_kwargs):
        return ActivationResult(
            ok=False,
            status_code=401,
            error_code="activation_token_invalid",
            error_detail="Token inválido.",
            payload={},
            network_error=False,
        )


def _logger() -> logging.Logger:
    logger = logging.getLogger("test-activation-bootstrap")
    logger.addHandler(logging.NullHandler())
    return logger


def test_bootstrap_without_token_or_device_is_unprovisioned(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "agent_config.json")
    out = bootstrap_activation(
        logger=_logger(),
        cloud_base_url="https://api.example.com",
        installed_version="1.0.0",
        config_manager=manager,
    )
    assert isinstance(out, ActivationBootstrapOutcome)
    assert out.state == AgentState.UNPROVISIONED
    assert out.result is None


def test_bootstrap_activation_success_persists_identity(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "agent_config.json")
    manager.save(
        {
            "activation_token": "act-token-123",
            "update_channel": "stable",
        }
    )
    out = bootstrap_activation(
        logger=_logger(),
        cloud_base_url="https://api.example.com",
        installed_version="1.0.0",
        config_manager=manager,
        activation_client=_ClientOk(),
    )
    data = manager.load()
    assert out.state == AgentState.ACTIVE
    assert data.get("edge_device_id") == "dev-123"
    assert data.get("store_id") == "123e4567-e89b-12d3-a456-426614174000"
    assert data.get("device_key") == "edge-device-123"
    assert "activation_token" not in data


def test_bootstrap_invalid_token_sets_error_state(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "agent_config.json")
    manager.save(
        {
            "activation_token": "bad-token",
            "update_channel": "stable",
        }
    )
    out = bootstrap_activation(
        logger=_logger(),
        cloud_base_url="https://api.example.com",
        installed_version="1.0.0",
        config_manager=manager,
        activation_client=_ClientInvalidToken(),
    )
    assert out.state == AgentState.ERROR
    assert out.result is not None
    assert out.result.error_code == "activation_token_invalid"


def test_bootstrap_with_existing_device_stays_active_without_activation_call(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path / "agent_config.json")
    manager.save(
        {
            "device_key": "edge-existing",
            "edge_device_id": "dev-existing",
            "store_id": "123e4567-e89b-12d3-a456-426614174000",
        }
    )

    class _FailIfCalled:
        def activate(self, **_kwargs):
            raise AssertionError("activate should not be called")

    out = bootstrap_activation(
        logger=_logger(),
        cloud_base_url="https://api.example.com",
        installed_version="1.0.0",
        config_manager=manager,
        activation_client=_FailIfCalled(),
    )
    assert out.state == AgentState.ACTIVE
    assert out.result is None
