#!/usr/bin/env python3
"""Generate the Python-authoritative browser-geometry parity fixture."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from radialpaths import build_geometry, radial_profile


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "data" / "browser_geometry_fixture.json"


def _json_array(values: np.ndarray) -> list:
    array = np.asarray(values)
    if np.issubdtype(array.dtype, np.floating):
        return [None if not np.isfinite(value) else float(value) for value in array.ravel()]
    return array.ravel().tolist()


def main() -> None:
    height, width = 31, 43
    yy, xx = np.indices((height, width), dtype=float)
    support = ((xx - 20) / 17) ** 2 + ((yy - 15) / 12) ** 2 <= 1
    support |= ((xx >= 19) & (xx <= 38) & (np.abs(yy - (15 + 0.32 * (xx - 20))) <= 3))
    support &= (xx - 21) ** 2 + (yy - 14) ** 2 >= 3.6**2
    support[[0, -1], :] = False
    support[:, [0, -1]] = False
    centres = np.array([[13, 10], [19, 34]], dtype=int)

    geometry = build_geometry(support, centres)
    data = np.full((height, width), np.nan, dtype=float)
    data[support] = (
        0.9 * np.exp(-geometry.centre_distance[support] / 8.0)
        + 0.12 * xx[support] / width
        + 0.03 * np.cos(yy[support] / 3.0)
    )
    profiles = {
        name: radial_profile(data, geometry, coordinate=name)
        for name in ("rho_D", "rho_X")
    }

    payload = {
        "description": "Python-authoritative 8-neighbour geometry and 30-bin profile fixture",
        "generator": "tools/generate_browser_fixture.py",
        "width": width,
        "height": height,
        "support": _json_array(support.astype(np.uint8)),
        "centres": centres.tolist(),
        "data": _json_array(data),
        "expected": {
            "labels": _json_array(geometry.labels),
            "centre_distance": _json_array(geometry.centre_distance),
            "boundary": _json_array(geometry.boundary.astype(np.uint8)),
            "boundary_distance": _json_array(geometry.boundary_distance),
            "rho_D": _json_array(geometry.rho_D),
            "rho_X": _json_array(geometry.rho_X),
            "extents": _json_array(geometry.extents),
            "profiles": {
                name: {
                    "count": _json_array(profile.count),
                    "median": _json_array(profile.median),
                }
                for name, profile in profiles.items()
            },
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
