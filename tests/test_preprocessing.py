import unittest

import numpy as np

from radialpaths import build_geometry, radial_profile
from radialpaths.preprocessing import (
    SupportResult,
    estimate_background,
    finalize_support,
    find_centre_candidates,
    prepare_image,
    prepare_support,
    select_centres,
)


def simple_image(shape=(81, 91)):
    rng = np.random.default_rng(1803)
    yy, xx = np.indices(shape, dtype=float)
    image = 10.0 + rng.normal(0.0, 0.2, shape)
    image += 7.0 * np.exp(-((yy - 38) ** 2 + (xx - 29) ** 2) / (2 * 4.0**2))
    image += 5.5 * np.exp(-((yy - 43) ** 2 + (xx - 61) ** 2) / (2 * 5.0**2))
    bridge = (xx >= 29) & (xx <= 61)
    image += 1.2 * np.exp(-((yy - (38 + 5 * (xx - 29) / 32)) / 3.0) ** 2) * bridge
    return image


def prepared_from_smoothed(smoothed, support, background=0.0, sigma_bg=1.0):
    image = np.asarray(smoothed, dtype=float)
    valid = np.isfinite(image)
    return SupportResult(
        image=image,
        smoothed=image,
        background=background,
        sigma_bg=sigma_bg,
        provisional_support=np.asarray(support, dtype=bool),
        threshold=background + 1.5 * sigma_bg,
        smoothing_sigma=1.0,
        closing_radius=1.0,
        dilation_radius=1.0,
        valid_mask=valid,
        metadata={},
    )


class BackgroundTests(unittest.TestCase):
    def test_background_estimator(self):
        image = simple_image()
        result = estimate_background(
            image,
            preset="paper",
            psf_fwhm=3.7,
            error=np.full(image.shape, 0.2),
        )
        self.assertAlmostEqual(result.background, 10.0, delta=0.03)
        self.assertAlmostEqual(result.sigma_bg, 0.2, delta=0.03)
        self.assertGreaterEqual(result.number_of_iterations, 1)
        self.assertLessEqual(result.number_of_iterations, 5)
        self.assertTrue(np.any(result.background_mask))

    def test_constant_image_requires_scatter_or_error(self):
        with self.assertRaisesRegex(ValueError, "scatter is non-positive"):
            estimate_background(
                np.ones((21, 21)),
                preset="generic",
                smoothing_sigma=1.0,
                morphology_radius=1.0,
            )
        result = estimate_background(
            np.ones((21, 21)),
            preset="paper",
            psf_fwhm=3.0,
            error=np.full((21, 21), 0.4),
        )
        self.assertEqual(result.sigma_bg, 0.4)
        self.assertTrue(result.metadata["used_error_fallback"])

    def test_invalid_and_small_images(self):
        image = simple_image((31, 31))
        image[:3, :] = np.nan
        masked = np.ma.array(image, mask=np.zeros_like(image, dtype=bool))
        masked.mask[5:8, 5:8] = True
        result = estimate_background(
            masked,
            preset="generic",
            smoothing_sigma=1.0,
            morphology_radius=1.0,
        )
        self.assertFalse(np.any(result.background_mask[:3, :]))
        self.assertFalse(np.any(result.background_mask[5:8, 5:8]))
        with self.assertRaisesRegex(ValueError, "at least 3 by 3"):
            estimate_background(
                np.ones((2, 8)),
                preset="generic",
                smoothing_sigma=1.0,
                morphology_radius=1.0,
            )


class SupportTests(unittest.TestCase):
    def test_reference_support_threshold(self):
        image = simple_image()
        result = prepare_support(
            image,
            background=10.0,
            sigma_bg=0.2,
            preset="paper",
            psf_fwhm=3.7,
        )
        self.assertEqual(result.threshold, 10.3)
        self.assertAlmostEqual(result.smoothing_sigma, 3.7 / 2.354820045)
        self.assertEqual(result.closing_radius, 1.85)
        self.assertTrue(result.provisional_support[38, 29])
        self.assertTrue(result.provisional_support[43, 61])

    def test_internal_hole_and_bad_pixels_remain_excluded(self):
        yy, xx = np.indices((81, 81), dtype=float)
        radius = np.hypot(yy - 40, xx - 40)
        image = np.where((radius >= 12) & (radius <= 30), 8.0, 0.0)
        bad = np.zeros(image.shape, dtype=bool)
        bad[40, 62] = True
        result = prepare_support(
            image,
            background=0.0,
            sigma_bg=1.0,
            preset="generic",
            smoothing_sigma=0.6,
            closing_radius=1.0,
            dilation_radius=1.0,
            bad_pixel_mask=bad,
        )
        self.assertFalse(result.provisional_support[40, 40])
        self.assertFalse(result.provisional_support[40, 62])

    def test_empty_threshold_fails(self):
        with self.assertRaisesRegex(ValueError, "no traversable pixels"):
            prepare_support(
                np.zeros((31, 31)),
                background=0.0,
                sigma_bg=1.0,
                preset="generic",
                smoothing_sigma=1.0,
                closing_radius=1.0,
                dilation_radius=1.0,
            )


class CandidateTests(unittest.TestCase):
    def test_candidate_detection_order_and_support_restriction(self):
        image = np.zeros((31, 31), dtype=float)
        image[8, 8] = 9.0
        image[22, 21] = 7.0
        image[4, 27] = 12.0
        support = np.zeros_like(image, dtype=bool)
        support[5:27, 4:25] = True
        result = find_centre_candidates(
            prepared_from_smoothed(image, support),
            preset="generic",
            maximum_radius=2.0,
        )
        np.testing.assert_array_equal(result.positions, [[8, 8], [22, 21]])
        np.testing.assert_array_equal(result.rank, [0, 1])
        self.assertFalse(result.detection_mask[4, 27])

    def test_connected_plateau_collapses_deterministically(self):
        image = np.zeros((21, 21), dtype=float)
        image[8:10, 9:11] = 8.0
        support = np.ones_like(image, dtype=bool)
        result = find_centre_candidates(
            prepared_from_smoothed(image, support),
            preset="generic",
            maximum_radius=2.0,
        )
        self.assertEqual(len(result.positions), 1)
        np.testing.assert_array_equal(result.positions[0], [8, 9])

    def test_single_candidate_is_returned_without_inventing_another(self):
        image = np.zeros((19, 19), dtype=float)
        image[9, 10] = 8.0
        candidates = find_centre_candidates(
            prepared_from_smoothed(image, np.ones_like(image, dtype=bool)),
            preset="generic",
            maximum_radius=2.0,
        )
        np.testing.assert_array_equal(candidates.positions, [[9, 10]])
        np.testing.assert_array_equal(select_centres(candidates, n_centres=1), [[9, 10]])

    def test_selection_by_rank_indices_and_external_coordinates(self):
        image = np.zeros((31, 31), dtype=float)
        image[5, 5], image[7, 7], image[24, 24] = 10.0, 9.0, 8.0
        candidates = find_centre_candidates(
            prepared_from_smoothed(image, np.ones_like(image, dtype=bool)),
            preset="generic",
            maximum_radius=1.0,
            selection_min_separation=8.0,
        )
        ranked = select_centres(candidates, n_centres=2)
        np.testing.assert_array_equal(ranked, [[5, 5], [24, 24]])
        np.testing.assert_array_equal(candidates.select([2, 0]), [[24, 24], [5, 5]])
        np.testing.assert_array_equal(
            select_centres(centres=[(4.4, 8.6), (15.2, 16.8)]),
            [[4, 9], [15, 17]],
        )
        with self.assertRaisesRegex(ValueError, "only 2 candidates"):
            select_centres(candidates, n_centres=3)


class FinalizeTests(unittest.TestCase):
    def test_finalize_support_reports_rejected_components_and_touch(self):
        support = np.zeros((25, 25), dtype=bool)
        support[0:12, 2:13] = True
        support[17:22, 18:23] = True
        result = finalize_support(support, [(4, 5), (9, 10)])
        self.assertTrue(result.touches_array_boundary)
        self.assertEqual(result.number_of_pixels, 132)
        self.assertEqual(len(result.rejected_components), 1)

    def test_centres_in_different_components_fail(self):
        support = np.zeros((25, 25), dtype=bool)
        support[2:9, 2:9] = True
        support[15:22, 15:22] = True
        with self.assertRaisesRegex(ValueError, "no single connected"):
            finalize_support(support, [(4, 4), (18, 18)])

    def test_all_true_support_fails_without_inventing_boundary(self):
        with self.assertRaisesRegex(ValueError, "fills the array"):
            finalize_support(np.ones((11, 11), dtype=bool), [(5, 5)])


class CompletePathTests(unittest.TestCase):
    def test_prepare_image_to_geometry_to_profile(self):
        image = simple_image()
        prepared = prepare_image(
            image,
            preset="paper",
            psf_fwhm=3.7,
            n_centres=2,
            error=np.full(image.shape, 0.2),
        )
        geometry = build_geometry(prepared.support, prepared.centres)
        profile = radial_profile(image, geometry, coordinate="rho_X")
        np.testing.assert_array_equal(prepared.centres, [[38, 29], [43, 60]])
        self.assertEqual(prepared.final_support.number_of_pixels, 1120)
        self.assertEqual(geometry.n_centres, 2)
        self.assertEqual(profile.n_centres, 2)
        self.assertEqual(int(profile.count.sum()), 1120)
        self.assertEqual(int(np.count_nonzero(profile.populated)), 49)
        self.assertAlmostEqual(float(np.nansum(profile.median)), 580.8136936042101)

    def test_prepare_image_with_external_centres_bypasses_candidate_selection(self):
        image = simple_image()
        supplied = np.array([[38, 29], [43, 60]])
        prepared = prepare_image(
            image,
            preset="paper",
            psf_fwhm=3.7,
            centres=supplied,
            error=np.full(image.shape, 0.2),
        )
        np.testing.assert_array_equal(prepared.centres, supplied)

    def test_external_mask_and_centres_bypass_preprocessing(self):
        yy, xx = np.indices((41, 51))
        support = ((yy - 20) / 15) ** 2 + ((xx - 25) / 20) ** 2 <= 1
        centres = [(20, 16), (20, 34)]
        geometry = build_geometry(support, centres)
        self.assertEqual(geometry.n_centres, 2)
        np.testing.assert_array_equal(geometry.support, support)

    def test_negative_background_subtracted_image(self):
        image = simple_image() - 11.0
        prepared = prepare_image(
            image,
            preset="generic",
            smoothing_sigma=1.2,
            closing_radius=1.0,
            dilation_radius=1.0,
            maximum_radius=3.0,
            background=-1.0,
            sigma_bg=0.2,
            n_centres=2,
            minimum_separation=8.0,
        )
        self.assertEqual(len(prepared.centres), 2)


if __name__ == "__main__":
    unittest.main()
