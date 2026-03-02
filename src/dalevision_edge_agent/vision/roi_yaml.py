from __future__ import annotations

from typing import Dict, List, Tuple

import yaml

Point = Tuple[int, int]


def load_roi_yaml(path: str) -> tuple[Dict[str, List[Point]], Dict[str, List[Point]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    zones_raw = data.get("zones") or {}
    lines_raw = data.get("lines") or {}

    zones: Dict[str, List[Point]] = {}
    for name, pts in zones_raw.items():
        if not name or not pts:
            continue
        zones[name] = [(int(p[0]), int(p[1])) for p in pts]

    lines: Dict[str, List[Point]] = {}
    for name, pts in lines_raw.items():
        if not name or not pts or len(pts) != 2:
            continue
        lines[name] = [(int(pts[0][0]), int(pts[0][1])), (int(pts[1][0]), int(pts[1][1]))]

    return zones, lines
