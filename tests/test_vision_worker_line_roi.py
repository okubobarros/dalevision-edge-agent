from __future__ import annotations

from unittest.mock import Mock, patch

from dalevision_edge_agent.vision.worker import VisionWorker


def test_process_frame_counts_line_crossing_and_builds_context_payload() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    state = worker._init_camera_state("entrada")
    cam = {
        "id": "cam-entrada-1",
        "camera_id": "cam-entrada-1",
        "zone_id": "zone-front",
        "role": "entrada",
        "roi": {"roi_version": 3},
    }

    roi = {
        "zones": {},
        "lines": {"entrada_principal": [[50, 0], [50, 100]]},
        "zone_meta": {},
        "line_meta": {
            "entrada_principal": {
                "zone_id": "zone-front",
                "roi_entity_id": "line-entrada-principal",
                "metric_type": "entry_exit",
                "ownership": "primary",
            }
        },
    }

    emitted_events: list[dict] = []
    worker._extract_roi = lambda _cam, _frame: roi  # type: ignore[assignment]
    worker._send_crossing_event = lambda **kwargs: emitted_events.append(kwargs)  # type: ignore[assignment]

    worker._yolo_track = lambda _state, _frame: {
        "boxes": [[60, 10, 80, 90, 0, 7]]
    }  # type: ignore[assignment]
    worker._process_frame(state, cam, frame=object(), ts=1.0)

    worker._yolo_track = lambda _state, _frame: {
        "boxes": [[20, 10, 40, 90, 0, 7]]
    }  # type: ignore[assignment]
    worker._process_frame(state, cam, frame=object(), ts=6.0)

    payload = worker._build_payload(cam, state, {}, 0, 30)

    assert state["agg"]["entries"] == 1
    assert state["agg"]["exits"] == 0
    assert payload["traffic"]["footfall"] == 1
    assert payload["traffic"]["entries"] == 1
    assert payload["traffic"]["exits"] == 0
    assert payload["traffic"]["zone_id"] == "zone-front"
    assert payload["traffic"]["roi_entity_id"] == "line-entrada-principal"
    assert payload["traffic"]["metric_type"] == "entry_exit"
    assert payload["ownership"]["mode"] == "single_camera_owner"
    assert len(emitted_events) == 1
    assert emitted_events[0]["direction"] == "entry"
    assert emitted_events[0]["line_meta"]["roi_entity_id"] == "line-entrada-principal"


def test_extract_roi_preserves_line_and_zone_metadata() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    cam = {
        "zone_id": "zone-cashier",
        "roi": {
            "zones": [
                {
                    "id": "queue-zone",
                    "name": "Fila",
                    "type": "poly",
                    "metric_type": "queue",
                    "ownership": "primary",
                    "zone_id": "zone-cashier",
                    "roi_entity_id": "queue-zone",
                    "points": [
                        {"x": 0.1, "y": 0.1},
                        {"x": 0.2, "y": 0.1},
                        {"x": 0.2, "y": 0.2},
                    ],
                }
            ],
            "lines": [
                {
                    "id": "entry-line",
                    "name": "Entrada",
                    "type": "line",
                    "metric_type": "entry_exit",
                    "ownership": "primary",
                    "zone_id": "zone-cashier",
                    "roi_entity_id": "entry-line",
                    "points": [{"x": 0.3, "y": 0.1}, {"x": 0.3, "y": 0.9}],
                }
            ],
        },
    }

    class Frame:
        shape = (100, 100, 3)

    roi = worker._extract_roi(cam, Frame())

    assert roi is not None
    assert roi["zone_meta"]["Fila"]["metric_type"] == "queue"
    assert roi["zone_meta"]["Fila"]["roi_entity_id"] == "queue-zone"
    assert roi["line_meta"]["Entrada"]["metric_type"] == "entry_exit"
    assert roi["line_meta"]["Entrada"]["roi_entity_id"] == "entry-line"


def test_normalize_camera_accepts_snapshot_only_source() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    camera = worker._normalize_camera(
        {
            "id": "cam-1",
            "name": "Cam Snapshot",
            "last_snapshot_url": "https://snapshot.example.com/cam-1.jpg",
        }
    )

    assert camera is not None
    assert camera["camera_id"] == "cam-1"
    assert camera["rtsp_url"] == ""
    assert camera["last_snapshot_url"] == "https://snapshot.example.com/cam-1.jpg"


def test_normalize_camera_accepts_rtsp_alias_fields() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    camera = worker._normalize_camera(
        {
            "id": "cam-2",
            "name": "Cam Stream",
            "stream_url": "rtsp://example.com/live",
        }
    )

    assert camera is not None
    assert camera["camera_id"] == "cam-2"
    assert camera["rtsp_url"] == "rtsp://example.com/live"


def test_process_frame_emits_queue_state_with_queue_roi_context() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    state = worker._init_camera_state("balcao")
    cam = {
        "id": "cam-cashier-1",
        "camera_id": "cam-cashier-1",
        "zone_id": "zone-cashier",
        "role": "balcao",
        "roi": {"roi_version": 5},
    }

    roi = {
        "zones": {
            "area_atendimento_fila": [[0, 0], [100, 0], [100, 100], [0, 100]],
            "zona_funcionario_caixa": [[120, 0], [200, 0], [200, 100], [120, 100]],
        },
        "lines": {},
        "zone_meta": {
            "area_atendimento_fila": {
                "zone_id": "zone-cashier",
                "roi_entity_id": "queue-zone-1",
                "metric_type": "queue",
                "ownership": "primary",
            },
            "zona_funcionario_caixa": {
                "zone_id": "zone-cashier",
                "roi_entity_id": "staff-zone-1",
                "metric_type": "checkout_proxy",
                "ownership": "primary",
            },
        },
        "line_meta": {},
    }

    emitted_events: list[dict] = []
    worker._extract_roi = lambda _cam, _frame: roi  # type: ignore[assignment]
    worker._send_queue_state_event = lambda **kwargs: emitted_events.append(kwargs)  # type: ignore[assignment]
    worker._yolo_track = lambda _state, _frame: {
        "boxes": [
            [10, 10, 30, 90, 0, 1],
            [40, 10, 60, 90, 0, 2],
            [140, 10, 170, 90, 0, 3],
        ]
    }  # type: ignore[assignment]

    worker._process_frame(state, cam, frame=object(), ts=12.0)

    assert len(emitted_events) == 1
    assert emitted_events[0]["queue_length"] == 2
    assert emitted_events[0]["staff_active_est"] == 1
    assert emitted_events[0]["roi"]["zone_meta"]["area_atendimento_fila"]["roi_entity_id"] == "queue-zone-1"


def test_process_frame_emits_checkout_proxy_when_payment_cycle_finishes() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    state = worker._init_camera_state("balcao")
    cam = {
        "id": "cam-cashier-1",
        "camera_id": "cam-cashier-1",
        "zone_id": "zone-cashier",
        "role": "balcao",
        "roi": {"roi_version": 5},
    }

    roi = {
        "zones": {
            "ponto_pagamento": [[0, 0], [100, 0], [100, 100], [0, 100]],
            "zona_funcionario_caixa": [[120, 0], [200, 0], [200, 100], [120, 100]],
        },
        "lines": {},
        "zone_meta": {
            "ponto_pagamento": {
                "zone_id": "zone-cashier",
                "roi_entity_id": "checkout-zone-1",
                "metric_type": "checkout_proxy",
                "ownership": "primary",
            },
            "zona_funcionario_caixa": {
                "zone_id": "zone-cashier",
                "roi_entity_id": "staff-zone-1",
                "metric_type": "checkout_proxy",
                "ownership": "primary",
            },
        },
        "line_meta": {},
    }

    emitted_events: list[dict] = []
    worker._extract_roi = lambda _cam, _frame: roi  # type: ignore[assignment]
    worker._send_queue_state_event = lambda **kwargs: None  # type: ignore[assignment]
    worker._send_checkout_proxy_event = lambda **kwargs: emitted_events.append(kwargs)  # type: ignore[assignment]

    worker._yolo_track = lambda _state, _frame: {
        "boxes": [
            [10, 10, 30, 90, 0, 1],
            [140, 10, 170, 90, 0, 2],
        ]
    }  # type: ignore[assignment]
    worker._process_frame(state, cam, frame=object(), ts=10.0)

    worker._yolo_track = lambda _state, _frame: {
        "boxes": [
            [140, 10, 170, 90, 0, 2],
        ]
    }  # type: ignore[assignment]
    worker._process_frame(state, cam, frame=object(), ts=28.0)

    assert state["agg"]["checkout_events"] == 1
    assert len(emitted_events) == 1
    assert emitted_events[0]["duration_seconds"] == 18
    assert emitted_events[0]["interaction_count"] == 1
    assert emitted_events[0]["roi"]["zone_meta"]["ponto_pagamento"]["roi_entity_id"] == "checkout-zone-1"


def test_process_frame_emits_zone_occupancy_with_room_roi_context() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    state = worker._init_camera_state("salao")
    cam = {
        "id": "cam-room-1",
        "camera_id": "cam-room-1",
        "zone_id": "zone-dining",
        "role": "salao",
        "roi": {"roi_version": 6},
    }

    roi = {
        "zones": {
            "area_consumo": [[0, 0], [100, 0], [100, 100], [0, 100]],
        },
        "lines": {},
        "zone_meta": {
            "area_consumo": {
                "zone_id": "zone-dining",
                "roi_entity_id": "occupancy-zone-1",
                "metric_type": "occupancy",
                "ownership": "primary",
            }
        },
        "line_meta": {},
    }

    emitted_events: list[dict] = []
    worker._extract_roi = lambda _cam, _frame: roi  # type: ignore[assignment]
    worker._send_zone_occupancy_event = lambda **kwargs: emitted_events.append(kwargs)  # type: ignore[assignment]
    worker._yolo_track = lambda _state, _frame: {
        "boxes": [
            [10, 10, 30, 90, 0, 1],
            [40, 10, 60, 90, 0, 2],
            [140, 10, 170, 90, 0, 3],
        ]
    }  # type: ignore[assignment]

    worker._process_frame(state, cam, frame=object(), ts=15.0)
    worker._process_frame(state, cam, frame=object(), ts=27.0)
    payload = worker._build_payload(cam, state, {}, 0, 30)

    assert len(emitted_events) == 2
    assert emitted_events[-1]["occupancy_count"] == 2
    assert emitted_events[-1]["dwell_seconds_est"] == 12
    assert emitted_events[-1]["roi"]["zone_meta"]["area_consumo"]["roi_entity_id"] == "occupancy-zone-1"
    assert payload["traffic"]["engaged"] == 2
    assert payload["traffic"]["dwell_seconds_avg"] == 12


@patch("dalevision_edge_agent.vision.worker.requests.post")
def test_send_retail_event_uses_contract_v1(mock_post: Mock) -> None:
    mock_response = Mock()
    mock_response.status_code = 201
    mock_post.return_value = mock_response

    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    worker._send_retail_event(
        event_type="queue_length",
        value=6,
        ts="2026-03-15T10:32:00Z",
        camera_id="cam-1",
        zone_id="zone-front",
        roi_entity_id="queue-zone-1",
        metric_type="queue",
        confidence=0.92,
    )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["event_name"] == "retail.event.v1"
    assert payload["idempotency_key"] == payload["receipt_id"]
    assert payload["data"]["event_type"] == "queue_length"
    assert payload["data"]["value"] == 6
    assert payload["data"]["source"] == "edge"
    assert payload["data"]["confidence"] == 0.92
