"""Centre-conditioned radial-profile estimators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional, Union

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import RadialGeometry


@dataclass(frozen=True)
class CentreProfile:
    """One centre-associated profile extracted from a :class:`RadialProfile`."""

    centre: int
    coordinate: str
    edges: NDArray[np.float64]
    radius: NDArray[np.float64]
    median: NDArray[np.float64]
    p16: NDArray[np.float64]
    p84: NDArray[np.float64]
    count: NDArray[np.int64]
    unit: Optional[str] = None

    @property
    def populated(self) -> NDArray[np.bool_]:
        """Boolean mask of bins satisfying the minimum-pixel rule."""
        return np.isfinite(self.median)


@dataclass(frozen=True)
class RadialProfile:
    """Centre-conditioned binned profiles for a registered scalar field.

    All two-dimensional result arrays have shape ``(N, n_bins)``, where ``N``
    is the number of supplied centres.
    Omitted bins contain ``NaN`` in the summary arrays while retaining their
    actual pixel count in :attr:`count`.
    """

    coordinate: str
    edges: NDArray[np.float64]
    radius: NDArray[np.float64]
    median: NDArray[np.float64]
    p16: NDArray[np.float64]
    p84: NDArray[np.float64]
    count: NDArray[np.int64]
    min_pixels: int
    unit: Optional[str] = None

    @property
    def values(self) -> NDArray[np.float64]:
        """Alias for the binned median values."""
        return self.median

    @property
    def populated(self) -> NDArray[np.bool_]:
        """Boolean array marking bins that satisfy ``min_pixels``."""
        return np.isfinite(self.median)

    @property
    def n_centres(self) -> int:
        """Number of centre-conditioned profiles."""
        return int(self.median.shape[0])

    @property
    def n_bins(self) -> int:
        """Number of radial bins."""
        return int(self.median.shape[1])

    def for_centre(self, centre: int) -> CentreProfile:
        """Return the profile for one zero-based centre index."""
        if not 0 <= centre < self.n_centres:
            raise IndexError(f"centre must lie in [0, {self.n_centres - 1}]")
        return CentreProfile(
            centre=centre,
            coordinate=self.coordinate,
            edges=self.edges,
            radius=self.radius,
            median=self.median[centre],
            p16=self.p16[centre],
            p84=self.p84[centre],
            count=self.count[centre],
            unit=self.unit,
        )

    def __getitem__(self, centre: int) -> CentreProfile:
        return self.for_centre(centre)

    def __iter__(self) -> Iterator[CentreProfile]:
        for centre in range(self.n_centres):
            yield self.for_centre(centre)


def _profile_edges(bins: Union[int, ArrayLike]) -> NDArray[np.float64]:
    if np.isscalar(bins):
        number = int(bins)
        if number < 1 or float(bins) != number:
            raise ValueError("bins must be a positive integer or an edge array")
        return np.linspace(0.0, 1.0, number + 1)
    edges = np.asarray(bins, dtype=float)
    if edges.ndim != 1 or edges.size < 2:
        raise ValueError("bin edges must be a one-dimensional array of length >= 2")
    if not np.all(np.isfinite(edges)) or not np.all(np.diff(edges) > 0):
        raise ValueError("bin edges must be finite and strictly increasing")
    if not np.isclose(edges[0], 0.0) or not np.isclose(edges[-1], 1.0):
        raise ValueError("radial-profile edges must span [0, 1]")
    edges = edges.copy()
    edges[0], edges[-1] = 0.0, 1.0
    return edges


def _data_values(data: ArrayLike) -> tuple[NDArray[np.float64], Optional[str], NDArray[np.bool_]]:
    unit = str(data.unit) if hasattr(data, "unit") else None
    raw = data.value if hasattr(data, "unit") else data
    if np.ma.isMaskedArray(raw):
        excluded = np.ma.getmaskarray(raw).astype(bool)
        values = np.asarray(np.ma.getdata(raw), dtype=float)
    else:
        values = np.asarray(raw, dtype=float)
        excluded = np.zeros(values.shape, dtype=bool)
    return values, unit, excluded


def radial_profile(
    data: ArrayLike,
    geometry: RadialGeometry,
    *,
    coordinate: str = "rho_D",
    bins: Union[int, ArrayLike] = 30,
    min_pixels: int = 6,
    mask: Optional[ArrayLike] = None,
) -> RadialProfile:
    """Measure unweighted median profiles on a precomputed geometry.

    Parameters
    ----------
    data : array-like, 2D
        Registered scalar field. Non-finite and masked values are excluded.
        An Astropy Quantity is accepted and its unit string is retained.
    geometry : RadialGeometry
        Geometry returned by :func:`radialpaths.build_geometry`.
    coordinate : {``"rho_D"``, ``"rho_X"``}, optional
        Radial coordinate used for binning.
    bins : int or array-like, optional
        Number of equal bins on ``[0, 1]`` or explicit edges spanning that
        interval. The validated default is 30 equal bins.
    min_pixels : int, optional
        Minimum selected pixels required for a populated bin. The validated
        default is six.
    mask : array-like of bool, optional
        Additional exclusion mask, where ``True`` pixels are omitted.

    Returns
    -------
    RadialProfile
        Per-centre counts, unweighted medians, and 16th/84th percentiles.

    Notes
    -----
    Bins are lower-inclusive and upper-exclusive. Values exactly equal to one
    are explicitly included in the final bin, matching the observational
    figure estimator. No spline is fitted.
    """
    values, unit, excluded = _data_values(data)
    if values.shape != geometry.shape:
        raise ValueError(
            f"data shape {values.shape} does not match geometry shape {geometry.shape}"
        )
    if mask is not None:
        extra_mask = np.asarray(mask, dtype=bool)
        if extra_mask.shape != geometry.shape:
            raise ValueError("mask must match the geometry shape")
        excluded = excluded | extra_mask
    if int(min_pixels) != min_pixels or min_pixels < 1:
        raise ValueError("min_pixels must be a positive integer")
    min_pixels = int(min_pixels)

    edges = _profile_edges(bins)
    radius = (edges[:-1] + edges[1:]) / 2.0
    shape = (geometry.n_centres, len(radius))
    medians = np.full(shape, np.nan)
    p16 = np.full(shape, np.nan)
    p84 = np.full(shape, np.nan)
    counts = np.zeros(shape, dtype=np.int64)
    rho = geometry.coordinate(coordinate)
    # Compare bin edges in the coordinate field's dtype. This is ordinarily
    # float64. The explicit paper-reproduction geometry uses float32, matching
    # the serialized JADES coordinate maps and their original bin assignment.
    comparison_edges = edges.astype(rho.dtype, copy=False)
    coordinate_name = "rho_D" if coordinate.lower() == "rho_d" else "rho_X"

    finite = np.isfinite(rho) & np.isfinite(values) & ~excluded
    for centre in range(geometry.n_centres):
        selected = geometry.support & (geometry.labels == centre) & finite
        for index in range(len(radius)):
            use = selected & (rho >= comparison_edges[index]) & (
                rho < comparison_edges[index + 1]
            )
            if index == len(radius) - 1:
                use |= selected & (rho == 1)
            sample = values[use]
            counts[centre, index] = sample.size
            if sample.size < min_pixels:
                continue
            medians[centre, index] = float(np.median(sample))
            p16[centre, index] = float(np.quantile(sample, 0.16))
            p84[centre, index] = float(np.quantile(sample, 0.84))

    for array in (edges, radius, medians, p16, p84, counts):
        array.setflags(write=False)
    return RadialProfile(
        coordinate=coordinate_name,
        edges=edges,
        radius=radius,
        median=medians,
        p16=p16,
        p84=p84,
        count=counts,
        min_pixels=min_pixels,
        unit=unit,
    )


__all__ = ["CentreProfile", "RadialProfile", "radial_profile"]
