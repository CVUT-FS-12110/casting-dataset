from __future__ import annotations

from pathlib import Path


def export_step(
    model: object,
    output_path: str | Path,
    *,
    dataset_id: str | None = None,
    display_name: str | None = None,
    description: str | None = None,
) -> Path:
    """Export a CadQuery model to STEP, creating parent directories as needed."""
    try:
        import cadquery as cq
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local CAD install
        raise RuntimeError(
            "CadQuery is required to export STEP models. Install dependencies with "
            "`python -m pip install -r requirements.txt` using Python 3.10-3.12."
        ) from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(path), exportType="STEP")
    if dataset_id or display_name or description:
        _update_step_header(path, dataset_id, display_name, description)
    return path


def _step_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _update_step_header(
    path: Path,
    dataset_id: str | None,
    display_name: str | None,
    description: str | None,
) -> None:
    text = path.read_text(encoding="utf-8")
    header_end = text.find("ENDSEC;")
    data_start = text.find("DATA;")
    if header_end == -1 or data_start == -1 or header_end > data_start:
        return

    lines = text[:data_start].splitlines()
    updated: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("FILE_DESCRIPTION("):
            values = [value for value in (dataset_id, display_name, description) if value]
            updated.append(f"FILE_DESCRIPTION(({','.join(_step_string(value) for value in values)}),'2;1');")
        elif stripped.startswith("FILE_NAME(") and (dataset_id or display_name):
            file_name = dataset_id or display_name or "Open CASCADE Shape Model"
            updated.append(line.replace("'Open CASCADE Shape Model'", _step_string(file_name), 1))
        else:
            updated.append(line)

    path.write_text("\n".join(updated) + "\n" + text[data_start:], encoding="utf-8")
