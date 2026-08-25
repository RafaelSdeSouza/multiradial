"""Serialization helpers for reusable geometries and registered images."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np

from .geometry import RadialGeometry, _readonly


def save_geometry(path: Union[str, Path], geometry: RadialGeometry) -> None:
    """Save a :class:`~multiradial.RadialGeometry` to a compressed NPZ file."""
    np.savez_compressed(
        path,
        format_version=np.asarray(1, dtype=np.int16),
        support=geometry.support,
        centres=geometry.centres,
        distances=geometry.distances,
        labels=geometry.labels,
        centre_distance=geometry.centre_distance,
        boundary=geometry.boundary,
        boundary_distance=geometry.boundary_distance,
        rho_D=geometry.rho_D,
        rho_X=geometry.rho_X,
        extents=geometry.extents,
    )


def load_geometry(path: Union[str, Path]) -> RadialGeometry:
    """Load a geometry written by :func:`save_geometry`."""
    with np.load(path, allow_pickle=False) as archive:
        version = int(archive["format_version"])
        if version != 1:
            raise ValueError(f"unsupported MultiRadial geometry format version: {version}")
        return RadialGeometry(
            support=_readonly(np.asarray(archive["support"], dtype=bool)),
            centres=_readonly(np.asarray(archive["centres"], dtype=np.int64)),
            distances=_readonly(np.asarray(archive["distances"], dtype=float)),
            labels=_readonly(np.asarray(archive["labels"], dtype=np.int16)),
            centre_distance=_readonly(np.asarray(archive["centre_distance"], dtype=float)),
            boundary=_readonly(np.asarray(archive["boundary"], dtype=bool)),
            boundary_distance=_readonly(np.asarray(archive["boundary_distance"], dtype=float)),
            rho_D=_readonly(np.asarray(archive["rho_D"], dtype=np.float32)),
            rho_X=_readonly(np.asarray(archive["rho_X"], dtype=np.float32)),
            extents=_readonly(np.asarray(archive["extents"], dtype=float)),
        )


def read_fits(path: Union[str, Path], *, extension=0):
    """Read a FITS image lazily through the optional Astropy dependency."""
    try:
        from astropy.io import fits
    except ImportError as error:  # pragma: no cover - depends on optional environment
        raise ImportError("FITS input requires Astropy; install multiradial[io]") from error
    return np.asarray(fits.getdata(path, ext=extension), dtype=float)


__all__ = ["load_geometry", "read_fits", "save_geometry"]
