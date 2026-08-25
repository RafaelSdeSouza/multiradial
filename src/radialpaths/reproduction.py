"""Explicit compatibility helpers for reproducing the paper fixtures.

This module is not part of the small top-level analysis API. New analyses
should use :func:`radialpaths.build_geometry`, which returns float64 normalized
coordinates.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from .geometry import RadialGeometry, _build_geometry


def build_paper_geometry(
    support: ArrayLike,
    centres: ArrayLike,
    *,
    centre_order: str = "yx",
    validate_connected: bool = True,
) -> RadialGeometry:
    """Build geometry with the paper's serialized-coordinate semantics.

    This compatibility path retains the serialized-coordinate detail needed by
    the frozen JADES fixtures: ``rho_D`` and ``rho_X`` are cast to float32
    before binning. Exact ties go to the first supplied centre in both the
    public and paper-reproduction constructors.
    Distances and extents remain float64, as in the frozen implementation.
    """
    return _build_geometry(
        support,
        centres,
        centre_order=centre_order,
        validate_connected=validate_connected,
        coordinate_dtype=np.dtype(np.float32),
    )


__all__ = ["build_paper_geometry"]
