from __future__ import annotations

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
