from __future__ import annotations

from unittest.mock import Mock

from dalevision_edge_agent.vision.worker import VisionWorker
from dalevision_edge_agent.vision.roi_yaml import load_roi_yaml


def test_load_roi_yaml(tmp_path) -> None:
    content = """
zones:
  area_atendimento_fila:
    - [10, 20]
    - [30, 40]
    - [50, 60]
lines:
  linha_entrada_saida:
    - [1, 2]
    - [3, 4]
"""
    path = tmp_path / "roi.yaml"
    path.write_text(content, encoding="utf-8")

    zones, lines = load_roi_yaml(str(path))

    assert "area_atendimento_fila" in zones
    assert zones["area_atendimento_fila"][0] == (10, 20)
    assert "linha_entrada_saida" in lines
    assert lines["linha_entrada_saida"][1] == (3, 4)


def test_local_roi_legacy_zone_names_are_canonicalized() -> None:
    worker = VisionWorker(
        cloud_base_url="https://api.example.com",
        store_id="store-1",
        edge_token="token",
        logger=Mock(),
    )
    cam = {
        "camera_id": "cam-1",
        "zone_id": "zone-cashier",
        "roi_local": {
            "zones": {
                "fila": [(0, 0), (100, 0), (100, 100), (0, 100)],
                "caixa": [(110, 0), (160, 0), (160, 100), (110, 100)],
                "balcao": [(170, 0), (220, 0), (220, 100), (170, 100)],
            },
            "lines": {},
        },
    }

    roi = worker._extract_roi(cam, frame=object())

    assert roi is not None
    assert set(roi["zones"]) == {
        "area_atendimento_fila",
        "ponto_pagamento",
        "zona_funcionario_caixa",
    }
    assert roi["zone_meta"]["area_atendimento_fila"]["metric_type"] == "queue"
    assert roi["zone_meta"]["ponto_pagamento"]["metric_type"] == "checkout_proxy"
    assert roi["zone_meta"]["zona_funcionario_caixa"]["metric_type"] == "checkout_proxy"
    assert worker._infer_role_from_roi(roi["zones"], roi["lines"]) == "balcao"
