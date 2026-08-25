"""Cross-language parity checks for the browser-native geometry core."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "data" / "browser_geometry_fixture.json"
CORE = ROOT / "web" / "assets" / "geometry.js"


def _node_executable() -> str | None:
    requested = os.environ.get("RADIALPATHS_NODE")
    return requested if requested else shutil.which("node")


def _array(values, dtype=float):
    return np.array([np.nan if value is None else value for value in values], dtype=dtype)


def test_browser_geometry_and_profile_match_python_fixture():
    node = _node_executable()
    if node is None:
        pytest.skip("Node.js is not available for browser-core parity testing")

    script = r"""
const fs = require("fs");
const core = require(process.argv[1]);
const fixture = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const geometry = core.buildGeometry(fixture.support, fixture.width, fixture.height, fixture.centres);
const data = fixture.data.map(value => value === null ? NaN : value);
function serial(values) { return Array.from(values, value => Number.isFinite(value) ? value : null); }
const result = {
  labels: serial(geometry.labels),
  centre_distance: serial(geometry.centreDistance),
  boundary: serial(geometry.boundary),
  boundary_distance: serial(geometry.boundaryDistance),
  rho_D: serial(geometry.rhoD),
  rho_X: serial(geometry.rhoX),
  extents: serial(geometry.extents),
  profiles: {},
};
for (const name of ["rho_D", "rho_X"]) {
  const profile = core.radialProfile(data, geometry, name, 30, 6, null);
  result.profiles[name] = { count: profile.counts.flat(), median: serial(profile.medians.flat()) };
}
process.stdout.write(JSON.stringify(result));
"""
    completed = subprocess.run(
        [node, "-e", script, str(CORE), str(FIXTURE)],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = json.loads(completed.stdout)
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))["expected"]

    np.testing.assert_array_equal(actual["labels"], expected["labels"])
    np.testing.assert_array_equal(actual["boundary"], expected["boundary"])
    for name in ("centre_distance", "boundary_distance", "rho_D", "rho_X", "extents"):
        np.testing.assert_allclose(
            _array(actual[name]), _array(expected[name]), rtol=2e-14, atol=2e-14, equal_nan=True
        )
    for coordinate in ("rho_D", "rho_X"):
        np.testing.assert_array_equal(
            actual["profiles"][coordinate]["count"],
            expected["profiles"][coordinate]["count"],
        )
        np.testing.assert_allclose(
            _array(actual["profiles"][coordinate]["median"]),
            _array(expected["profiles"][coordinate]["median"]),
            rtol=2e-14,
            atol=2e-14,
            equal_nan=True,
        )
