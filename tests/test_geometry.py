import unittest

import numpy as np

from multiradial import build_geometry


class GeometryTests(unittest.TestCase):
    def setUp(self):
        yy, xx = np.indices((31, 45))
        self.support = ((xx - 22) / 19) ** 2 + ((yy - 15) / 12) ** 2 <= 1
        self.centres = [(15, 13), (15, 31)]

    def test_centres_and_coordinate_ranges(self):
        geometry = build_geometry(self.support, self.centres)
        self.assertEqual(geometry.n_centres, 2)
        np.testing.assert_array_equal(geometry.centres, self.centres)
        self.assertTrue(np.all(geometry.labels[~self.support] == -1))
        for coordinate in (geometry.rho_D, geometry.rho_X):
            self.assertTrue(np.all(np.isnan(coordinate[~self.support])))
            self.assertGreaterEqual(np.nanmin(coordinate), 0)
            self.assertLessEqual(np.nanmax(coordinate), 1)
        for index, centre in enumerate(self.centres):
            self.assertEqual(geometry.labels[centre], index)
            self.assertEqual(geometry.centre_distance[centre], 0)

    def test_xy_input_order(self):
        geometry = build_geometry(self.support, [(13, 15), (31, 15)], centre_order="xy")
        np.testing.assert_array_equal(geometry.centres, self.centres)

    def test_tie_goes_to_first_supplied_centre(self):
        geometry = build_geometry(self.support, self.centres)
        self.assertEqual(geometry.labels[15, 22], 0)

    def test_invalid_supports_fail_early(self):
        with self.assertRaisesRegex(ValueError, "two-dimensional"):
            build_geometry(np.ones(4), [(0, 0)])
        disconnected = np.zeros((9, 9), bool)
        disconnected[1:3, 1:3] = True
        disconnected[6:8, 6:8] = True
        with self.assertRaisesRegex(ValueError, "8-connected"):
            build_geometry(disconnected, [(1, 1)])
        with self.assertRaisesRegex(ValueError, "True support pixel"):
            build_geometry(self.support, [(0, 0)])


if __name__ == "__main__":
    unittest.main()

