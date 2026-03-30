from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Optional
import uuid

import requests

DEFAULT_CONFIG_FILENAME = "agent_config.json"
ACTIVATE_ENDPOINT = "/api/v1/stores/activate/"
REQUEST_TIMEOUT_SECONDS = 10
_ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


class AgentState(str, Enum):
    UNPROVISIONED = "unprovisioned"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEGRADED = "degraded"
    ERROR = "error"


class ConfigManager:
    def __init__(self, path: Path):
        self.path = path

    @classmethod
    def from_default(cls) -> "ConfigManager":
        explicit = str(os.getenv("DALE_AGENT_CONFIG_PATH") or "").strip()
        if explicit:
            return cls(Path(explicit))
        config_dir = str(os.getenv("DALE_CONFIG_DIR") or "").strip()
        if config_dir:
            return cls(Path(config_dir) / DEFAULT_CONFIG_FILENAME)
        return cls(Path.cwd() / DEFAULT_CONFIG_FILENAME)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return dict(data)
        except Exception:
            return {}
        return {}

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def update_partial(self, **fields: Any) -> dict[str, Any]:
        data = self.load()
        for key, value in fields.items():
            if value is None and key in data:
                data.pop(key, None)
                continue
            data[key] = value
        self.save(data)
        return data


class StateMachine:
    def __init__(self, logger: logging.Logger, initial: AgentState = AgentState.UNPROVISIONED):
        self._state = initial
        self._logger = logger
        self._logger.info("[ACTIVATION] state=%s", self._state.value)

    def set_state(self, new_state: AgentState, *, reason: str = "") -> None:
        old_state = self._state
        self._state = new_state
        if reason:
            self._logger.info(
                "[ACTIVATION] state transition %s -> %s reason=%s",
                old_state.value,
                new_state.value,
                reason,
            )
        else:
            self._logger.info(
                "[ACTIVATION] state transition %s -> %s",
                old_state.value,
                new_state.value,
            )

    def get_state(self) -> AgentState:
        return self._state


@dataclass(frozen=True)
class ActivationResult:
    ok: bool
    status_code: Optional[int]
    error_code: Optional[str]
    error_detail: Optional[str]
    payload: dict[str, Any]
    network_error: bool = False


class ActivationClient:
    def __init__(self, cloud_base_url: str):
        self.cloud_base_url = str(cloud_base_url or "").rstrip("/")

    def activate(
        self,
        *,
        activation_token: str,
        device_key: str,
        installed_version: str,
        update_channel: str,
    ) -> ActivationResult:
        url = f"{self.cloud_base_url}{ACTIVATE_ENDPOINT}"
        body = {
            "activation_token": activation_token,
            "device_key": device_key,
            "installed_version": installed_version,
            "update_channel": update_channel,
        }
        try:
            response = requests.post(url, json=body, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.RequestException as exc:
            return ActivationResult(
                ok=False,
                status_code=None,
                error_code="network_error",
                error_detail=str(exc),
                payload={},
                network_error=True,
            )
        payload = {}
        try:
            payload = response.json() if response.content else {}
        except Exception:
            payload = {}
        if 200 <= response.status_code < 300:
            return ActivationResult(
                ok=True,
                status_code=response.status_code,
                error_code=None,
                error_detail=None,
                payload=payload if isinstance(payload, dict) else {},
                network_error=False,
            )
        error_code = None
        error_detail = None
        if isinstance(payload, dict):
            error_code = str(payload.get("error") or "") or None
            error_detail = str(payload.get("detail") or payload.get("message") or "") or None
        if not error_code:
            error_code = f"http_{response.status_code}"
        return ActivationResult(
            ok=False,
            status_code=response.status_code,
            error_code=error_code,
            error_detail=error_detail,
            payload=payload if isinstance(payload, dict) else {},
            network_error=False,
        )


@dataclass(frozen=True)
class ActivationBootstrapOutcome:
    state: AgentState
    config: dict[str, Any]
    result: Optional[ActivationResult]


def hydrate_runtime_env_from_activation_config(
    *,
    logger: logging.Logger,
    config: dict[str, Any],
    env_path: Optional[Path] = None,
) -> bool:
    cloud_base_url = str(config.get("cloud_base_url") or "").strip()
    store_id = str(config.get("store_id") or "").strip()
    edge_token = str(config.get("edge_token") or "").strip()
    agent_id = str(config.get("agent_id") or "").strip()
    if not cloud_base_url or not store_id or not edge_token:
        logger.warning(
            "[ACTIVATION] missing activation bootstrap fields for env hydration "
            "(cloud=%s store=%s token=%s)",
            bool(cloud_base_url),
            bool(store_id),
            bool(edge_token),
        )
        return False

    os.environ["CLOUD_BASE_URL"] = cloud_base_url
    os.environ["STORE_ID"] = store_id
    os.environ["EDGE_TOKEN"] = edge_token
    os.environ["DALE_CLOUD_BASE_URL"] = cloud_base_url
    os.environ["DALE_STORE_ID"] = store_id
    os.environ["DALE_EDGE_TOKEN"] = edge_token
    if agent_id:
        os.environ["AGENT_ID"] = agent_id
        os.environ["DALE_AGENT_ID"] = agent_id

    target_env = env_path
    if target_env is None:
        explicit_env = str(os.getenv("DALE_ENV_PATH") or "").strip()
        if explicit_env:
            target_env = Path(explicit_env)
        else:
            config_dir = str(os.getenv("DALE_CONFIG_DIR") or "").strip()
            if config_dir:
                target_env = Path(config_dir) / ".env"
    if target_env is None:
        return True

    target_env.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if target_env.exists():
        try:
            lines = target_env.read_text(encoding="utf-8").splitlines()
        except Exception:
            lines = []

    updates = {
        "CLOUD_BASE_URL": cloud_base_url,
        "STORE_ID": store_id,
        "EDGE_TOKEN": edge_token,
    }
    if agent_id:
        updates["AGENT_ID"] = agent_id

    index_by_key: dict[str, int] = {}
    for i, line in enumerate(lines):
        match = _ENV_LINE_RE.match(line.strip())
        if match:
            index_by_key[match.group(1)] = i

    for key, value in updates.items():
        serialized = f"{key}={value}"
        if key in index_by_key:
            lines[index_by_key[key]] = serialized
        else:
            lines.append(serialized)

    text = "\n".join(lines).rstrip() + "\n"
    target_env.write_text(text, encoding="utf-8")
    logger.info(
        "[ACTIVATION] env hydrated path=%s store_id=%s edge_token_len=%s",
        target_env,
        store_id,
        len(edge_token),
    )
    return True


def _generate_device_key() -> str:
    return f"edge-{uuid.uuid4()}"


def bootstrap_activation(
    *,
    logger: logging.Logger,
    cloud_base_url: str,
    installed_version: str,
    activation_token: Optional[str] = None,
    config_manager: Optional[ConfigManager] = None,
    activation_client: Optional[ActivationClient] = None,
) -> ActivationBootstrapOutcome:
    manager = config_manager or ConfigManager.from_default()
    data = manager.load()
    if cloud_base_url:
        data = manager.update_partial(cloud_base_url=str(cloud_base_url).strip())
    if activation_token:
        data = manager.update_partial(activation_token=str(activation_token).strip())

    has_device = bool(data.get("device_key") and data.get("edge_device_id"))
    sm = StateMachine(logger=logger, initial=AgentState.ACTIVE if has_device else AgentState.UNPROVISIONED)

    if has_device:
        logger.info("[ACTIVATION] bootstrap ready device_key=%s", str(data.get("device_key")))
        return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=None)

    token = str(data.get("activation_token") or "").strip()
    if not token:
        sm.set_state(AgentState.UNPROVISIONED, reason="missing_activation_token")
        logger.warning(
            "[ACTIVATION] missing activation_token and no device identity. "
            "Agent is unprovisioned."
        )
        return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=None)

    sm.set_state(AgentState.ACTIVATING, reason="token_present")
    device_key = str(data.get("device_key") or "").strip() or _generate_device_key()
    update_channel = str(data.get("update_channel") or "stable").strip().lower() or "stable"
    manager.update_partial(device_key=device_key, update_channel=update_channel, installed_version=installed_version)
    data = manager.load()
    if not str(cloud_base_url or "").strip():
        sm.set_state(AgentState.ERROR, reason="missing_cloud_base_url")
        logger.error(
            "[ACTIVATION] CLOUD_BASE_URL ausente para ativacao inicial."
        )
        return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=None)

    client = activation_client or ActivationClient(cloud_base_url=cloud_base_url)
    result = client.activate(
        activation_token=token,
        device_key=device_key,
        installed_version=installed_version,
        update_channel=update_channel,
    )
    if result.ok:
        payload = result.payload if isinstance(result.payload, dict) else {}
        manager.update_partial(
            device_key=str(payload.get("device_key") or device_key),
            store_id=str(payload.get("store_id") or data.get("store_id") or ""),
            edge_token=str(payload.get("edge_token") or data.get("edge_token") or ""),
            edge_device_id=str(payload.get("device_id") or ""),
            update_channel=str(payload.get("update_channel") or update_channel),
            installed_version=str(payload.get("installed_version") or installed_version),
            activation_token=None,
        )
        data = manager.load()
        sm.set_state(AgentState.ACTIVE, reason="activation_success")
        return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=result)

    if result.network_error:
        sm.set_state(AgentState.ACTIVATING, reason="activation_network_retry")
        logger.warning(
            "[ACTIVATION] network error during activation: %s",
            result.error_detail or "unknown",
        )
        return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=result)

    if result.status_code in {401, 403, 409}:
        sm.set_state(AgentState.ERROR, reason=result.error_code or "activation_error")
    else:
        sm.set_state(AgentState.ACTIVATING, reason=result.error_code or "activation_retryable")
    logger.error(
        "[ACTIVATION] activation failed status=%s code=%s detail=%s",
        result.status_code,
        result.error_code,
        result.error_detail,
    )
    return ActivationBootstrapOutcome(state=sm.get_state(), config=data, result=result)
