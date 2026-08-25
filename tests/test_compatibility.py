import importlib
import unittest
import warnings


class CompatibilityNamespaceTests(unittest.TestCase):
    def test_old_namespace_reexports_canonical_api_with_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            old = importlib.import_module("multiradial")
        canonical = importlib.import_module("radialpaths")
        self.assertIs(old.build_geometry, canonical.build_geometry)
        self.assertIs(old.radial_profile, canonical.radial_profile)
        self.assertTrue(any(item.category is FutureWarning for item in caught))


if __name__ == "__main__":
    unittest.main()
