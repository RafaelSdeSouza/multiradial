"""Tests for the deterministic teaching supports."""

import pytest

from radialpaths import build_geometry
from radialpaths.synthetic import make_scene


@pytest.mark.parametrize("name", ["capybara", "trex"])
@pytest.mark.parametrize("size", [61, 80, 101, 112])
def test_playful_supports_are_connected_and_buildable(name, size):
    scene = make_scene(name, size=size)
    geometry = build_geometry(scene.support, scene.centres)

    assert geometry.n_centres == 2
    assert scene.support[tuple(scene.centres[0])]
    assert scene.support[tuple(scene.centres[1])]
    assert geometry.support.sum() == scene.support.sum()
