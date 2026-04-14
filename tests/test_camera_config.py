from dalevision_edge_agent.camera_config import (
    build_camera_processing_plan,
    normalize_indicator_list,
)


def test_normalize_indicator_list_maps_aliases_and_deduplicates():
    assert normalize_indicator_list(["entrada", "flow", "queue_monitoring", "staff"]) == [
        "flow",
        "queue",
        "productivity",
    ]


def test_build_camera_processing_plan_uses_indicators():
    plan = build_camera_processing_plan({"indicators": ["flow", "queue"]})
    assert plan == {
        "flow": True,
        "queue": True,
        "occupancy": False,
        "productivity": False,
    }


def test_build_camera_processing_plan_falls_back_to_role():
    plan = build_camera_processing_plan({"role": "balcao"})
    assert plan["queue"] is True
    assert plan["productivity"] is True
