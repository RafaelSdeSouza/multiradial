"""Browser-ready Panel explorer for MultiRadial synthetic geometries.

Run locally with ``panel serve app/explorer.py --show`` or convert it to a
serverless Pyodide application with ``tools/build_pages.py``.
"""

from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
import panel as pn
from matplotlib.patches import Rectangle

from multiradial import build_geometry, radial_profile
from multiradial.plotting import CENTRE_COLOURS, plot_geometry, plot_profile
from multiradial.synthetic import make_scene


pn.extension(
    sizing_mode="stretch_width",
    raw_css=[
        """
        :root {
          --mr-ink: #1f2933;
          --mr-muted: #5f6b76;
          --mr-line: #d8dee4;
          --mr-paper: #ffffff;
          --mr-wash: #f5f7f8;
          --mr-teal: #2a9d8f;
        }
        body { background: var(--mr-wash); color: var(--mr-ink); }
        .mr-shell { margin: 0 auto; }
        .mr-header {
          border-bottom: 1px solid var(--mr-line);
          margin-bottom: 0.8rem;
          padding: 0.2rem 0 0.9rem;
        }
        .mr-header h1 { font-size: 1.75rem; margin: 0 0 0.2rem; }
        .mr-header p { color: var(--mr-muted); margin: 0; }
        .mr-note {
          background: #eef7f5;
          border-left: 3px solid var(--mr-teal);
          border-radius: 2px;
          color: var(--mr-ink);
          padding: 0.65rem 0.8rem;
        }
        .mr-settings { color: var(--mr-muted); font-size: 0.86rem; }
        @media (max-width: 640px) {
          .mr-header h1 { font-size: 1.45rem; }
          .mr-shell { padding-left: 0.1rem; padding-right: 0.1rem; }
        }
        """
    ],
)


shape = pn.widgets.Select(
    name="Support geometry",
    value="folded",
    options={
        "Compact irregular": "compact",
        "Folded support": "folded",
        "Perforated support": "perforated",
        "Branched support": "branched",
    },
    width=240,
)
coordinate = pn.widgets.Select(
    name="Coordinate",
    value="rho_D",
    options={
        "Boundary depth ρ_D": "rho_D",
        "Normalized progression ρ_X": "rho_X",
    },
    width=240,
)
tracer = pn.widgets.Select(
    name="Registered tracer",
    value="brightness",
    options={"Brightness": "brightness", "Secondary tracer": "tracer"},
    width=240,
)


@lru_cache(maxsize=None)
def _scene_and_geometry(shape_name):
    """Build each immutable support geometry once and reuse it across tracers."""
    scene = make_scene(shape_name)
    geometry = build_geometry(scene.support, scene.centres)
    return scene, geometry


def _mark_centres(ax, geometry):
    for index, (row, column) in enumerate(geometry.centres):
        colour = CENTRE_COLOURS[index % len(CENTRE_COLOURS)]
        ax.scatter(
            column,
            row,
            s=82,
            facecolor=colour,
            edgecolor="white",
            linewidth=2.2,
            zorder=5,
        )
        ax.scatter(
            column,
            row,
            s=28,
            facecolor=colour,
            edgecolor="#20252B",
            linewidth=0.6,
            zorder=6,
        )


def _coordinate_title(name, *, selected):
    prefix = "Selected" if selected else "Comparison"
    if name == "rho_D":
        return rf"{prefix}: boundary depth $\rho_D$"
    return rf"{prefix}: progression $\rho_X$"


def _explorer_figure(scene, geometry, field_name, selected_coordinate):
    field = getattr(scene, field_name)
    other_coordinate = "rho_X" if selected_coordinate == "rho_D" else "rho_D"
    profile = radial_profile(field, geometry, coordinate=selected_coordinate)

    figure, axes = plt.subplots(2, 2, figsize=(9.2, 7.0), constrained_layout=True)

    tracer_ax = axes[0, 0]
    tracer_ax.imshow(np.ma.masked_where(~geometry.support, field), origin="upper", cmap="gray")
    tracer_ax.contour(
        geometry.support.astype(float), levels=[0.5], colors="white", linewidths=0.85
    )
    _mark_centres(tracer_ax, geometry)
    tracer_ax.set_title("Registered scalar field")
    tracer_ax.set(xticks=[], yticks=[])
    for spine in tracer_ax.spines.values():
        spine.set_visible(False)

    selected_ax = axes[0, 1]
    plot_geometry(geometry, coordinate=selected_coordinate, ax=selected_ax)
    selected_ax.set_title(_coordinate_title(selected_coordinate, selected=True), color="#176f66")
    selected_ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            transform=selected_ax.transAxes,
            fill=False,
            edgecolor="#2a9d8f",
            linewidth=2.0,
            clip_on=False,
        )
    )

    comparison_ax = axes[1, 0]
    plot_geometry(geometry, coordinate=other_coordinate, ax=comparison_ax)
    comparison_ax.set_title(_coordinate_title(other_coordinate, selected=False), color="#5f6b76")

    profile_ax = axes[1, 1]
    plot_profile(profile, ax=profile_ax)
    profile_ax.set_title("Centre-conditioned profile")
    profile_ax.set_ylabel("Median tracer")

    return figure


COORDINATE_NOTES = {
    "rho_D": (
        "**Selected: relative centre–boundary depth ρ_D.** It responds to the "
        "nearest local boundary, so a narrow lateral edge can be reached early. "
        "The ρ_X panel remains visible for direct comparison."
    ),
    "rho_X": (
        "**Selected: normalized progression ρ_X.** It measures distance away from "
        "each supplied centre relative to the furthest point in its associated region. "
        "The ρ_D panel remains visible for direct comparison."
    ),
}


@pn.depends(shape, coordinate, tracer)
def view(shape, coordinate, tracer):
    scene, geometry = _scene_and_geometry(shape)
    figure = _explorer_figure(scene, geometry, tracer, coordinate)
    pane = pn.pane.Matplotlib(
        figure,
        format="svg",
        tight=True,
        sizing_mode="stretch_width",
        max_width=970,
    )
    plt.close(figure)
    return pn.Column(
        pn.pane.Markdown(COORDINATE_NOTES[coordinate], css_classes=["mr-note"]),
        pane,
        sizing_mode="stretch_width",
    )


header = pn.pane.HTML(
    """
    <div class="mr-header">
      <h1>MultiRadial interactive explorer</h1>
      <p>Inspect how local boundary depth and normalized progression respond to the same accepted support.</p>
    </div>
    """
)

controls = pn.Card(
    pn.FlexBox(shape, coordinate, tracer, flex_wrap="wrap", gap="0.8rem"),
    pn.pane.Markdown(
        "Geometry is built from the support and supplied centres only. Switching the "
        "registered tracer reuses that same geometry.",
    ),
    pn.pane.Markdown(
        "Fixed profile estimator: 30 equal bins on [0, 1], minimum six pixels per bin, "
        "unweighted median.",
        css_classes=["mr-settings"],
    ),
    title="Geometry and measurement controls",
    collapsed=False,
    sizing_mode="stretch_width",
)

app = pn.Column(
    header,
    controls,
    view,
    max_width=1080,
    sizing_mode="stretch_width",
    margin=(18, 18),
    css_classes=["mr-shell"],
)

app.servable(title="MultiRadial interactive explorer")
