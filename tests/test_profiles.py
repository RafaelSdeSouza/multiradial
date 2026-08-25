import unittest

import numpy as np

from multiradial import build_geometry, radial_profile


class ProfileTests(unittest.TestCase):
    def setUp(self):
        yy, xx = np.indices((91, 91))
        self.support = (xx - 45) ** 2 + (yy - 45) ** 2 <= 39**2
        self.geometry = build_geometry(self.support, [(45, 45)])
        self.image = 10.0 - 0.04 * np.hypot(yy - 45, xx - 45)

    def test_validated_defaults_and_endpoint(self):
        result = radial_profile(self.image, self.geometry)
        self.assertEqual(result.coordinate, "rho_D")
        self.assertEqual(result.n_bins, 30)
        self.assertEqual(result.min_pixels, 6)
        self.assertGreater(result.count[0, -1], 6)
        self.assertTrue(np.isfinite(result.median[0, -1]))
        self.assertEqual(int(result.count.sum()), int(self.support.sum()))

    def test_registered_tracers_reuse_geometry(self):
        first = radial_profile(self.image, self.geometry, coordinate="rho_X")
        second = radial_profile(2 * self.image + 3, self.geometry, coordinate="rho_X")
        populated = first.populated & second.populated
        np.testing.assert_allclose(second.median[populated], 2 * first.median[populated] + 3)
        np.testing.assert_array_equal(first.count, second.count)

    def test_small_bins_are_omitted_but_counted(self):
        result = radial_profile(self.image, self.geometry, bins=100, min_pixels=20)
        omitted = result.count < 20
        self.assertTrue(np.any(omitted))
        self.assertTrue(np.all(np.isnan(result.median[omitted])))

    def test_mask_and_shape_validation(self):
        mask = np.zeros_like(self.support)
        mask[:, 45:] = True
        result = radial_profile(self.image, self.geometry, mask=mask)
        self.assertLess(int(result.count.sum()), int(self.support.sum()))
        with self.assertRaisesRegex(ValueError, "does not match"):
            radial_profile(np.ones((2, 2)), self.geometry)


if __name__ == "__main__":
    unittest.main()

