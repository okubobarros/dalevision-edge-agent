import math
from typing import Iterable, Tuple


Point = Tuple[int, int]
Line = Tuple[Point, Point]


def point_in_polygon(px: int, py: int, polygon: Iterable[Point]) -> bool:
    # Lazy import to keep dependency optional.
    import cv2
    import numpy as np

    contour = np.array(list(polygon), dtype=np.int32)
    return cv2.pointPolygonTest(contour, (float(px), float(py)), False) >= 0


def line_side(p1: Point, p2: Point, p: Point) -> float:
    return (p2[0] - p1[0]) * (p[1] - p1[1]) - (p2[1] - p1[1]) * (p[0] - p1[0])


def bucket_index(t_seconds: float, bucket_seconds: int) -> int:
    return int(math.floor(t_seconds / bucket_seconds))

