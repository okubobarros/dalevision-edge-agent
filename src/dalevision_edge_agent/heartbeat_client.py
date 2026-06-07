from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .heartbeat import REQUEST_TIMEOUT_SECONDS, send_heartbeat


@dataclass(frozen=True)
class HeartbeatPayload:
    device_key: str
    installed_version: str
    update_channel: str
    status: str
    uptime_seconds: int
    cameras_connected: int
    inference_fps: float
    avg_inference_fps: Optional[float] = None
    enabled_indicators: Optional[list] = None

    def to_extra_data(self) -> dict:
        data: dict = {
            "device_key": self.device_key,
            "installed_version": self.installed_version,
            "update_channel": self.update_channel,
            "status": self.status,
            "uptime_seconds": self.uptime_seconds,
            "cameras_connected": self.cameras_connected,
            "inference_fps": self.inference_fps,
        }
        if self.avg_inference_fps is not None:
            data["avg_inference_fps"] = self.avg_inference_fps
        if self.enabled_indicators is not None:
            data["enabled_indicators"] = self.enabled_indicators
        return data


class HeartbeatClient:
    def send(
        self,
        *,
        url: str,
        edge_token: str,
        store_id: str,
        agent_id: str,
        version: str,
        payload: HeartbeatPayload,
        extra_data: Optional[dict] = None,
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        resolved_extra_data = payload.to_extra_data()
        if isinstance(extra_data, dict) and extra_data:
            resolved_extra_data.update(extra_data)
        return send_heartbeat(
            url=url,
            edge_token=edge_token,
            store_id=store_id,
            agent_id=agent_id,
            version=version,
            timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            extra_data=resolved_extra_data,
        )
