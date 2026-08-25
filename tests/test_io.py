import tempfile
import unittest
from pathlib import Path

import numpy as np

from multiradial import build_geometry
from multiradial.io import load_geometry, save_geometry


class GeometryIOTests(unittest.TestCase):
    def test_npz_round_trip(self):
        yy, xx = np.indices((31, 31))
        support = np.hypot(yy - 15, xx - 15) <= 12
        expected = build_geometry(support, [(15, 15)])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "geometry.npz"
            save_geometry(path, expected)
            actual = load_geometry(path)
        np.testing.assert_array_equal(actual.support, expected.support)
        np.testing.assert_array_equal(actual.labels, expected.labels)
        np.testing.assert_allclose(actual.rho_D, expected.rho_D, equal_nan=True)
        np.testing.assert_allclose(actual.rho_X, expected.rho_X, equal_nan=True)


if __name__ == "__main__":
    unittest.main()

