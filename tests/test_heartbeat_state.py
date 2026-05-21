from dalevision_edge_agent.activation import AgentState
from dalevision_edge_agent.main import (
    _apply_onboarding_burst_sleep,
    _heartbeat_sleep_seconds,
    _next_agent_state_after_heartbeat,
)


def test_next_state_success_is_active() -> None:
    next_state = _next_agent_state_after_heartbeat(
        current_state=AgentState.DEGRADED,
        ok=True,
        status_code=201,
    )
    assert next_state == AgentState.ACTIVE


def test_next_state_network_error_is_degraded() -> None:
    next_state = _next_agent_state_after_heartbeat(
        current_state=AgentState.ACTIVE,
        ok=False,
        status_code=None,
    )
    assert next_state == AgentState.DEGRADED


def test_next_state_auth_error_is_error() -> None:
    next_state = _next_agent_state_after_heartbeat(
        current_state=AgentState.ACTIVE,
        ok=False,
        status_code=401,
    )
    assert next_state == AgentState.ERROR


def test_degraded_sleep_uses_degraded_interval() -> None:
    interval = _heartbeat_sleep_seconds(
        state=AgentState.DEGRADED,
        active_interval_seconds=30,
        degraded_interval_seconds=300,
        backoff_index=0,
    )
    assert interval == 300


def test_onboarding_burst_clamps_sleep_in_warmup_window() -> None:
    sleep_seconds = _apply_onboarding_burst_sleep(
        base_sleep_seconds=30,
        started_at=100.0,
        now_ts=120.0,
        burst_enabled=True,
        burst_window_seconds=90,
        burst_interval_seconds=5,
    )
    assert sleep_seconds == 5


def test_onboarding_burst_keeps_base_after_window() -> None:
    sleep_seconds = _apply_onboarding_burst_sleep(
        base_sleep_seconds=30,
        started_at=100.0,
        now_ts=220.0,
        burst_enabled=True,
        burst_window_seconds=90,
        burst_interval_seconds=5,
    )
    assert sleep_seconds == 30
