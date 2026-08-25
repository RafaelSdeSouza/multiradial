"""Small deterministic supports and tracers for examples and teaching."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

from ._silhouettes import SILHOUETTES_XY


@dataclass(frozen=True)
class SyntheticScene:
    """A support, supplied centres, and two registered demonstration tracers."""

    name: str
    support: NDArray[np.bool_]
    centres: NDArray[np.int64]
    brightness: NDArray[np.float64]
    tracer: NDArray[np.float64]


def _distance_to_segments(
    yy: NDArray[np.float64], xx: NDArray[np.float64], points: list[tuple[float, float]]
) -> NDArray[np.float64]:
    distance = np.full(yy.shape, np.inf)
    for first, second in zip(points[:-1], points[1:]):
        ay, ax = first
        by, bx = second
        dy, dx = by - ay, bx - ax
        length_squared = dy * dy + dx * dx
        fraction = ((yy - ay) * dy + (xx - ax) * dx) / max(length_squared, 1e-12)
        fraction = np.clip(fraction, 0.0, 1.0)
        py, px = ay + fraction * dy, ax + fraction * dx
        distance = np.minimum(distance, np.hypot(yy - py, xx - px))
    return distance


def _inside_polygon(
    yy: NDArray[np.float64],
    xx: NDArray[np.float64],
    points: list[tuple[float, float]],
) -> NDArray[np.bool_]:
    """Rasterize one polygon whose vertices are given as ``(row, column)``."""
    inside = np.zeros(yy.shape, dtype=bool)
    previous_y, previous_x = points[-1]
    for current_y, current_x in points:
        denominator = previous_y - current_y
        if denominator == 0:
            denominator = np.finfo(float).eps
        crosses = (current_y > yy) != (previous_y > yy)
        crossing_x = (
            (previous_x - current_x) * (yy - current_y) / denominator + current_x
        )
        inside ^= crosses & (xx < crossing_x)
        previous_y, previous_x = current_y, current_x
    return inside


def _nearest_support_pixels(
    support: NDArray[np.bool_], candidates: NDArray[np.float64]
) -> NDArray[np.int64]:
    rows, columns = np.nonzero(support)
    selected = []
    for row, column in candidates:
        index = np.argmin((rows - row) ** 2 + (columns - column) ** 2)
        selected.append((rows[index], columns[index]))
    return np.asarray(selected, dtype=np.int64)


def _tracers(
    shape: tuple[int, int], support: NDArray[np.bool_], centres: NDArray[np.int64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    yy, xx = np.indices(shape, dtype=float)
    brightness = np.zeros(shape, dtype=float)
    tracer = 0.25 + 0.55 * xx / max(shape[1] - 1, 1)
    for index, (cy, cx) in enumerate(centres):
        radius = np.hypot(yy - cy, xx - cx)
        brightness += (1.0 - 0.18 * index) * np.exp(-radius / (10.0 + 2.0 * index))
        tracer += 0.12 * (-1) ** index * np.exp(-(radius / 15.0) ** 2)
    brightness += 0.05 * np.sin(xx / 7.0) * np.cos(yy / 9.0)
    brightness[~support] = np.nan
    tracer[~support] = np.nan
    return brightness, tracer


def make_scene(name: str = "folded", size: int = 101) -> SyntheticScene:
    """Create a canonical deterministic demonstration scene.

    Parameters
    ----------
    name : {``"compact"``, ``"folded"``, ``"perforated"``, ``"branched"``,
        ``"capybara"``, ``"trex"``}
        Geometric example.
    size : int, optional
        Square array size. Values below 61 are rejected to keep structures
        resolved for the 30-bin demonstration.
    """
    if size < 61:
        raise ValueError("size must be at least 61 pixels")
    yy, xx = np.indices((size, size), dtype=float)
    scale = size / 101.0
    key = name.lower()

    if key == "compact":
        support = ((xx - 50 * scale) / (37 * scale)) ** 2 + ((yy - 51 * scale) / (30 * scale)) ** 2 <= 1
        support |= (xx - 72 * scale) ** 2 + (yy - 38 * scale) ** 2 <= (13 * scale) ** 2
        centres = np.rint([[48 * scale, 38 * scale], [47 * scale, 64 * scale]]).astype(int)
    elif key == "folded":
        path = [
            (24 * scale, 24 * scale),
            (24 * scale, 73 * scale),
            (49 * scale, 78 * scale),
            (75 * scale, 68 * scale),
            (75 * scale, 30 * scale),
            (55 * scale, 24 * scale),
        ]
        support = _distance_to_segments(yy, xx, path) <= 11 * scale
        centres = np.rint([[24 * scale, 25 * scale], [74 * scale, 31 * scale]]).astype(int)
    elif key == "perforated":
        outer = ((xx - 50 * scale) / (39 * scale)) ** 2 + ((yy - 50 * scale) / (32 * scale)) ** 2 <= 1
        hole = (xx - 52 * scale) ** 2 + (yy - 49 * scale) ** 2 < (12 * scale) ** 2
        support = outer & ~hole
        centres = np.rint([[50 * scale, 25 * scale], [50 * scale, 77 * scale]]).astype(int)
    elif key == "branched":
        trunk = _distance_to_segments(
            yy, xx, [(82 * scale, 50 * scale), (50 * scale, 50 * scale)],
        ) <= 9 * scale
        left = _distance_to_segments(
            yy, xx, [(52 * scale, 50 * scale), (20 * scale, 22 * scale)],
        ) <= 9 * scale
        right = _distance_to_segments(
            yy, xx, [(52 * scale, 50 * scale), (19 * scale, 80 * scale)],
        ) <= 9 * scale
        support = trunk | left | right
        centres = np.rint(
            [[80 * scale, 50 * scale], [21 * scale, 23 * scale], [20 * scale, 79 * scale]]
        ).astype(int)
    elif key in SILHOUETTES_XY:
        silhouette_yx = [
            (y * 100 * scale, x * 100 * scale) for x, y in SILHOUETTES_XY[key]
        ]
        support = _inside_polygon(yy, xx, silhouette_yx)
        labels, component_count = ndimage.label(
            support, structure=np.ones((3, 3), dtype=int)
        )
        if component_count > 1:
            sizes = np.bincount(labels.ravel())
            sizes[0] = 0
            support = labels == sizes.argmax()
        centre_candidates = {
            "capybara": [[47 * scale, 59 * scale], [42 * scale, 24 * scale]],
            "trex": [[50 * scale, 52 * scale], [29 * scale, 84 * scale]],
        }
        centres = _nearest_support_pixels(
            support, np.asarray(centre_candidates[key], dtype=float)
        )
    else:
        raise ValueError(
            "name must be 'compact', 'folded', 'perforated', 'branched', "
            "'capybara', or 'trex'"
        )

    support[[0, -1], :] = False
    support[:, [0, -1]] = False
    brightness, tracer = _tracers(support.shape, support, centres)
    return SyntheticScene(key, support, centres, brightness, tracer)


__all__ = ["SyntheticScene", "make_scene"]
