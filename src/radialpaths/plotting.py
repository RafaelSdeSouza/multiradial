"""Optional Matplotlib helpers with manuscript-consistent semantics."""

from __future__ import annotations

from typing import Optional

import numpy as np

from .geometry import RadialGeometry
from .profiles import RadialProfile
from .preprocessing import CentreCandidates


CENTRE_COLOURS = ("#0072B2", "#D55E00", "#009E73", "#7B61A8")


def _pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:  # pragma: no cover - depends on optional environment
        raise ImportError(
            "Plotting requires Matplotlib; install radialpaths[plot] or radialpaths[demo]"
        ) from error
    return plt


def plot_geometry(
    geometry: RadialGeometry,
    *,
    coordinate: str = "rho_D",
    ax=None,
    contours: bool = True,
):
    """Plot a radial-coordinate field, support outline, and supplied centres.

    Returns the Matplotlib ``Axes`` and image artist.
    """
    plt = _pyplot()
    if ax is None:
        _, ax = plt.subplots(figsize=(4.2, 4.0))
    field = np.ma.masked_where(~geometry.support, geometry.coordinate(coordinate))
    image = ax.imshow(field, origin="upper", cmap="cividis", vmin=0, vmax=1)
    ax.contour(geometry.support.astype(float), levels=[0.5], colors="#343A40", linewidths=1.1)
    if contours:
        ax.contour(
            np.where(geometry.support, field, np.nan),
            levels=[0.25, 0.5, 0.75],
            colors="white",
            linewidths=0.65,
            alpha=0.9,
        )
    for index, (row, column) in enumerate(geometry.centres):
        colour = CENTRE_COLOURS[index % len(CENTRE_COLOURS)]
        ax.scatter(column, row, s=82, facecolor=colour, edgecolor="white", linewidth=2.2, zorder=5)
        ax.scatter(column, row, s=28, facecolor=colour, edgecolor="#20252B", linewidth=0.6, zorder=6)
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax, image


def plot_profile(profile: RadialProfile, *, ax=None, uncertainty: bool = True):
    """Plot centre-conditioned profile medians with optional percentile bands."""
    plt = _pyplot()
    if ax is None:
        _, ax = plt.subplots(figsize=(4.5, 3.4))
    for centre in range(profile.n_centres):
        colour = CENTRE_COLOURS[centre % len(CENTRE_COLOURS)]
        selected = profile.populated[centre]
        if uncertainty:
            ax.fill_between(
                profile.radius[selected],
                profile.p16[centre, selected],
                profile.p84[centre, selected],
                color=colour,
                alpha=0.14,
                linewidth=0,
            )
        ax.plot(
            profile.radius[selected],
            profile.median[centre, selected],
            color=colour,
            linewidth=1.8,
            label=f"Centre {chr(ord('A') + centre)}",
        )
    coordinate_label = r"$\rho_D$" if profile.coordinate == "rho_D" else r"$\rho_X$"
    ax.set(xlim=(0, 1), xlabel=coordinate_label, ylabel="Median tracer")
    for name in ("top", "right"):
        ax.spines[name].set_visible(False)
    ax.tick_params(direction="out", width=0.8)
    ax.legend(frameon=False)
    return ax


def plot_overview(
    data,
    geometry: RadialGeometry,
    *,
    coordinate: str = "rho_D",
    profile: Optional[RadialProfile] = None,
):
    """Plot tracer, coordinate geometry, and profile as a compact narrative."""
    plt = _pyplot()
    if profile is None:
        from .profiles import radial_profile

        profile = radial_profile(data, geometry, coordinate=coordinate)
    figure, axes = plt.subplots(1, 3, figsize=(10.2, 3.25), constrained_layout=True)
    axes[0].imshow(np.ma.masked_where(~geometry.support, data), origin="upper", cmap="gray")
    axes[0].contour(geometry.support.astype(float), levels=[0.5], colors="white", linewidths=0.8)
    axes[0].set_title("Registered tracer")
    axes[0].set(xticks=[], yticks=[])
    plot_geometry(geometry, coordinate=coordinate, ax=axes[1])
    axes[1].set_title("Radial geometry")
    plot_profile(profile, ax=axes[2])
    axes[2].set_title("Centre-conditioned profile")
    return figure, axes


def plot_centre_candidates(
    image,
    candidates: CentreCandidates,
    *,
    selected=None,
    ax=None,
):
    """Plot numbered centre candidates for scientific review.

    Selected and unselected markers are visually distinct. Candidate numbers
    are zero-based and match :attr:`CentreCandidates.rank`.
    """
    plt = _pyplot()
    if ax is None:
        _, ax = plt.subplots(figsize=(5.2, 4.5))
    values = np.asarray(image, dtype=float)
    ax.imshow(values, origin="upper", cmap="gray")
    selected_indices = set() if selected is None else {int(index) for index in selected}
    for rank, (row, column) in enumerate(candidates.positions):
        is_selected = rank in selected_indices
        colour = CENTRE_COLOURS[rank % len(CENTRE_COLOURS)] if is_selected else "#6B737C"
        ax.scatter(
            column,
            row,
            s=92 if is_selected else 68,
            facecolor=colour,
            edgecolor="white",
            linewidth=2.0,
            zorder=4,
        )
        ax.text(
            column + 2.2,
            row - 2.2,
            str(rank),
            color="white",
            fontsize=8.5,
            weight="bold",
            ha="left",
            va="bottom",
            zorder=5,
            bbox={"facecolor": "#20252B", "edgecolor": "none", "pad": 1.4, "alpha": 0.86},
        )
    ax.set(xticks=[], yticks=[])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


__all__ = [
    "CENTRE_COLOURS",
    "plot_centre_candidates",
    "plot_geometry",
    "plot_overview",
    "plot_profile",
]
