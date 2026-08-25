"""Inspectable preparation of support masks and candidate centres from images.

The functions in this module prepare the two formal inputs to the radial
construction: a connected support and supplied centre coordinates. They do not
infer physical nuclei, galaxies, or components.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import ndimage

from .geometry import _readonly


PAPER_GAUSSIAN_FWHM = 2.354820045


def _metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class BackgroundResult:
    """Background location and scatter with the pixels used to estimate them."""

    background: float
    sigma_bg: float
    background_mask: NDArray[np.bool_]
    number_of_iterations: int
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class SupportResult:
    """Intermediate products from threshold-based support preparation."""

    image: NDArray[np.float64]
    smoothed: NDArray[np.float64]
    background: float
    sigma_bg: float
    provisional_support: NDArray[np.bool_]
    threshold: float
    smoothing_sigma: float
    closing_radius: float
    dilation_radius: float
    valid_mask: NDArray[np.bool_]
    metadata: Mapping[str, object]


@dataclass(frozen=True)
class CentreCandidates:
    """Ranked local-intensity maxima considered as possible supplied centres."""

    positions: NDArray[np.int64]
    peak_values: NDArray[np.float64]
    significance: NDArray[np.float64]
    rank: NDArray[np.int64]
    min_separation: float
    selection_min_separation: Optional[float]
    detection_mask: NDArray[np.bool_]
    metadata: Mapping[str, object]

    def select(self, indices: Sequence[int]) -> NDArray[np.int64]:
        """Return candidate positions for explicit zero-based candidate indices."""
        return select_centres(self, indices=indices)


@dataclass(frozen=True)
class FinalSupportResult:
    """One connected support selected after supplied centres are known."""

    support: NDArray[np.bool_]
    component_labels: NDArray[np.int32]
    selected_component: int
    rejected_components: tuple[int, ...]
    number_of_pixels: int
    all_centres_contained: bool
    touches_array_boundary: bool


@dataclass(frozen=True)
class PreparedImage:
    """All decisions made by :func:`prepare_image`, before radial geometry."""

    image: NDArray[np.float64]
    background_result: BackgroundResult
    support_result: SupportResult
    candidates: CentreCandidates
    centres: NDArray[np.int64]
    final_support: FinalSupportResult

    @property
    def background(self) -> float:
        return self.background_result.background

    @property
    def sigma_bg(self) -> float:
        return self.background_result.sigma_bg

    @property
    def smoothed(self) -> NDArray[np.float64]:
        return self.support_result.smoothed

    @property
    def provisional_support(self) -> NDArray[np.bool_]:
        return self.support_result.provisional_support

    @property
    def support(self) -> NDArray[np.bool_]:
        return self.final_support.support


def _image_and_valid(
    image: ArrayLike,
    bad_pixel_mask: Optional[ArrayLike] = None,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    raw = image.value if hasattr(image, "unit") else image
    if np.ma.isMaskedArray(raw):
        masked = np.ma.getmaskarray(raw).astype(bool)
        values = np.asarray(np.ma.getdata(raw), dtype=float)
    else:
        values = np.asarray(raw, dtype=float)
        masked = np.zeros(values.shape, dtype=bool)
    if values.ndim != 2:
        raise ValueError("image must be a two-dimensional scalar array")
    if min(values.shape) < 3:
        raise ValueError("image must be at least 3 by 3 pixels")
    if bad_pixel_mask is not None:
        bad = np.asarray(bad_pixel_mask, dtype=bool)
        if bad.shape != values.shape:
            raise ValueError("bad_pixel_mask must match the image shape")
        masked |= bad
    valid = np.isfinite(values) & ~masked
    if not np.any(valid):
        raise ValueError("image contains no finite, unmasked pixels")
    clean = values.copy()
    clean[~valid] = np.nan
    return clean, valid


def _finite_gaussian_filter(image: NDArray[np.float64], sigma: float) -> NDArray[np.float64]:
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("smoothing sigma must be a positive number of pixels")
    finite = np.isfinite(image)
    filled = np.where(finite, image, 0.0)
    weights = ndimage.gaussian_filter(finite.astype(float), sigma=sigma, mode="constant")
    signal = ndimage.gaussian_filter(filled, sigma=sigma, mode="constant")
    return np.divide(signal, weights, out=np.full_like(signal, np.nan), where=weights > 0)


def _disk(radius: float) -> NDArray[np.bool_]:
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("morphology radius must be a non-negative number of pixels")
    integer_radius = max(1, int(math.ceil(radius)))
    yy, xx = np.indices((2 * integer_radius + 1, 2 * integer_radius + 1))
    return np.hypot(xx - integer_radius, yy - integer_radius) <= radius


def _robust_location_scale(values: ArrayLike, fallback: float = math.nan) -> tuple[float, float, bool]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return math.nan, float(fallback), np.isfinite(fallback) and fallback > 0
    location = float(np.median(finite))
    scale = float(1.4826 * np.median(np.abs(finite - location)))
    used_fallback = not np.isfinite(scale) or scale <= 0
    if used_fallback:
        scale = float(fallback)
    return location, scale, used_fallback


def _scales(
    *,
    preset: str,
    psf_fwhm: Optional[float],
    smoothing_sigma: Optional[float],
    morphology_radius: Optional[float],
) -> tuple[float, float]:
    if preset not in {"generic", "paper"}:
        raise ValueError("preset must be 'generic' or 'paper'")
    if preset == "paper":
        if psf_fwhm is None or not np.isfinite(psf_fwhm) or psf_fwhm <= 0:
            raise ValueError("preset='paper' requires a positive psf_fwhm in pixels")
        return float(psf_fwhm) / PAPER_GAUSSIAN_FWHM, 0.5 * float(psf_fwhm)
    if smoothing_sigma is None or morphology_radius is None:
        raise ValueError(
            "preset='generic' requires smoothing_sigma and morphology_radius in pixels"
        )
    return float(smoothing_sigma), float(morphology_radius)


def estimate_background(
    image: ArrayLike,
    *,
    preset: str = "generic",
    psf_fwhm: Optional[float] = None,
    smoothing_sigma: Optional[float] = None,
    morphology_radius: Optional[float] = None,
    error: Optional[ArrayLike] = None,
    bad_pixel_mask: Optional[ArrayLike] = None,
    border_fraction: float = 0.20,
    threshold_sigma: float = 1.5,
    maximum_iterations: int = 5,
    convergence_centre_sigma: float = 0.02,
    convergence_scale_fraction: float = 0.02,
) -> BackgroundResult:
    """Estimate a background from the image exterior with source exclusion.

    ``preset="paper"`` reproduces the finite iterative estimator used for the
    JADES preparation. It is a reference procedure, not a claim that this
    background model is appropriate for every image.
    """
    values, valid = _image_and_valid(image, bad_pixel_mask)
    sigma, radius = _scales(
        preset=preset,
        psf_fwhm=psf_fwhm,
        smoothing_sigma=smoothing_sigma,
        morphology_radius=morphology_radius,
    )
    if preset == "paper" and not (
        np.isclose(border_fraction, 0.20)
        and np.isclose(threshold_sigma, 1.5)
        and int(maximum_iterations) == 5
        and np.isclose(convergence_centre_sigma, 0.02)
        and np.isclose(convergence_scale_fraction, 0.02)
    ):
        raise ValueError(
            "preset='paper' fixes border_fraction=0.20, threshold_sigma=1.5, "
            "maximum_iterations=5, and both convergence tolerances=0.02"
        )
    if not 0 < border_fraction < 0.5:
        raise ValueError("border_fraction must lie between 0 and 0.5")
    if int(maximum_iterations) != maximum_iterations or maximum_iterations < 1:
        raise ValueError("maximum_iterations must be a positive integer")

    fallback = math.nan
    if error is not None:
        error_values, error_valid = _image_and_valid(error, bad_pixel_mask)
        if error_values.shape != values.shape:
            raise ValueError("error must match the image shape")
        positive = error_valid & np.isfinite(error_values) & (error_values > 0)
        if np.any(positive):
            fallback = float(np.nanmedian(error_values[positive]))

    ny, nx = values.shape
    border_y = max(1, int(math.ceil(border_fraction * ny)))
    border_x = max(1, int(math.ceil(border_fraction * nx)))
    border = np.zeros(values.shape, dtype=bool)
    border[:border_y, :] = True
    border[-border_y:, :] = True
    border[:, :border_x] = True
    border[:, -border_x:] = True
    exterior = border & valid
    location, scale, used_fallback = _robust_location_scale(values[exterior], fallback)
    if not np.isfinite(location):
        raise ValueError("the initial outer image region contains no valid pixels")
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError(
            "background scatter is non-positive; provide an error image or background statistics"
        )

    smoothed = _finite_gaussian_filter(values, sigma)
    structure = _disk(radius)
    iterations = 0
    for index in range(int(maximum_iterations)):
        provisional = valid & np.isfinite(smoothed) & (
            smoothed >= location + float(threshold_sigma) * scale
        )
        provisional = ndimage.binary_closing(provisional, structure=structure)
        provisional = ndimage.binary_dilation(provisional, structure=structure)
        provisional &= valid
        updated_exterior = valid & ~provisional
        new_location, new_scale, fallback_now = _robust_location_scale(
            values[updated_exterior], fallback
        )
        iterations = index + 1
        used_fallback |= fallback_now
        if not np.isfinite(new_location) or not np.isfinite(new_scale) or new_scale <= 0:
            break
        centre_change = abs(new_location - location) / scale
        scale_change = abs(new_scale - scale) / scale
        location, scale, exterior = new_location, new_scale, updated_exterior
        if (
            centre_change <= convergence_centre_sigma
            and scale_change <= convergence_scale_fraction
        ):
            break

    return BackgroundResult(
        background=location,
        sigma_bg=scale,
        background_mask=_readonly(exterior),
        number_of_iterations=iterations,
        metadata=_metadata(
            {
                "preset": preset,
                "border_fraction": float(border_fraction),
                "threshold_sigma": float(threshold_sigma),
                "smoothing_sigma": sigma,
                "morphology_radius": radius,
                "used_error_fallback": bool(used_fallback),
            }
        ),
    )


def prepare_support(
    image: ArrayLike,
    *,
    background: float,
    sigma_bg: float,
    preset: str = "generic",
    psf_fwhm: Optional[float] = None,
    smoothing_sigma: Optional[float] = None,
    closing_radius: Optional[float] = None,
    dilation_radius: Optional[float] = None,
    threshold_sigma: float = 1.5,
    bad_pixel_mask: Optional[ArrayLike] = None,
) -> SupportResult:
    """Construct a provisional support without selecting a component.

    Internal holes are never filled. Invalid and user-masked pixels remain
    excluded from the provisional support.
    """
    values, valid = _image_and_valid(image, bad_pixel_mask)
    if not np.isfinite(background):
        raise ValueError("background must be finite")
    if not np.isfinite(sigma_bg) or sigma_bg <= 0:
        raise ValueError("sigma_bg must be positive and finite")
    if preset == "paper":
        if not np.isclose(threshold_sigma, 1.5):
            raise ValueError("preset='paper' fixes the support threshold at 1.5 sigma_bg")
        sigma, morphology_radius = _scales(
            preset=preset,
            psf_fwhm=psf_fwhm,
            smoothing_sigma=None,
            morphology_radius=None,
        )
        closing = morphology_radius
        dilation = morphology_radius
    elif preset == "generic":
        if smoothing_sigma is None or closing_radius is None or dilation_radius is None:
            raise ValueError(
                "preset='generic' requires smoothing_sigma, closing_radius, and "
                "dilation_radius in pixels"
            )
        sigma = float(smoothing_sigma)
        closing = float(closing_radius)
        dilation = float(dilation_radius)
    else:
        raise ValueError("preset must be 'generic' or 'paper'")

    smoothed = _finite_gaussian_filter(values, sigma)
    threshold = float(background) + float(threshold_sigma) * float(sigma_bg)
    support = valid & np.isfinite(smoothed) & (smoothed >= threshold)
    support = ndimage.binary_closing(support, structure=_disk(closing))
    support = ndimage.binary_dilation(support, structure=_disk(dilation))
    support &= valid
    if not np.any(support):
        raise ValueError("support threshold produced no traversable pixels")

    return SupportResult(
        image=_readonly(values),
        smoothed=_readonly(smoothed),
        background=float(background),
        sigma_bg=float(sigma_bg),
        provisional_support=_readonly(support),
        threshold=threshold,
        smoothing_sigma=sigma,
        closing_radius=closing,
        dilation_radius=dilation,
        valid_mask=_readonly(valid),
        metadata=_metadata(
            {
                "preset": preset,
                "threshold_sigma": float(threshold_sigma),
                "fills_internal_holes": False,
                "touches_array_boundary": bool(
                    np.any(support[[0, -1], :]) or np.any(support[:, [0, -1]])
                ),
            }
        ),
    )


def find_centre_candidates(
    prepared_support: SupportResult,
    *,
    preset: str = "generic",
    psf_fwhm: Optional[float] = None,
    maximum_radius: Optional[float] = None,
    threshold_sigma: float = 5.0,
    selection_min_separation: Optional[float] = None,
) -> CentreCandidates:
    """Rank local maxima on the support-preparation smoothed image.

    The paper preset uses a maximum-filter radius of one PSF FWHM. The separate
    two-FWHM admission separation is stored as the recommended selection
    separation and is applied only when centres are selected automatically.
    """
    if preset == "paper":
        if psf_fwhm is None or not np.isfinite(psf_fwhm) or psf_fwhm <= 0:
            raise ValueError("preset='paper' requires a positive psf_fwhm in pixels")
        radius = float(psf_fwhm)
        if not np.isclose(threshold_sigma, 5.0):
            raise ValueError("preset='paper' fixes the candidate threshold at 5 sigma_bg")
        if selection_min_separation is None:
            selection_min_separation = 2.0 * float(psf_fwhm)
    elif preset == "generic":
        if maximum_radius is None or not np.isfinite(maximum_radius) or maximum_radius <= 0:
            raise ValueError("preset='generic' requires a positive maximum_radius in pixels")
        radius = float(maximum_radius)
    else:
        raise ValueError("preset must be 'generic' or 'paper'")

    image = prepared_support.smoothed
    support = prepared_support.provisional_support & prepared_support.valid_mask
    integer_radius = max(1, int(math.ceil(radius)))
    maxima = image == ndimage.maximum_filter(
        image,
        size=2 * integer_radius + 1,
        mode="constant",
        cval=-np.inf,
    )
    threshold = prepared_support.background + float(threshold_sigma) * prepared_support.sigma_bg
    candidate_pixels = maxima & support & np.isfinite(image) & (image >= threshold)
    plateau_labels, count = ndimage.label(
        candidate_pixels, structure=np.ones((3, 3), dtype=int)
    )
    peaks: list[tuple[int, int, float]] = []
    for label_id in range(1, count + 1):
        yy, xx = np.nonzero(plateau_labels == label_id)
        if yy.size == 0:
            continue
        chosen = int(np.nanargmax(image[yy, xx]))
        peaks.append((int(yy[chosen]), int(xx[chosen]), float(image[yy[chosen], xx[chosen]])))
    peaks.sort(key=lambda item: (-item[2], item[0], item[1]))

    if peaks:
        positions = np.asarray([(row, column) for row, column, _ in peaks], dtype=np.int64)
        values = np.asarray([value for _, _, value in peaks], dtype=float)
    else:
        positions = np.empty((0, 2), dtype=np.int64)
        values = np.empty(0, dtype=float)
    significance = (values - prepared_support.background) / prepared_support.sigma_bg
    ranks = np.arange(len(peaks), dtype=np.int64)
    detection_mask = np.zeros(image.shape, dtype=bool)
    if len(positions):
        detection_mask[positions[:, 0], positions[:, 1]] = True

    return CentreCandidates(
        positions=_readonly(positions),
        peak_values=_readonly(values),
        significance=_readonly(significance),
        rank=_readonly(ranks),
        min_separation=radius,
        selection_min_separation=(
            None if selection_min_separation is None else float(selection_min_separation)
        ),
        detection_mask=_readonly(detection_mask),
        metadata=_metadata(
            {
                "preset": preset,
                "threshold": threshold,
                "threshold_sigma": float(threshold_sigma),
                "maximum_filter_radius": radius,
                "maximum_filter_size": 2 * integer_radius + 1,
                "coordinate_order": "row, column",
            }
        ),
    )


def select_centres(
    candidates: Optional[CentreCandidates] = None,
    *,
    n_centres: Optional[int] = None,
    indices: Optional[Sequence[int]] = None,
    centres: Optional[ArrayLike] = None,
    min_separation: Optional[float] = None,
) -> NDArray[np.int64]:
    """Select supplied centres by rank, candidate indices, or coordinates.

    No value of ``n_centres`` is inferred. Explicit coordinates bypass
    candidate detection entirely.
    """
    methods = sum(item is not None for item in (n_centres, indices, centres))
    if methods != 1:
        raise ValueError("provide exactly one of n_centres, indices, or centres")
    if centres is not None:
        selected = np.asarray(centres, dtype=float)
        if selected.ndim == 1 and selected.size == 2:
            selected = selected[None, :]
        if selected.ndim != 2 or selected.shape[1] != 2 or selected.shape[0] == 0:
            raise ValueError("centres must have shape (n_centres, 2)")
        if not np.all(np.isfinite(selected)):
            raise ValueError("centres must contain only finite coordinates")
        return _readonly(np.rint(selected).astype(np.int64))
    if candidates is None:
        raise ValueError("candidate-based selection requires CentreCandidates")

    if indices is not None:
        chosen = np.asarray(indices, dtype=int)
        if chosen.ndim != 1 or chosen.size == 0:
            raise ValueError("indices must be a non-empty one-dimensional sequence")
        if len(np.unique(chosen)) != chosen.size:
            raise ValueError("candidate indices must be distinct")
        if np.any(chosen < 0) or np.any(chosen >= len(candidates.positions)):
            raise IndexError("candidate index is outside the available range")
        return _readonly(candidates.positions[chosen])

    if int(n_centres) != n_centres or int(n_centres) < 1:
        raise ValueError("n_centres must be a positive integer")
    separation = candidates.selection_min_separation if min_separation is None else min_separation
    separation = 0.0 if separation is None else float(separation)
    if not np.isfinite(separation) or separation < 0:
        raise ValueError("min_separation must be non-negative and finite")
    accepted: list[NDArray[np.int64]] = []
    for position in candidates.positions:
        if all(np.linalg.norm(position - other) >= separation for other in accepted):
            accepted.append(position)
        if len(accepted) == int(n_centres):
            break
    if len(accepted) != int(n_centres):
        raise ValueError(
            f"requested {int(n_centres)} centres but only {len(accepted)} candidates "
            "satisfy the selection separation"
        )
    return _readonly(np.asarray(accepted, dtype=np.int64))


def finalize_support(
    provisional_support: ArrayLike,
    centres: ArrayLike,
    *,
    connectivity: int = 8,
    bad_pixel_mask: Optional[ArrayLike] = None,
) -> FinalSupportResult:
    """Retain the connected provisional component containing all centres."""
    support = np.asarray(provisional_support, dtype=bool)
    if support.ndim != 2:
        raise ValueError("provisional_support must be a two-dimensional mask")
    if bad_pixel_mask is not None:
        bad = np.asarray(bad_pixel_mask, dtype=bool)
        if bad.shape != support.shape:
            raise ValueError("bad_pixel_mask must match the support shape")
        support = support & ~bad
    if not np.any(support):
        raise ValueError("provisional support contains no traversable pixels")
    selected_centres = select_centres(centres=centres)
    inside = (
        (selected_centres[:, 0] >= 0)
        & (selected_centres[:, 0] < support.shape[0])
        & (selected_centres[:, 1] >= 0)
        & (selected_centres[:, 1] < support.shape[1])
    )
    if not np.all(inside):
        raise ValueError("every supplied centre must lie inside the support array")
    if connectivity not in {4, 8}:
        raise ValueError("connectivity must be 4 or 8")
    structure = ndimage.generate_binary_structure(2, 2 if connectivity == 8 else 1)
    labels, count = ndimage.label(support, structure=structure)
    centre_labels = labels[selected_centres[:, 0], selected_centres[:, 1]]
    if np.any(centre_labels == 0):
        raise ValueError("every supplied centre must lie on the provisional support")
    if len(np.unique(centre_labels)) != 1:
        raise ValueError("no single connected support component contains all supplied centres")
    selected_component = int(centre_labels[0])
    final = labels == selected_component
    if np.all(final):
        raise ValueError(
            "the selected support fills the array and has no represented boundary; "
            "provide a larger cutout or an explicit excluded border"
        )
    rejected = tuple(index for index in range(1, count + 1) if index != selected_component)
    touches = bool(np.any(final[[0, -1], :]) or np.any(final[:, [0, -1]]))
    return FinalSupportResult(
        support=_readonly(final),
        component_labels=_readonly(labels.astype(np.int32)),
        selected_component=selected_component,
        rejected_components=rejected,
        number_of_pixels=int(np.count_nonzero(final)),
        all_centres_contained=True,
        touches_array_boundary=touches,
    )


def prepare_image(
    image: ArrayLike,
    *,
    preset: str,
    n_centres: Optional[int] = None,
    selected_candidate_indices: Optional[Sequence[int]] = None,
    centres: Optional[ArrayLike] = None,
    psf_fwhm: Optional[float] = None,
    smoothing_sigma: Optional[float] = None,
    closing_radius: Optional[float] = None,
    dilation_radius: Optional[float] = None,
    maximum_radius: Optional[float] = None,
    minimum_separation: Optional[float] = None,
    background: Optional[float] = None,
    sigma_bg: Optional[float] = None,
    error: Optional[ArrayLike] = None,
    bad_pixel_mask: Optional[ArrayLike] = None,
) -> PreparedImage:
    """Run the inspectable image-to-support-and-centres preparation sequence.

    Exactly one of ``n_centres``, ``selected_candidate_indices``, or ``centres``
    must be provided. The returned object exposes every intermediate product;
    it does not build radial geometry.
    """
    values, valid = _image_and_valid(image, bad_pixel_mask)
    if (background is None) != (sigma_bg is None):
        raise ValueError("background and sigma_bg must be supplied together")
    if background is None:
        background_result = estimate_background(
            values,
            preset=preset,
            psf_fwhm=psf_fwhm,
            smoothing_sigma=smoothing_sigma,
            morphology_radius=(
                closing_radius if closing_radius is not None else dilation_radius
            ),
            error=error,
            bad_pixel_mask=~valid,
        )
    else:
        if not np.isfinite(background) or not np.isfinite(sigma_bg) or sigma_bg <= 0:
            raise ValueError("provided background must be finite and sigma_bg must be positive")
        background_result = BackgroundResult(
            background=float(background),
            sigma_bg=float(sigma_bg),
            background_mask=_readonly(valid),
            number_of_iterations=0,
            metadata=_metadata({"preset": "provided", "used_error_fallback": False}),
        )
    support_result = prepare_support(
        values,
        background=background_result.background,
        sigma_bg=background_result.sigma_bg,
        preset=preset,
        psf_fwhm=psf_fwhm,
        smoothing_sigma=smoothing_sigma,
        closing_radius=closing_radius,
        dilation_radius=dilation_radius,
        bad_pixel_mask=~valid,
    )
    candidates = find_centre_candidates(
        support_result,
        preset=preset,
        psf_fwhm=psf_fwhm,
        maximum_radius=maximum_radius,
        selection_min_separation=minimum_separation,
    )
    methods = sum(
        item is not None for item in (n_centres, selected_candidate_indices, centres)
    )
    if methods != 1:
        raise ValueError(
            "provide exactly one of n_centres, selected_candidate_indices, or centres"
        )
    if centres is not None:
        selected = select_centres(centres=centres)
    elif selected_candidate_indices is not None:
        selected = select_centres(candidates, indices=selected_candidate_indices)
    else:
        selected = select_centres(
            candidates,
            n_centres=n_centres,
            min_separation=minimum_separation,
        )
    final = finalize_support(
        support_result.provisional_support,
        selected,
        connectivity=8,
        bad_pixel_mask=~valid,
    )
    return PreparedImage(
        image=_readonly(values),
        background_result=background_result,
        support_result=support_result,
        candidates=candidates,
        centres=selected,
        final_support=final,
    )


__all__ = [
    "BackgroundResult",
    "CentreCandidates",
    "FinalSupportResult",
    "PreparedImage",
    "SupportResult",
    "estimate_background",
    "finalize_support",
    "find_centre_candidates",
    "prepare_image",
    "prepare_support",
    "select_centres",
]
