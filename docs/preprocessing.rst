Preparing support and supplied centres
======================================

RadialPaths operates on NumPy-compatible two-dimensional scalar fields; FITS
support is provided for astronomical use. The radial construction itself still
starts from a support and supplied centres. Image preparation is a separate,
inspectable sequence::

   image
      -> provisional support
      -> centre candidates
      -> selected supplied centres
      -> final connected support
      -> build_geometry(...)

The reference preprocessing identifies local intensity maxima as centre
candidates. The supplied centres used for radial analysis may be selected from
these candidates or provided independently. RadialPaths does not require a
particular segmentation or centre-detection method.

Image input
-----------

NumPy-compatible arrays are the primary input. Optional helpers in
``radialpaths.io`` read FITS through Astropy and grayscale PNG, JPEG, or TIFF
files through Pillow. Raster sample values retain their stored scale. Colour
raster input requires either a zero-based channel index or the explicit
``colour_mode="luminance"`` conversion

.. math::

   Y = 0.2126 R + 0.7152 G + 0.0722 B.

No colour conversion is selected implicitly.

Reference image preparation
---------------------------

The ``paper`` preset reproduces the observational image-preparation rules used
for the JADES examples. It requires a PSF FWHM in pixels and should not be
treated as a universal image-segmentation prescription.

.. code-block:: python

   from radialpaths import build_geometry, radial_profile
   from radialpaths.preprocessing import (
       estimate_background,
       finalize_support,
       find_centre_candidates,
       prepare_support,
       select_centres,
   )

   background = estimate_background(
       image,
       error=error_image,
       psf_fwhm=3.74,
       preset="paper",
   )

   provisional = prepare_support(
       image,
       background=background.background,
       sigma_bg=background.sigma_bg,
       psf_fwhm=3.74,
       preset="paper",
   )

   candidates = find_centre_candidates(
       provisional,
       psf_fwhm=3.74,
       preset="paper",
   )
   centres = candidates.select([0, 2])
   final = finalize_support(provisional.provisional_support, centres)

   geometry = build_geometry(final.support, centres)
   profile = radial_profile(image, geometry, coordinate="rho_X")

Candidate indices are zero-based and follow decreasing smoothed intensity.
Selecting indices is a scientific choice; the package does not infer how many
centres an object should have.

Paper preset
------------

The named preset fixes the following implementation details:

- initial background pixels are the outer 20 per cent border;
- the background centre is the median and
  :math:`\sigma_{\rm bg}=1.4826\,\mathrm{MAD}`;
- at most five background iterations exclude a provisional source mask;
- convergence requires both a 0.02-sigma centre change and a 0.02 fractional
  scale change;
- a positive median error-image value is used only when the MAD is
  non-positive, matching the frozen workflow;
- Gaussian smoothing uses
  :math:`\sigma=\mathrm{FWHM}/2.354820045`;
- support pixels satisfy
  :math:`I_{\rm smooth}\geq I_{\rm bg}+1.5\sigma_{\rm bg}`;
- binary closing and dilation use circular footprints of radius half a PSF
  FWHM;
- internal holes are not filled;
- candidate pixels are local maxima above five background sigmas, using a
  maximum-filter radius of one PSF FWHM;
- connected plateaus collapse to the first brightest pixel in row-major order;
- candidates are ranked by smoothed intensity;
- automatic centre selection uses a minimum separation of two PSF FWHM;
- the final support is the 8-connected component containing every selected
  supplied centre.

The 9-by-9 maximum-filter window in the two published systems follows from
``ceil(3.743...) = 4``; it is not a fixed window size for other PSFs.

Generic pixel-scale preparation
-------------------------------

For images without a PSF model, use ``preset="generic"`` and state the
smoothing, morphology, and local-maximum scales in pixels. These are analysis
choices and remain visible in the result objects.

Invalid pixels
--------------

NaNs, NumPy masked pixels, and a user-provided bad-pixel mask are excluded
from background estimation, candidate detection, and support traversal. They
are not replaced by zeros before thresholding.

External masks and centres
--------------------------

A catalogue segmentation and independently measured centres bypass the
reference preprocessing completely::

   geometry = build_geometry(my_catalogue_mask, my_measured_centres)

This remains the shortest and most direct path when those inputs already
exist.
