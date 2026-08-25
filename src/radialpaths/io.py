"""Serialization helpers for reusable geometries and registered images."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import numpy as np

from .geometry import RadialGeometry, _readonly


def save_geometry(path: Union[str, Path], geometry: RadialGeometry) -> None:
    """Save a :class:`~radialpaths.RadialGeometry` to a compressed NPZ file."""
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
            raise ValueError(f"unsupported RadialPaths geometry format version: {version}")
        return RadialGeometry(
            support=_readonly(np.asarray(archive["support"], dtype=bool)),
            centres=_readonly(np.asarray(archive["centres"], dtype=np.int64)),
            distances=_readonly(np.asarray(archive["distances"], dtype=float)),
            labels=_readonly(np.asarray(archive["labels"], dtype=np.int16)),
            centre_distance=_readonly(np.asarray(archive["centre_distance"], dtype=float)),
            boundary=_readonly(np.asarray(archive["boundary"], dtype=bool)),
            boundary_distance=_readonly(np.asarray(archive["boundary_distance"], dtype=float)),
            rho_D=_readonly(np.asarray(archive["rho_D"])),
            rho_X=_readonly(np.asarray(archive["rho_X"])),
            extents=_readonly(np.asarray(archive["extents"], dtype=float)),
        )


def read_fits(path: Union[str, Path], *, extension=0):
    """Read a FITS image lazily through the optional Astropy dependency."""
    try:
        from astropy.io import fits
    except ImportError as error:  # pragma: no cover - depends on optional environment
        raise ImportError("FITS input requires Astropy; install radialpaths[io]") from error
    return np.asarray(fits.getdata(path, ext=extension), dtype=float)


def read_image(
    path: Union[str, Path],
    *,
    channel: Optional[int] = None,
    colour_mode: Optional[str] = None,
):
    """Read a raster image as a two-dimensional scalar array.

    Grayscale PNG, JPEG, and TIFF files are returned directly. For a colour
    image, provide a zero-based ``channel`` or set ``colour_mode="luminance"``.
    The documented luminance conversion is Rec. 709:
    ``0.2126 R + 0.7152 G + 0.0722 B``. No colour conversion is performed
    silently.
    """
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - optional environment
        raise ImportError("raster input requires Pillow; install radialpaths[io]") from error
    with Image.open(path) as opened:
        values = np.asarray(opened, dtype=float)
    if values.ndim == 2:
        if channel is not None or colour_mode is not None:
            raise ValueError("channel and colour_mode apply only to colour raster images")
        return values
    if values.ndim != 3 or values.shape[2] < 3:
        raise ValueError("raster image must be grayscale or have at least three colour channels")
    if (channel is None) == (colour_mode is None):
        raise ValueError("for a colour image, provide exactly one of channel or colour_mode")
    if channel is not None:
        if int(channel) != channel or not 0 <= int(channel) < values.shape[2]:
            raise ValueError("channel is outside the available colour-channel range")
        return values[..., int(channel)]
    if colour_mode != "luminance":
        raise ValueError("colour_mode must be 'luminance'")
    return 0.2126 * values[..., 0] + 0.7152 * values[..., 1] + 0.0722 * values[..., 2]


__all__ = ["load_geometry", "read_fits", "read_image", "save_geometry"]
