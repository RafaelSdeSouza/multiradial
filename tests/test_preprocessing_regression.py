import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from radialpaths.preprocessing import (
    estimate_background,
    finalize_support,
    find_centre_candidates,
    prepare_image,
    prepare_support,
)


DATA = Path(__file__).parent / "data"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class JadesPreprocessingRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = DATA / "jades_preprocessing_reference.npz"
        cls.fixture = np.load(cls.path, allow_pickle=False)
        cls.manifest = json.loads(
            (DATA / "jades_preprocessing_manifest.json").read_text(encoding="utf-8")
        )

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    def test_fixture_source_and_checksum(self):
        self.assertIn("run_native_candidate_admission.py", self.manifest["source_implementation"])
        self.assertEqual(self.manifest["fixture_sha256"], sha256(self.path))

    def test_two_published_systems_match_frozen_preprocessing(self):
        for system in ("gzmerger09", "gzmerger29"):
            with self.subTest(system=system):
                image = self.fixture[f"{system}_image"]
                error = self.fixture[f"{system}_error"]
                psf_fwhm = float(self.fixture[f"{system}_psf_fwhm"])
                expected_centres = self.fixture[f"{system}_selected_centres"]

                background = estimate_background(
                    image,
                    preset="paper",
                    psf_fwhm=psf_fwhm,
                    error=error,
                )
                self.assertEqual(background.background, float(self.fixture[f"{system}_background"]))
                self.assertEqual(background.sigma_bg, float(self.fixture[f"{system}_sigma_bg"]))
                self.assertEqual(
                    background.number_of_iterations,
                    int(self.fixture[f"{system}_iterations"]),
                )
                np.testing.assert_array_equal(
                    background.background_mask,
                    self.fixture[f"{system}_background_mask"],
                )

                support = prepare_support(
                    image,
                    background=background.background,
                    sigma_bg=background.sigma_bg,
                    preset="paper",
                    psf_fwhm=psf_fwhm,
                )
                np.testing.assert_array_equal(
                    support.provisional_support,
                    self.fixture[f"{system}_raw_support"],
                )
                final = finalize_support(support.provisional_support, expected_centres)
                np.testing.assert_array_equal(
                    final.support,
                    self.fixture[f"{system}_final_support"],
                )

                frozen_component_support = replace(
                    support,
                    provisional_support=final.support,
                )
                candidates = find_centre_candidates(
                    frozen_component_support,
                    preset="paper",
                    psf_fwhm=psf_fwhm,
                )
                np.testing.assert_array_equal(
                    candidates.positions,
                    self.fixture[f"{system}_candidate_positions"],
                )
                np.testing.assert_array_equal(
                    candidates.peak_values,
                    self.fixture[f"{system}_candidate_values"],
                )
                np.testing.assert_array_equal(candidates.positions[:2], expected_centres)

                prepared = prepare_image(
                    image,
                    preset="paper",
                    psf_fwhm=psf_fwhm,
                    centres=expected_centres,
                    error=error,
                )
                np.testing.assert_array_equal(prepared.support, final.support)
                np.testing.assert_array_equal(prepared.centres, expected_centres)


if __name__ == "__main__":
    unittest.main()
