"""Browser-ready Panel explorer for RadialPaths synthetic geometries.

Run locally with ``panel serve app/explorer.py --show``. The public static
site uses the separate browser-native implementation in ``web/assets``.
"""

from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
import panel as pn
import param
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

from radialpaths import build_geometry, radial_profile
from radialpaths.plotting import CENTRE_COLOURS, plot_geometry, plot_profile
from radialpaths.synthetic import make_scene


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
        "Capybara": "capybara",
        "T-Rex": "trex",
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
centre_configuration = pn.widgets.Select(
    name="Supplied centres",
    value="2",
    options={
        "One centre": "1",
        "Two centres": "2",
        "Three centres": "3",
        "Four centres": "4",
    },
    width=240,
)


class WavefrontPlayer(pn.reactive.ReactiveHTML):
    """Browser-native controller for the support-constrained arrival frames."""

    frame = param.Integer(default=12, bounds=(0, 12))

    _template = """
    <div id="control" class="mr-wavefront-control">
      <label id="label">Normalized arrival frame</label>
      <div id="row" class="mr-wavefront-row">
        <input id="slider" type="range" min="0" max="12" step="1"
               value="12"></input>
        <button id="play" type="button">
          Animate wavefront
        </button>
      </div>
    </div>
    """

    _scripts = {
        "render": """
          slider.value = data.frame;
          label.textContent = 'Normalized arrival frame: ' + data.frame;
          slider.oninput = function() {
            state.run = (state.run || 0) + 1;
            data.frame = Number(slider.value);
          };
          function begin_animation() {
            state.run = (state.run || 0) + 1;
            var run = state.run;
            data.frame = 0;
            play.textContent = 'Animating…';

            function advance() {
              if (state.run !== run) return;
              if (data.frame === 12) {
                play.textContent = 'Animate wavefront';
                return;
              }
              data.frame = data.frame + 1;
              globalThis.setTimeout(advance, 900);
            }
            globalThis.setTimeout(advance, 900);
          }
          play.onpointerdown = function(event) {
            event.preventDefault();
            begin_animation();
          };
          play.onkeydown = function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              begin_animation();
            }
          };
        """,
        "frame": """
          slider.value = data.frame;
          label.textContent = 'Normalized arrival frame: ' + data.frame;
        """,
    }

    _stylesheets = [
        """
        .mr-wavefront-control { color: #1f2933; font-family: inherit; }
        .mr-wavefront-control label {
          display: block;
          font-size: 0.9rem;
          margin-bottom: 0.35rem;
        }
        .mr-wavefront-row {
          align-items: center;
          display: flex;
          gap: 0.8rem;
        }
        .mr-wavefront-row input { flex: 1 1 190px; min-width: 120px; }
        .mr-wavefront-row button {
          background: #1976b9;
          border: 1px solid #176aa5;
          border-radius: 4px;
          color: white;
          cursor: pointer;
          font-size: 0.9rem;
          font-weight: 600;
          min-height: 34px;
          padding: 0.42rem 0.85rem;
          white-space: nowrap;
        }
        .mr-wavefront-row button:hover { background: #176aa5; }
        """
    ]


wavefront = WavefrontPlayer(
    sizing_mode="stretch_width",
    max_width=440,
    height=74,
)


CENTRE_CANDIDATES = {
    "compact": np.array([[48, 38], [47, 64], [65, 51], [32, 51]], dtype=int),
    "folded": np.array([[24, 25], [74, 31], [49, 78], [24, 65]], dtype=int),
    "perforated": np.array([[50, 25], [50, 77], [22, 50], [78, 50]], dtype=int),
    "branched": np.array([[80, 50], [21, 23], [20, 79], [50, 50]], dtype=int),
    "capybara": np.array([[54, 39], [47, 70], [53, 86], [72, 31]], dtype=int),
    "trex": np.array([[50, 50], [32, 79], [40, 23], [70, 57]], dtype=int),
}


def _configured_centres(scene, configuration):
    count = int(configuration)
    return CENTRE_CANDIDATES[scene.name][:count]


@lru_cache(maxsize=None)
def _scene_and_geometry(shape_name, configuration="2"):
    """Build each immutable support geometry once and reuse it across tracers."""
    scene = make_scene(shape_name)
    geometry = build_geometry(scene.support, _configured_centres(scene, configuration))
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


def _explorer_figure(scene, geometry, field_name, selected_coordinate, arrival_fraction):
    field = getattr(scene, field_name)
    other_coordinate = "rho_X" if selected_coordinate == "rho_D" else "rho_D"
    full_profile = radial_profile(field, geometry, coordinate=selected_coordinate)
    maximum_arrival = float(np.nanmax(geometry.centre_distance))
    normalized_arrival = geometry.centre_distance / max(maximum_arrival, np.finfo(float).eps)
    reached = geometry.support & (normalized_arrival <= arrival_fraction)
    profile = (
        full_profile
        if arrival_fraction >= 1
        else radial_profile(
            field,
            geometry,
            coordinate=selected_coordinate,
            mask=~reached,
        )
    )

    figure, axes = plt.subplots(2, 2, figsize=(9.2, 7.0), constrained_layout=True)

    tracer_ax = axes[0, 0]
    tracer_ax.imshow(np.ma.masked_where(~geometry.support, field), origin="upper", cmap="gray")
    tracer_ax.contour(
        geometry.support.astype(float), levels=[0.5], colors="white", linewidths=0.85
    )
    if arrival_fraction < 1:
        unreached = geometry.support & ~reached
        tracer_ax.imshow(
            np.ma.masked_where(~unreached, np.ones(geometry.shape)),
            origin="upper",
            cmap=ListedColormap(["#eef1f3"]),
            alpha=0.82,
            vmin=0,
            vmax=1,
        )
        if arrival_fraction > 0:
            tracer_ax.contour(
                np.where(geometry.support, normalized_arrival, np.nan),
                levels=[arrival_fraction],
                colors="#2a9d8f",
                linewidths=1.8,
            )
    _mark_centres(tracer_ax, geometry)
    tracer_ax.set_title(f"Registered scalar field · arrival {arrival_fraction:.0%}")
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
    if arrival_fraction < 1:
        for centre in range(full_profile.n_centres):
            selected = full_profile.populated[centre]
            profile_ax.plot(
                full_profile.radius[selected],
                full_profile.median[centre, selected],
                color="#b4bbc2",
                linewidth=1.1,
                alpha=0.75,
                zorder=0,
            )
    plot_profile(profile, ax=profile_ax)
    profile_ax.set_title("Accumulated centre-conditioned profile")
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


@pn.depends(shape, centre_configuration, coordinate, tracer, wavefront.param.frame)
def view(shape, centre_configuration, coordinate, tracer, wavefront):
    scene, geometry = _scene_and_geometry(shape, centre_configuration)
    arrival_fraction = wavefront / 12.0
    figure = _explorer_figure(
        scene,
        geometry,
        tracer,
        coordinate,
        arrival_fraction,
    )
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
        pn.pane.Markdown(
            f"**Propagation state:** {arrival_fraction:.0%} of the global maximum "
            "assigned-centre distance has arrived. Grey curves show the final "
            "profile while coloured curves show bins populated by reached pixels."
        ),
        pane,
        sizing_mode="stretch_width",
    )


header = pn.pane.HTML(
    """
    <div class="mr-header">
      <h1>RadialPaths interactive explorer</h1>
      <p>Inspect how local boundary depth and normalized progression respond to the same accepted support.</p>
    </div>
    """
)

controls = pn.Card(
    pn.FlexBox(
        shape,
        centre_configuration,
        coordinate,
        tracer,
        wavefront,
        flex_wrap="wrap",
        gap="0.8rem",
    ),
    pn.pane.Markdown(
        "Changing the supplied-centre configuration rebuilds the geometry while "
        "leaving the registered tracer fixed. Switching tracers reuses the current "
        "geometry. The animation advances a support-constrained arrival front and "
        "shows the profile populated by reached pixels.",
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

app.servable(title="RadialPaths interactive explorer")
