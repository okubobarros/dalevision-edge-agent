from __future__ import annotations

from typing import Dict, List, Tuple

import yaml

Point = Tuple[int, int]


def load_config(path: str) -> tuple[Dict[str, List[Point]], Dict[str, List[Point]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    zones = data.get("zones", {}) or {}
    lines = data.get("lines", {}) or {}
    return zones, lines

