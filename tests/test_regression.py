import json
import unittest
from pathlib import Path

import numpy as np

from radialpaths import radial_profile
from radialpaths.reproduction import build_paper_geometry


DATA = Path(__file__).parent / "data"


class FrozenRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = np.load(DATA / "reference_geometry_profile.npz", allow_pickle=False)
        cls.manifest = json.loads((DATA / "regression_manifest.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    def test_fixture_has_frozen_provenance(self):
        self.assertIn("prepare_v06_benchmark.py", self.manifest["geometry_source"])
        self.assertIn("make_jades_figure.R", self.manifest["profile_source"])
        self.assertEqual(len(self.manifest["fixture_sha256"]), 64)

    def test_geometry_matches_frozen_arrays(self):
        expected = self.fixture
        geometry = build_paper_geometry(expected["support"], expected["centres"])
        np.testing.assert_array_equal(geometry.labels, expected["labels"])
        np.testing.assert_array_equal(geometry.boundary, expected["boundary"])
        for name in (
            "distances",
            "centre_distance",
            "boundary_distance",
            "rho_D",
            "rho_X",
            "extents",
        ):
            np.testing.assert_allclose(
                getattr(geometry, name), expected[name], rtol=1e-13, atol=1e-13, equal_nan=True
            )

    def test_profiles_match_published_estimator(self):
        expected = self.fixture
        geometry = build_paper_geometry(expected["support"], expected["centres"])
        for coordinate in ("rho_D", "rho_X"):
            profile = radial_profile(expected["image"], geometry, coordinate=coordinate)
            np.testing.assert_array_equal(profile.count, expected[f"{coordinate}_count"])
            for name in ("median", "p16", "p84"):
                np.testing.assert_allclose(
                    getattr(profile, name),
                    expected[f"{coordinate}_{name}"],
                    rtol=1e-13,
                    atol=1e-13,
                    equal_nan=True,
                )


if __name__ == "__main__":
    unittest.main()
