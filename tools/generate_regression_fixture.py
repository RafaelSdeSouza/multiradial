#!/usr/bin/env python3
"""Generate the MultiRadial regression fixture from the frozen implementation.

This maintenance tool is not run during tests. It exists so every expected
array has an explicit provenance path back to the paper implementation.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy
import skimage


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "radial_letter_v0_1_release"
    / "analysis"
    / "v06_survey_native_benchmark"
    / "scripts"
    / "prepare_v06_benchmark.py"
)
PROFILE_SOURCE = (
    ROOT
    / "radial_letter_v0_1_release"
    / "mnras_submission"
    / "scripts"
    / "make_jades_figure.R"
)
OUTPUT = ROOT / "tests" / "data" / "reference_geometry_profile.npz"
MANIFEST = ROOT / "tests" / "data" / "regression_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frozen_module():
    specification = importlib.util.spec_from_file_location("frozen_geometry", SOURCE)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def exact_observational_profile(image, support, basin, coordinate, bins=30, minimum=6):
    medians = np.full((2, bins), np.nan)
    p16 = np.full((2, bins), np.nan)
    p84 = np.full((2, bins), np.nan)
    counts = np.zeros((2, bins), dtype=np.int64)
    edges = np.linspace(0.0, 1.0, bins + 1)
    for centre in range(2):
        selected = support & (basin == centre) & np.isfinite(coordinate) & np.isfinite(image)
        for index in range(bins):
            use = selected & (coordinate >= edges[index]) & (coordinate < edges[index + 1])
            if index == bins - 1:
                use |= selected & (coordinate == 1)
            values = image[use]
            counts[centre, index] = values.size
            if values.size < minimum:
                continue
            medians[centre, index] = np.median(values)
            p16[centre, index] = np.quantile(values, 0.16)
            p84[centre, index] = np.quantile(values, 0.84)
    return edges, counts, medians, p16, p84


def main() -> None:
    yy, xx = np.indices((81, 101), dtype=float)
    left = ((xx - 29) / 25) ** 2 + ((yy - 35) / 27) ** 2 <= 1
    right = ((xx - 72) / 24) ** 2 + ((yy - 45) / 25) ** 2 <= 1
    bridge = (yy >= 27) & (yy <= 53) & (xx >= 27) & (xx <= 74)
    hole = (xx - 52) ** 2 + (yy - 40) ** 2 < 7**2
    support = (left | right | bridge) & ~hole
    support[[0, -1], :] = False
    support[:, [0, -1]] = False
    centres = np.asarray([[30, 23], [48, 78]], dtype=int)
    image = (
        3.2 * np.exp(-np.hypot(yy - 30, xx - 23) / 15)
        + 2.4 * np.exp(-np.hypot(yy - 48, xx - 78) / 18)
        + 0.003 * xx
        + 0.02 * np.sin(yy / 4)
    )
    image[~support] = np.nan

    frozen = load_frozen_module()
    basin, rho_d, rho_x, dcore, dboundary, extents = frozen.coordinate_fields(
        support, centres
    )
    # The actual observational consumers read the float32 FITS products written
    # by prepare_v06_benchmark.py:133--134, not the transient float64 arrays.
    rho_d = rho_d.astype(np.float32)
    rho_x = rho_x.astype(np.float32)
    boundary = support & scipy.ndimage.binary_dilation(
        ~support, structure=np.ones((3, 3), dtype=bool)
    )
    distances = np.stack(
        [frozen.distance_from_sources(support, [tuple(centre)]) for centre in centres]
    )
    edges, counts_d, median_d, p16_d, p84_d = exact_observational_profile(
        image, support, basin, rho_d
    )
    _, counts_x, median_x, p16_x, p84_x = exact_observational_profile(
        image, support, basin, rho_x
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUTPUT,
        support=support,
        centres=centres,
        image=image,
        distances=distances,
        labels=basin,
        centre_distance=dcore,
        boundary=boundary,
        boundary_distance=dboundary,
        rho_D=rho_d,
        rho_X=rho_x,
        extents=extents,
        edges=edges,
        rho_D_count=counts_d,
        rho_D_median=median_d,
        rho_D_p16=p16_d,
        rho_D_p84=p84_d,
        rho_X_count=counts_x,
        rho_X_median=median_x,
        rho_X_p16=p16_x,
        rho_X_p84=p84_x,
    )
    manifest = {
        "description": "Non-convex two-centre support with an internal excluded hole",
        "geometry_source": str(SOURCE.relative_to(ROOT)),
        "geometry_source_sha256": sha256(SOURCE),
        "profile_source": str(PROFILE_SOURCE.relative_to(ROOT)),
        "profile_source_sha256": sha256(PROFILE_SOURCE),
        "generator": str(Path(__file__).resolve().relative_to(ROOT)),
        "generator_sha256": sha256(Path(__file__).resolve()),
        "fixture": str(OUTPUT.relative_to(ROOT)),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "scikit_image_version": skimage.__version__,
        "graph": "MCP_Geometric, fully_connected=True, unit in-support costs",
        "profile": "30 bins on [0,1], endpoint included, min 6, unweighted median/p16/p84",
        "coordinate_storage": "rho_D and rho_X cast to float32 as in prepare_v06_benchmark.py:133-134",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["fixture_sha256"] = sha256(OUTPUT)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"wrote {MANIFEST}")


if __name__ == "__main__":
    main()
