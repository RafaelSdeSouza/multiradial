import unittest

import numpy as np

from radialpaths import build_geometry


class CircularCaseTests(unittest.TestCase):
    def test_single_centred_circle_limits(self):
        yy, xx = np.indices((101, 101))
        radius = np.hypot(yy - 50, xx - 50)
        support = radius <= 40
        geometry = build_geometry(support, [(50, 50)])

        self.assertEqual(geometry.rho_D[50, 50], 0)
        self.assertEqual(geometry.rho_X[50, 50], 0)
        self.assertAlmostEqual(np.nanmax(geometry.rho_D), 1)
        self.assertAlmostEqual(np.nanmax(geometry.rho_X), 1)
        self.assertTrue(np.all(geometry.boundary_distance[geometry.boundary] == 0))
        np.testing.assert_allclose(
            geometry.rho_X[support],
            geometry.centre_distance[support] / np.nanmax(geometry.centre_distance[support]),
        )


if __name__ == "__main__":
    unittest.main()
