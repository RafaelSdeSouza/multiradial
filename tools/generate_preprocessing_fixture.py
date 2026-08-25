#!/usr/bin/env python3
"""Derive compact preprocessing fixtures from the frozen JADES products.

This maintenance script is not run during tests. It reads the local paper
inputs and records only the arrays and scalar values needed for offline package
regression tests.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy import ndimage


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]
FROZEN_ROOT = (
    PROJECT_ROOT
    / "radial_letter_v0_1_release"
    / "analysis"
    / "v06_survey_native_benchmark"
)
SOURCE = FROZEN_ROOT / "scripts" / "run_native_candidate_admission.py"
IMPLEMENTATION = FROZEN_ROOT / "config" / "frozen_native_preparation_implementation.json"
ADMISSION = FROZEN_ROOT / "results" / "gz_admission" / "candidate_admission.csv"
ORIGINS = FROZEN_ROOT / "results" / "gz_admission" / "frozen_detected_origins.csv"
OUTPUT = ROOT / "tests" / "data" / "jades_preprocessing_reference.npz"
MANIFEST = ROOT / "tests" / "data" / "jades_preprocessing_manifest.json"
SYSTEMS = ("GZMERGER09", "GZMERGER29")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frozen_module():
    specification = importlib.util.spec_from_file_location("frozen_preprocessing", SOURCE)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    frozen = load_frozen_module()
    implementation = json.loads(IMPLEMENTATION.read_text(encoding="utf-8"))
    admission = {row["candidate_label"]: row for row in csv_rows(ADMISSION)}
    origin_rows = csv_rows(ORIGINS)
    arrays: dict[str, np.ndarray] = {}
    sources: list[dict[str, object]] = []

    for system in SYSTEMS:
        row = admission[system]
        image_path = Path(row["cutout_path"])
        support_path = Path(row["support_path"])
        with fits.open(image_path, memmap=False) as hdul:
            image = np.asarray(hdul["SCI"].data, dtype=float)
            error = np.asarray(hdul["ERR"].data, dtype=float)
        expected_support = np.asarray(fits.getdata(support_path), dtype=bool)
        psf_fwhm = float(row["psf_fwhm_pixels"])
        background, sigma_bg, iterations, exterior = frozen.iterative_background(
            image, error, psf_fwhm, implementation
        )
        smoothed = frozen.finite_gaussian_filter(image, psf_fwhm / 2.354820045)
        raw_support = np.isfinite(smoothed) & (
            smoothed >= background + implementation["support"]["threshold_sigma"] * sigma_bg
        )
        raw_support = ndimage.binary_closing(
            raw_support,
            structure=frozen.disk(
                implementation["support"]["closing_radius_psf_fwhm"] * psf_fwhm
            ),
        )
        raw_support = ndimage.binary_dilation(
            raw_support,
            structure=frozen.disk(
                implementation["support"]["dilation_radius_psf_fwhm"] * psf_fwhm
            ),
        )
        peak_threshold = background + 5.0 * sigma_bg
        peaks = frozen.ranked_peaks(smoothed, expected_support, peak_threshold, psf_fwhm)
        selected = sorted(
            (
                row_item
                for row_item in origin_rows
                if row_item["candidate_label"] == system
            ),
            key=lambda item: int(item["origin_index"]),
        )
        selected_yx = np.asarray(
            [(int(item["y_pixel"]), int(item["x_pixel"])) for item in selected],
            dtype=np.int64,
        )
        peak_positions = np.asarray([(y, x) for y, x, _ in peaks], dtype=np.int64)
        peak_values = np.asarray([value for _, _, value in peaks], dtype=float)

        prefix = system.lower()
        arrays[f"{prefix}_image"] = image
        arrays[f"{prefix}_error"] = error
        arrays[f"{prefix}_raw_support"] = raw_support
        arrays[f"{prefix}_final_support"] = expected_support
        arrays[f"{prefix}_background_mask"] = exterior
        arrays[f"{prefix}_selected_centres"] = selected_yx
        arrays[f"{prefix}_candidate_positions"] = peak_positions
        arrays[f"{prefix}_candidate_values"] = peak_values
        arrays[f"{prefix}_psf_fwhm"] = np.asarray(psf_fwhm)
        arrays[f"{prefix}_background"] = np.asarray(background)
        arrays[f"{prefix}_sigma_bg"] = np.asarray(sigma_bg)
        arrays[f"{prefix}_iterations"] = np.asarray(iterations, dtype=np.int64)
        sources.append(
            {
                "system": system,
                "image": str(image_path.relative_to(PROJECT_ROOT)),
                "image_sha256": sha256(image_path),
                "support": str(support_path.relative_to(PROJECT_ROOT)),
                "support_sha256": sha256(support_path),
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUTPUT, **arrays)
    manifest = {
        "description": "Offline JADES paper-preprocessing regression fixture",
        "systems": list(SYSTEMS),
        "source_implementation": str(SOURCE.relative_to(PROJECT_ROOT)),
        "source_implementation_sha256": sha256(SOURCE),
        "implementation_config": str(IMPLEMENTATION.relative_to(PROJECT_ROOT)),
        "implementation_config_sha256": sha256(IMPLEMENTATION),
        "sources": sources,
        "generator": str(Path(__file__).resolve().relative_to(ROOT)),
        "fixture": str(OUTPUT.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["fixture_sha256"] = sha256(OUTPUT)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"wrote {MANIFEST}")


if __name__ == "__main__":
    main()
