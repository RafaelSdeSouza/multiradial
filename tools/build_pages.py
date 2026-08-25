"""Build the complete static GitHub Pages artifact for MultiRadial."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _repository_identity() -> tuple[str, str]:
    slug = os.environ.get("GITHUB_REPOSITORY", "RafaelSdeSouza/multiradial")
    repository_url = f"https://github.com/{slug}"
    owner, name = slug.split("/", 1)
    pages_url = f"https://{owner}.github.io/{name}/"
    return repository_url, pages_url


def _copy_web_sources(output: Path) -> None:
    repository_url, pages_url = _repository_identity()
    source = ROOT / "web"

    shutil.copytree(source / "assets", output / "assets", dirs_exist_ok=True)
    shutil.copytree(source / "tutorial", output / "tutorial", dirs_exist_ok=True)
    shutil.copy2(source / "404.html", output / "404.html")
    shutil.copy2(ROOT / "CITATION.cff", output / "CITATION.cff")

    landing = (source / "index.html").read_text(encoding="utf-8")
    landing = landing.replace("__REPOSITORY_URL__", repository_url)
    landing = landing.replace("__PAGES_URL__", pages_url)
    (output / "index.html").write_text(landing, encoding="utf-8")


def build(output: Path, wheel: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    wheel = wheel.resolve()
    if not wheel.exists():
        raise FileNotFoundError(f"wheel not found: {wheel}")

    _run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "lite",
            "build",
            "--contents",
            "examples",
            "--output-dir",
            str(output / "lite"),
            "--piplite-wheels",
            str(wheel),
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "panel",
            "convert",
            "app/explorer.py",
            "--to",
            "pyodide-worker",
            "--out",
            str(output / "explorer"),
            "--title",
            "MultiRadial interactive explorer",
            "--requirements",
            str(wheel),
        ]
    )

    converted = output / "explorer" / "explorer.html"
    if not converted.exists():
        raise FileNotFoundError(f"Panel conversion did not produce {converted}")
    converted.replace(output / "explorer" / "index.html")
    _copy_web_sources(output)

    required = [
        output / "index.html",
        output / "explorer" / "index.html",
        output / "tutorial" / "index.html",
        output / "lite" / "lab" / "index.html",
        output / "CITATION.cff",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"incomplete Pages artifact: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site")
    parser.add_argument(
        "--wheel",
        type=Path,
        default=ROOT / "dist" / "multiradial-0.1.0.dev0-py3-none-any.whl",
    )
    arguments = parser.parse_args()
    build(arguments.output.resolve(), arguments.wheel)


if __name__ == "__main__":
    main()
