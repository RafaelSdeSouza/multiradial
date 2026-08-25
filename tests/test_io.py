import tempfile
import unittest
from pathlib import Path

import numpy as np

from radialpaths import build_geometry
from radialpaths.io import load_geometry, read_fits, read_image, save_geometry


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

    def test_fits_image_input(self):
        from astropy.io import fits

        expected = np.arange(30, dtype=np.float32).reshape(5, 6)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "image.fits"
            fits.writeto(path, expected)
            actual = read_fits(path)
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.float64)

    def test_grayscale_and_explicit_colour_raster_input(self):
        from PIL import Image

        grayscale = np.arange(30, dtype=np.uint8).reshape(5, 6)
        colour = np.stack([grayscale, grayscale + 10, grayscale + 20], axis=-1)
        with tempfile.TemporaryDirectory() as directory:
            grey_path = Path(directory) / "grey.png"
            colour_path = Path(directory) / "colour.png"
            Image.fromarray(grayscale).save(grey_path)
            Image.fromarray(colour).save(colour_path)
            np.testing.assert_array_equal(read_image(grey_path), grayscale)
            np.testing.assert_array_equal(read_image(colour_path, channel=1), colour[..., 1])
            expected_luminance = (
                0.2126 * colour[..., 0]
                + 0.7152 * colour[..., 1]
                + 0.0722 * colour[..., 2]
            )
            np.testing.assert_allclose(
                read_image(colour_path, colour_mode="luminance"), expected_luminance
            )
            with self.assertRaisesRegex(ValueError, "provide exactly one"):
                read_image(colour_path)


if __name__ == "__main__":
    unittest.main()
