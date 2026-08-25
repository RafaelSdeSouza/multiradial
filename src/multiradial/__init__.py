"""Compatibility namespace for the former :mod:`multiradial` import."""

from __future__ import annotations

import importlib
import sys
import warnings


warnings.warn(
    "The 'multiradial' import has been renamed to 'radialpaths'; update imports "
    "before the compatibility namespace is removed.",
    FutureWarning,
    stacklevel=2,
)

from radialpaths import *  # noqa: E402,F401,F403
from radialpaths import __all__, __version__  # noqa: E402,F401


for _name in (
    "geometry",
    "io",
    "plotting",
    "preprocessing",
    "profiles",
    "reproduction",
    "synthetic",
):
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(f"radialpaths.{_name}")

del _name
