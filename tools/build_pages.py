"""Build the static RadialPaths website without a Python browser runtime."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = (
    "01_quickstart.ipynb",
    "02_understanding_coordinates.ipynb",
    "03_your_own_image.ipynb",
    "04_registered_tracers.ipynb",
)


def _repository_identity() -> tuple[str, str]:
    slug = os.environ.get("GITHUB_REPOSITORY", "RafaelSdeSouza/multiradial")
    repository_url = f"https://github.com/{slug}"
    pages_url = os.environ.get(
        "RADIALPATHS_PAGES_URL",
        os.environ.get(
            "MULTIRADIAL_PAGES_URL",
            "https://rafaelsdesouza.com.br/multiradial/",
        ),
    )
    return repository_url, pages_url


def _replace_placeholders(root: Path, repository_url: str, pages_url: str) -> None:
    for path in root.rglob("*.html"):
        content = path.read_text(encoding="utf-8")
        content = content.replace("__REPOSITORY_URL__", repository_url)
        content = content.replace("__PAGES_URL__", pages_url)
        path.write_text(content, encoding="utf-8")


def _render_notebooks(output: Path) -> None:
    try:
        from nbconvert import HTMLExporter
    except ImportError as error:
        raise ImportError("site rendering requires the radialpaths[site] extra") from error

    examples_output = output / "examples"
    assets_output = examples_output / "assets"
    assets_output.mkdir(parents=True, exist_ok=True)
    exporter = HTMLExporter(template_name="lab")
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True

    for notebook_name in NOTEBOOKS:
        source = ROOT / "examples" / notebook_name
        shutil.copy2(source, examples_output / notebook_name)
        body, _ = exporter.from_filename(str(source))
        (examples_output / f"{source.stem}.html").write_text(body, encoding="utf-8")

        notebook = json.loads(source.read_text(encoding="utf-8"))
        preview = None
        for cell in notebook["cells"]:
            for result in cell.get("outputs", []):
                encoded = result.get("data", {}).get("image/png")
                if encoded:
                    preview = encoded if isinstance(encoded, str) else "".join(encoded)
                    break
            if preview:
                break
        if preview is None:
            raise ValueError(f"executed notebook has no PNG preview: {source}")
        (assets_output / f"{source.stem}.png").write_bytes(base64.b64decode(preview))


def build(output: Path) -> None:
    output = output.resolve()
    if output in {ROOT, ROOT.parent, Path(output.anchor)}:
        raise ValueError(f"refusing to replace broad output directory: {output}")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    repository_url, pages_url = _repository_identity()
    shutil.copytree(ROOT / "web", output, dirs_exist_ok=True)
    shutil.copytree(
        ROOT / "docs" / "_static" / "tutorials" / "your_own_image",
        output / "tutorial" / "assets",
        dirs_exist_ok=True,
    )
    for notebook in NOTEBOOKS:
        shutil.copy2(ROOT / "examples" / notebook, output / "tutorial" / notebook)
    _render_notebooks(output)

    rendered_docs = ROOT / "docs" / "_build" / "html"
    if not (rendered_docs / "index.html").exists():
        raise FileNotFoundError(
            "Sphinx documentation is not built; run sphinx-build before build_pages.py"
        )
    shutil.copytree(
        rendered_docs,
        output / "docs",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".doctrees"),
    )
    shutil.copy2(ROOT / "CITATION.cff", output / "CITATION.cff")
    (output / ".nojekyll").touch()
    _replace_placeholders(output, repository_url, pages_url)

    required = [
        output / "index.html",
        output / "explorer" / "index.html",
        output / "tutorial" / "index.html",
        output / "tutorial" / "assets" / "07_final_geometry.png",
        output / "tutorial" / "03_your_own_image.ipynb",
        output / "examples" / "01_quickstart.html",
        output / "examples" / "assets" / "01_quickstart.png",
        output / "citation" / "index.html",
        output / "docs" / "index.html",
        output / "assets" / "geometry.js",
        output / "assets" / "explorer.js",
        output / "CITATION.cff",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"incomplete Pages artifact: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    arguments = parser.parse_args()
    build(arguments.output)


if __name__ == "__main__":
    main()
