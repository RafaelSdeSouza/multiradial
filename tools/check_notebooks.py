"""Validate saved outputs and execute the four release notebooks in isolation."""

from __future__ import annotations

import copy
from pathlib import Path
import tempfile

from nbclient import NotebookClient
from nbformat import read


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = (
    "01_quickstart.ipynb",
    "02_understanding_coordinates.ipynb",
    "03_your_own_image.ipynb",
    "04_registered_tracers.ipynb",
)


def _audit_saved(path: Path):
    notebook = read(path, as_version=4)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if not code_cells:
        raise ValueError(f"notebook contains no code cells: {path}")
    if any(cell.execution_count is None for cell in code_cells):
        raise ValueError(f"notebook contains an unexecuted code cell: {path}")
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.output_type == "error"
    ]
    if errors:
        raise ValueError(f"notebook contains a saved error output: {path}")
    if not any(
        "image/png" in output.get("data", {})
        for cell in code_cells
        for output in cell.get("outputs", [])
    ):
        raise ValueError(f"notebook contains no saved figure output: {path}")
    first_cell = "".join(notebook.cells[0].source)
    if "Rafael S. de Souza" not in first_cell or "https://rafaelsdesouza.com.br/" not in first_cell:
        raise ValueError(f"notebook first cell lacks the release authorship links: {path}")
    source = "\n".join("".join(cell.source) for cell in code_cells)
    if "from radialpaths import" not in source or "multiradial" in source.lower():
        raise ValueError(f"notebook import identity is inconsistent: {path}")
    return notebook, len(code_cells)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="radialpaths-notebooks-") as temporary:
        execution_directory = Path(temporary)
        for name in NOTEBOOKS:
            path = ROOT / "examples" / name
            notebook, code_count = _audit_saved(path)
            executed = copy.deepcopy(notebook)
            NotebookClient(
                executed,
                timeout=600,
                kernel_name="python3",
                resources={"metadata": {"path": str(execution_directory)}},
            ).execute()
            errors = [
                output
                for cell in executed.cells
                if cell.cell_type == "code"
                for output in cell.get("outputs", [])
                if output.output_type == "error"
            ]
            if errors:
                raise ValueError(f"fresh execution produced an error: {path}")
            print(f"{name}: {code_count} code cells executed")


if __name__ == "__main__":
    main()
