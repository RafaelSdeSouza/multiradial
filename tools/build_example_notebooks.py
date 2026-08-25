#!/usr/bin/env python3
"""Build and execute the focused RadialPaths example notebooks."""

from __future__ import annotations

from pathlib import Path
import textwrap

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def markdown(value: str):
    return nbformat.v4.new_markdown_cell(textwrap.dedent(value).strip())


def code(value: str):
    return nbformat.v4.new_code_cell(textwrap.dedent(value).strip())


SETUP = code(
    """
    from pathlib import Path
    import sys
    source = Path("src") if Path("src/radialpaths").exists() else Path("../src")
    if str(source.resolve()) not in sys.path:
        sys.path.insert(0, str(source.resolve()))

    import matplotlib.pyplot as plt
    import numpy as np
    from radialpaths import build_geometry, radial_profile

    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.linewidth": 0.8})
    """
)


def header(title: str, summary: str, goals: str, keywords: str):
    goal_lines = "\n".join(
        f"- {item.strip().rstrip('.')}" for item in goals.split(";") if item.strip()
    )
    return markdown(
        f"""
        # {title}

        ## Author

        [Rafael S. de Souza](https://rafaelsdesouza.com.br/)

        ## Learning goals

        {goal_lines}

        ## Keywords

        {keywords}

        ## Summary

        {summary}

        ## Resources

        - [Documentation](https://rafaelsdesouza.com.br/multiradial/docs/)
        - [Source](https://github.com/RafaelSdeSouza/multiradial)
        - Paper/preprint: bibliographic link pending
        - [Citation metadata](https://github.com/RafaelSdeSouza/multiradial/blob/main/CITATION.cff)

        Execute this notebook from a local checkout. A Colab installation link
        will be added only after the first immutable release tag exists.
        """
    )


def notebook(cells):
    result = nbformat.v4.new_notebook(cells=cells)
    result.metadata.update(
        {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        }
    )
    return result


def quickstart():
    return notebook(
        [
            header(
                "Quick start: geometry and one radial profile",
                "Construct two coordinates on a connected irregular mask and measure a scalar field.",
                "provide support and centres; inspect centre assignment and both coordinates; compute a centre-conditioned profile.",
                "support mask, supplied centres, radial profile",
            ),
            SETUP,
            markdown(
                """
                ## Define the formal inputs

                `True` pixels are traversable. Supplied centres use NumPy
                `(row, column)` order and must lie inside the connected support.
                """
            ),
            code(
                """
                yy, xx = np.indices((81, 111), dtype=float)
                support = ((xx - 52) / 43) ** 2 + ((yy - 40) / 27) ** 2 <= 1
                support |= ((xx - 82) / 18) ** 2 + ((yy - 49) / 16) ** 2 <= 1
                centres = [(37, 30), (47, 76)]
                geometry = build_geometry(support, centres)

                intensity = np.full(support.shape, np.nan)
                intensity[support] = np.exp(-geometry.centre_distance[support] / 14)
                intensity[support] += 0.08 * xx[support] / support.shape[1]
                profile = radial_profile(intensity, geometry, coordinate="rho_X")
                print(geometry.rho_D.dtype, geometry.rho_X.dtype)
                print(profile.median.shape, "centre profiles by", profile.n_bins, "bins")
                """
            ),
            code(
                """
                fig, axes = plt.subplots(1, 4, figsize=(12.2, 3.0), constrained_layout=True)
                for ax, field, title in zip(
                    axes,
                    [intensity, geometry.labels, geometry.rho_D, geometry.rho_X],
                    ["Registered intensity", "Centre-associated regions", r"Relative depth $\\rho_D$", r"Progression $\\rho_X$"],
                ):
                    ax.imshow(field, cmap="cividis", origin="upper", vmin=0, vmax=1)
                    ax.contour(support, [0.5], colors="#30363b", linewidths=0.8)
                    ax.scatter(np.asarray(centres)[:, 1], np.asarray(centres)[:, 0], c=["#0072B2", "#D55E00"], edgecolors="white", s=35)
                    ax.set(title=title, xticks=[], yticks=[])
                plt.show()
                """
            ),
            code(
                """
                fig, ax = plt.subplots(figsize=(5.2, 3.2))
                for centre_index, values in enumerate(profile.median):
                    ax.plot(profile.radius, values, lw=2, label=f"Centre {centre_index + 1}")
                ax.set(xlabel=r"Normalized progression $\\rho_X$", ylabel="Median intensity")
                ax.spines[["top", "right"]].set_visible(False)
                ax.legend(frameon=False)
                plt.show()
                """
            ),
            markdown(
                """
                The support and centres fix the geometry. Changing the
                registered intensity values does not recompute centre assignment
                or either coordinate.
                """
            ),
        ]
    )


def coordinates():
    return notebook(
        [
            header(
                "Understanding relative depth and progression",
                "Use controlled supports to determine when relative boundary depth and normalized progression coincide and when they separate.",
                "recover the circular reference case; compare compact, elongated, folded, and perforated supports; narrow a tail while keeping its centreline fixed; identify how an internal boundary enters rho_D.",
                "circular reference, elongated tail, folded support, internal boundary, coordinate interpretation",
            ),
            SETUP,
            markdown(
                """
                ## Controlled support families

                The supplied centre and support determine both coordinate
                fields. The examples below change one geometric feature at a
                time rather than changing the measured tracer.
                """
            ),
            code(
                """
                yy, xx = np.indices((101, 131), dtype=float)

                def distance_to_polyline(x, y, points):
                    result = np.full_like(x, np.inf, dtype=float)
                    for (ax, ay), (bx, by) in zip(points[:-1], points[1:]):
                        dx, dy = bx - ax, by - ay
                        t = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
                        result = np.minimum(result, np.hypot(x - (ax + t * dx), y - (ay + t * dy)))
                    return result

                def make_case(name, tail_half_width=9):
                    if name == "circle":
                        mask = np.hypot(xx - 65, yy - 50) <= 36
                        centre = [(50, 65)]
                    elif name == "compact":
                        mask = ((xx - 61) / 43) ** 2 + ((yy - 51) / 31) ** 2 <= 1
                        mask |= ((xx - 91) / 17) ** 2 + ((yy - 39) / 16) ** 2 <= 1
                        centre = [(50, 54)]
                    elif name == "elongated":
                        spine_y = 47 + 0.10 * (xx - 23) + 3 * np.sin((xx - 23) / 24)
                        mask = (xx >= 20) & (xx <= 116) & (np.abs(yy - spine_y) <= tail_half_width)
                        mask |= ((xx - 23) / 16) ** 2 + ((yy - 47) / 15) ** 2 <= 1
                        centre = [(47, 23)]
                    elif name == "folded":
                        path = [(25, 27), (95, 27), (105, 50), (94, 74), (32, 72), (28, 55)]
                        mask = distance_to_polyline(xx, yy, path) <= 8
                        centre = [(27, 25)]
                    elif name == "perforated":
                        mask = ((xx - 65) / 52) ** 2 + ((yy - 50) / 39) ** 2 <= 1
                        mask &= (xx - 72) ** 2 + (yy - 48) ** 2 >= 12**2
                        centre = [(52, 28)]
                    mask[[0, -1], :] = False
                    mask[:, [0, -1]] = False
                    return mask, centre, build_geometry(mask, centre)

                cases = {name: make_case(name) for name in ("circle", "compact", "elongated", "folded", "perforated")}

                fig, axes = plt.subplots(2, 5, figsize=(13.2, 5.0), constrained_layout=True)
                for column, (name, (mask, centre, geometry)) in enumerate(cases.items()):
                    for row, field in enumerate((geometry.rho_D, geometry.rho_X)):
                        axes[row, column].imshow(field, cmap="cividis", origin="upper", vmin=0, vmax=1)
                        axes[row, column].contour(mask, [0.5], colors="#30363b", linewidths=0.8)
                        axes[row, column].scatter([centre[0][1]], [centre[0][0]], c="#0072B2", edgecolors="white", s=32)
                        axes[row, column].set(xticks=[], yticks=[])
                    axes[0, column].set_title(name.capitalize())
                axes[0, 0].set_ylabel(r"Relative depth $\\rho_D$")
                axes[1, 0].set_ylabel(r"Progression $\\rho_X$")
                plt.show()
                """
            ),
            markdown(
                """
                The centred circle supplies the finite-grid reference: both
                fields approximate conventional normalized radius. Compact
                perturbations preserve much of that agreement. Elongation,
                folding, and an internal excluded region separate the two
                denominators.
                """
            ),
            markdown(
                """
                ## Narrow the tail without moving its centreline

                The sampled centreline and supplied centre remain fixed. Only
                the lateral half-width changes.
                """
            ),
            code(
                """
                fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4), constrained_layout=True)
                for half_width, colour in zip((14, 9, 5), ("#9aa3aa", "#2A9D8F", "#7B61A8")):
                    mask, centre, geometry = make_case("elongated", tail_half_width=half_width)
                    columns = np.arange(23, 114)
                    rows = np.rint(47 + 0.10 * (columns - 23) + 3 * np.sin((columns - 23) / 24)).astype(int)
                    progression = (columns - columns.min()) / (columns.max() - columns.min())
                    axes[0].plot(progression, geometry.rho_D[rows, columns], color=colour, lw=2, label=f"half-width {half_width} px")
                    axes[1].plot(progression, geometry.rho_X[rows, columns], color=colour, lw=2)
                axes[0].set(title=r"Relative depth $\\rho_D$", ylabel="Coordinate value")
                axes[1].set(title=r"Normalized progression $\\rho_X$")
                for ax in axes:
                    ax.set(xlabel="Centreline progression", ylim=(-0.02, 1.02))
                    ax.spines[["top", "right"]].set_visible(False)
                axes[0].legend(frameon=False, fontsize=8)
                plt.show()
                """
            ),
            markdown(
                r"""
                Narrowing the support reduces the centreline values of
                $\rho_D=d/(d+b)$ because the nearby lateral boundary reduces
                $b$. The ordering of $\rho_X=d/L$ remains tied to distance from
                the supplied centre relative to the full region extent. In the
                perforated case, excluded hole pixels cannot be traversed and
                adjacent in-support pixels enter the boundary set used for $b$.
                """
            ),
        ]
    )


def registered_tracers():
    return notebook(
        [
            header(
                "Reuse one geometry across registered tracers",
                "Measure brightness, colour, and velocity-like fields on one immutable geometry.",
                "separate geometry from measurement; compare profiles without redefining radial position.",
                "registered tracers, geometry reuse, radial profiles",
            ),
            SETUP,
            code(
                """
                yy, xx = np.indices((91, 121), dtype=float)
                support = ((xx - 55) / 47) ** 2 + ((yy - 45) / 31) ** 2 <= 1
                support |= ((xx >= 48) & (xx <= 106) & (np.abs(yy - (45 + 0.25 * (xx - 48))) <= 7))
                centres = [(43, 28), (54, 81)]
                geometry = build_geometry(support, centres)

                brightness = np.full(support.shape, np.nan)
                colour = np.full(support.shape, np.nan)
                velocity = np.full(support.shape, np.nan)
                brightness[support] = np.exp(-geometry.centre_distance[support] / 13)
                colour[support] = 0.2 + 0.65 * xx[support] / support.shape[1]
                velocity[support] = -90 + 180 * xx[support] / support.shape[1]

                measurements = {
                    "brightness": radial_profile(brightness, geometry, coordinate="rho_X"),
                    "colour": radial_profile(colour, geometry, coordinate="rho_X"),
                    "velocity": radial_profile(velocity, geometry, coordinate="rho_X"),
                }
                """
            ),
            code(
                """
                fig, axes = plt.subplots(1, 3, figsize=(10.7, 3.2), constrained_layout=True)
                for ax, (name, profile) in zip(axes, measurements.items()):
                    for centre_index, values in enumerate(profile.median):
                        ax.plot(profile.radius, values, lw=2, label=f"Centre {centre_index + 1}")
                    ax.set(xlabel=r"Normalized progression $\\rho_X$", title=name.capitalize())
                    ax.spines[["top", "right"]].set_visible(False)
                axes[0].legend(frameon=False, fontsize=8)
                plt.show()
                """
            ),
            markdown(
                """
                All three profile calls use the same support, centre assignment,
                graph distances, and coordinate arrays. Only the registered
                pixel values passed to the estimator differ.
                """
            ),
        ]
    )


def execute_and_write(name: str, value) -> None:
    NotebookClient(value, timeout=180, kernel_name="python3", resources={"metadata": {"path": ROOT}}).execute()
    path = EXAMPLES / name
    nbformat.write(value, path)
    print(path)


def main() -> None:
    execute_and_write("01_quickstart.ipynb", quickstart())
    execute_and_write("02_understanding_coordinates.ipynb", coordinates())
    execute_and_write("04_registered_tracers.ipynb", registered_tracers())


if __name__ == "__main__":
    main()
