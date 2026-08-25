"""Centre-conditioned radial analysis on irregular supports.

The top-level API deliberately separates construction of radial geometry from
measurement of registered scalar fields.
"""

from ._version import __version__
from .geometry import RadialGeometry, build_geometry
from .profiles import CentreProfile, RadialProfile, radial_profile

__all__ = [
    "CentreProfile",
    "RadialGeometry",
    "RadialProfile",
    "__version__",
    "build_geometry",
    "radial_profile",
]

