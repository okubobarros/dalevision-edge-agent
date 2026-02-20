import logging
from types import SimpleNamespace

from dalevision_edge_agent import main as agent_main


def test_run_once_returns_zero_on_201(monkeypatch) -> None:
    def fake_send_heartbeat(**_kwargs):
        return True, 201, None

    monkeypatch.setattr(agent_main, "send_heartbeat", fake_send_heartbeat)
    settings = SimpleNamespace(edge_token="t", store_id="s", agent_id="a")
    logger = logging.getLogger("test-run-once")
    logger.addHandler(logging.NullHandler())

    exit_code = agent_main._run_once(
        settings=settings,
        url="https://example.com/api/edge/events/",
        version="1.0.0",
        logger=logger,
    )

    assert exit_code == 0
