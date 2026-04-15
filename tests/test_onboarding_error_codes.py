from dalevision_edge_agent.onboarding_error_codes import (
    map_camera_health_error_to_code,
    map_heartbeat_failure_to_code,
)


def test_map_camera_health_error_to_code() -> None:
    assert map_camera_health_error_to_code("auth_failed") == "NVR_AUTH_FAIL"
    assert map_camera_health_error_to_code("rtsp_timeout") == "RTSP_TIMEOUT"
    assert map_camera_health_error_to_code("connect_failed") == "NVR_UNREACHABLE"


def test_map_heartbeat_failure_to_code() -> None:
    assert map_heartbeat_failure_to_code(401) == "HEARTBEAT_REJECTED"
    assert map_heartbeat_failure_to_code(403) == "HEARTBEAT_REJECTED"
    assert map_heartbeat_failure_to_code(500) == "NVR_UNREACHABLE"
