from __future__ import annotations

from pathlib import Path

import pytest

from dalevision_edge_agent.diagnostics import _parse_ipconfig, run_doctor
from dalevision_edge_agent.cameras import build_rtsp_candidates
from dalevision_edge_agent.rtsp_test import _build_intelbras_rtsp


def test_parse_ipconfig_extracts_ipv4_and_gateway() -> None:
    sample = """
Ethernet adapter:
   IPv4 Address. . . . . . . . . . . : 192.168.5.10
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.5.1
   DNS Servers . . . . . . . . . . . : 8.8.8.8
"""
    parsed = _parse_ipconfig(sample)
    assert parsed["ipv4"] == "192.168.5.10"
    assert parsed["mask"] == "255.255.255.0"
    assert parsed["gateway"] == "192.168.5.1"


def test_doctor_generates_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_cmd(command: str, timeout_seconds: int = 8) -> str:
        if "ipconfig" in command:
            return "IPv4 Address: 192.168.1.10\nSubnet Mask: 255.255.255.0\nDefault Gateway: 192.168.1.1"
        return ""

    monkeypatch.setattr("dalevision_edge_agent.diagnostics._run_cmd", fake_run_cmd)
    monkeypatch.setenv("PROGRAMDATA", str(tmp_path))

    import logging

    log = logging.getLogger("test")
    payload = run_doctor(cloud_base_url="", logger=log, nvr_ip=None, share=False)
    assert "summary" in payload


def test_build_rtsp_candidates_ip_camera() -> None:
    camera = {"ip": "10.0.0.10", "username": "user", "password": "pass"}
    candidates = build_rtsp_candidates(camera)
    assert candidates
    assert candidates[0].startswith("rtsp://user:pass@10.0.0.10:554")


def test_intelbras_template() -> None:
    url = _build_intelbras_rtsp("192.168.1.10", "admin", "1234", 2, 1)
    assert "channel=2" in url
    assert "subtype=1" in url
