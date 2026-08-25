"""Support-constrained multi-centre radial geometry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import ndimage
from skimage.graph import MCP_Geometric


def _readonly(array: NDArray) -> NDArray:
    """Return a contiguous, read-only copy of an array."""
    result = np.ascontiguousarray(array)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class RadialGeometry:
    r"""Reusable radial geometry for a support and supplied centres.

    Parameters are exposed as arrays so the construction remains inspectable.
    Arrays outside ``support`` are ``NaN`` for continuous fields and ``-1`` for
    ``labels``.

    Attributes
    ----------
    support : ndarray of bool, shape (ny, nx)
        Connected accepted support :math:`\Omega`.
    centres : ndarray of int, shape (n_centres, 2)
        Rounded centre positions in NumPy ``(row, column)`` order.
    distances : ndarray, shape (n_centres, ny, nx)
        Per-centre support-constrained graph distances :math:`d_k(x)`.
    labels : ndarray of int, shape (ny, nx)
        Centre assignment :math:`a(x)`. Outside-support pixels are ``-1``.
    centre_distance : ndarray, shape (ny, nx)
        Distance to the assigned centre.
    boundary : ndarray of bool, shape (ny, nx)
        In-support pixels adjacent to excluded pixels in the 3-by-3
        neighborhood.
    boundary_distance : ndarray, shape (ny, nx)
        Support-constrained distance :math:`b(x)` to the boundary.
    rho_D, rho_X : ndarray, shape (ny, nx)
        Relative depth and normalized progression coordinates.
    extents : ndarray, shape (n_centres,)
        :math:`L_k`, the maximum assigned-centre distance in each region.
    """

    support: NDArray[np.bool_]
    centres: NDArray[np.int64]
    distances: NDArray[np.float64]
    labels: NDArray[np.int16]
    centre_distance: NDArray[np.float64]
    boundary: NDArray[np.bool_]
    boundary_distance: NDArray[np.float64]
    rho_D: NDArray[np.float32]
    rho_X: NDArray[np.float32]
    extents: NDArray[np.float64]

    @property
    def basin(self) -> NDArray[np.int16]:
        """Alias for :attr:`labels`, retained for implementation provenance."""
        return self.labels

    @property
    def n_centres(self) -> int:
        """Number of supplied centres."""
        return int(self.centres.shape[0])

    @property
    def shape(self) -> tuple[int, int]:
        """Spatial array shape."""
        return self.support.shape

    def coordinate(self, name: str) -> NDArray[np.float64]:
        """Return one radial-coordinate field.

        Parameters
        ----------
        name : {``"rho_D"``, ``"rho_X"``}
            Coordinate name. Lower-case spellings ``"rho_d"`` and
            ``"rho_x"`` are accepted.
        """
        normalized = _normalize_coordinate_name(name)
        return self.rho_D if normalized == "rho_D" else self.rho_X

    def region(self, centre: int) -> NDArray[np.bool_]:
        """Return the centre-associated region :math:`B_k` as a mask."""
        if not 0 <= centre < self.n_centres:
            raise IndexError(f"centre must lie in [0, {self.n_centres - 1}]")
        return self.support & (self.labels == centre)


def _normalize_coordinate_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("coordinate must be 'rho_D' or 'rho_X'")
    lookup = {"rho_d": "rho_D", "rho_x": "rho_X"}
    try:
        return lookup[name.lower()]
    except KeyError as error:
        raise ValueError("coordinate must be 'rho_D' or 'rho_X'") from error


def _prepare_centres(
    centres: ArrayLike,
    shape: tuple[int, int],
    centre_order: str,
) -> NDArray[np.int64]:
    values = np.asarray(centres, dtype=float)
    if values.ndim == 1 and values.size == 2:
        values = values[None, :]
    if values.ndim != 2 or values.shape[1] != 2 or values.shape[0] == 0:
        raise ValueError("centres must have shape (n_centres, 2)")
    if not np.all(np.isfinite(values)):
        raise ValueError("centres must contain only finite coordinates")
    if centre_order not in {"yx", "xy"}:
        raise ValueError("centre_order must be 'yx' or 'xy'")
    if centre_order == "xy":
        values = values[:, ::-1]
    rounded = np.rint(values).astype(np.int64)
    if np.unique(rounded, axis=0).shape[0] != rounded.shape[0]:
        raise ValueError("centres must occupy distinct pixels after rounding")
    inside_array = (
        (rounded[:, 0] >= 0)
        & (rounded[:, 0] < shape[0])
        & (rounded[:, 1] >= 0)
        & (rounded[:, 1] < shape[1])
    )
    if not np.all(inside_array):
        raise ValueError("every centre must lie inside the support array")
    return rounded


def _distance_from_sources(
    support: NDArray[np.bool_], sources_yx: Sequence[tuple[int, int]]
) -> NDArray[np.float64]:
    """Run the validated 8-neighbour unit-cost graph distance."""
    costs = np.where(support, 1.0, np.inf)
    distance, _ = MCP_Geometric(costs, fully_connected=True).find_costs(starts=sources_yx)
    distance = np.asarray(distance, dtype=float)
    distance[~support] = np.nan
    return distance


def build_geometry(
    support: ArrayLike,
    centres: ArrayLike,
    *,
    centre_order: str = "yx",
    validate_connected: bool = True,
) -> RadialGeometry:
    r"""Build support-constrained multi-centre radial geometry.

    This function reproduces the validated paper implementation: an
    8-neighbour pixel graph with unit in-support costs, first-centre tie
    assignment, and a boundary made of support pixels touching excluded pixels
    in a 3-by-3 neighborhood.

    Parameters
    ----------
    support : array-like of bool, 2D
        Accepted support :math:`\Omega`. ``True`` pixels are traversable and
        ``False`` pixels—including internal holes—are excluded.
    centres : array-like, shape (n_centres, 2)
        Supplied centre coordinates. Values are rounded with ``numpy.rint`` to
        match the frozen implementation.
    centre_order : {``"yx"``, ``"xy"``}, optional
        Coordinate ordering. The default is NumPy ``(row, column)`` order;
        ``"xy"`` accepts astronomy/plotting-style ``(x, y)`` positions.
    validate_connected : bool, optional
        Require one 8-connected support component. The paper assumes a
        connected support, so the default is ``True``.

    Returns
    -------
    RadialGeometry
        Reusable geometry independent of any subsequently measured tracer.

    Notes
    -----
    The array should contain at least one layer of excluded pixels around its
    outer support if contact with the array edge is intended to be a physical
    boundary. This preserves the frozen boundary expression exactly rather
    than silently padding the input.
    """
    mask = np.asarray(support, dtype=bool)
    if mask.ndim != 2:
        raise ValueError("support must be a two-dimensional array")
    if not np.any(mask):
        raise ValueError("support must contain at least one True pixel")
    mask = np.ascontiguousarray(mask)

    origins = _prepare_centres(centres, mask.shape, centre_order)
    if not np.all(mask[origins[:, 0], origins[:, 1]]):
        raise ValueError("every centre must lie on a True support pixel")

    if validate_connected:
        _, component_count = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
        if component_count != 1:
            raise ValueError(
                "support must be one 8-connected component; "
                f"found {component_count} components"
            )

    distances = np.stack(
        [_distance_from_sources(mask, [tuple(origin)]) for origin in origins]
    )
    finite_distances = np.where(np.isfinite(distances), distances, np.inf)
    labels = np.argmin(finite_distances, axis=0).astype(np.int16)
    labels[~mask] = -1
    centre_distance = np.take_along_axis(
        distances, np.maximum(labels, 0)[None, ...], axis=0
    )[0]

    boundary = mask & ndimage.binary_dilation(
        ~mask, structure=np.ones((3, 3), dtype=bool)
    )
    boundary_sources = [tuple(point) for point in np.argwhere(boundary)]
    if not boundary_sources:
        raise ValueError(
            "support has no represented boundary; pad a full-array support with False pixels"
        )
    boundary_distance = _distance_from_sources(mask, boundary_sources)
    denominator = centre_distance + boundary_distance
    rho_d = np.divide(
        centre_distance,
        denominator,
        out=np.full_like(centre_distance, np.nan),
        where=denominator > 0,
    )

    rho_x = np.full_like(centre_distance, np.nan)
    extents = np.full(len(origins), np.nan)
    for index in range(len(origins)):
        selected = mask & (labels == index)
        if not np.any(selected):
            raise ValueError(
                f"centre {index} has an empty associated region; use distinct, separated centres"
            )
        extent = float(np.nanmax(centre_distance[selected]))
        extents[index] = extent
        rho_x[selected] = centre_distance[selected] / max(
            extent, np.finfo(float).eps
        )

    # The frozen observational preparation serializes both normalized
    # coordinates as float32 before they are binned in Figures 4--5
    # (prepare_v06_benchmark.py:133--134). Preserve that end-to-end behavior:
    # tiny float64-to-float32 changes can move pixels lying exactly on a bin
    # edge even though the coordinate-field error is only about 3e-8.
    rho_d = rho_d.astype(np.float32)
    rho_x = rho_x.astype(np.float32)

    return RadialGeometry(
        support=_readonly(mask),
        centres=_readonly(origins),
        distances=_readonly(distances),
        labels=_readonly(labels),
        centre_distance=_readonly(centre_distance),
        boundary=_readonly(boundary),
        boundary_distance=_readonly(boundary_distance),
        rho_D=_readonly(rho_d),
        rho_X=_readonly(rho_x),
        extents=_readonly(extents),
    )


__all__ = ["RadialGeometry", "build_geometry"]
