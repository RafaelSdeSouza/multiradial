import unittest

import numpy as np

from multiradial import build_geometry


class InternalBoundaryTests(unittest.TestCase):
    def setUp(self):
        yy, xx = np.indices((101, 101))
        outer = np.hypot(yy - 50, xx - 50) <= 42
        self.hole = np.hypot(yy - 50, xx - 50) < 15
        self.support = outer & ~self.hole
        self.geometry = build_geometry(self.support, [(50, 24), (50, 76)])

    def test_hole_is_not_traversable(self):
        self.assertTrue(np.all(np.isnan(self.geometry.distances[:, self.hole])))
        self.assertTrue(np.all(self.geometry.labels[self.hole] == -1))
        self.assertTrue(np.all(np.isnan(self.geometry.rho_D[self.hole])))
        self.assertTrue(np.all(np.isnan(self.geometry.rho_X[self.hole])))

    def test_hole_contributes_to_boundary_distance(self):
        yy, xx = np.indices(self.support.shape)
        inner_edge = self.support & (np.hypot(yy - 50, xx - 50) < 17)
        self.assertTrue(np.any(inner_edge & self.geometry.boundary))
        self.assertTrue(np.all(self.geometry.boundary_distance[self.geometry.boundary] == 0))

    def test_graph_path_bends_around_hole(self):
        target = (50, 76)
        direct = np.hypot(target[0] - 50, target[1] - 24)
        self.assertGreater(self.geometry.distances[0][target], direct)


if __name__ == "__main__":
    unittest.main()
