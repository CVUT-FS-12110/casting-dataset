#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_SRC = Path(__file__).resolve().parents[2]
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from casting_dataset.brake_discs import (
    METADATA_DATETIME_FORMAT,
    brake_disc_index_item,
    brake_disc_metadata,
    brake_disc_presets,
    make_brake_disc,
)
from casting_dataset.step import export_step


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate representative brake disc STEP models."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/step/brake_discs"),
        help="Directory where STEP files will be written.",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("generated/metadata/brake_discs"),
        help="Directory where JSON metadata files will be written.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=Path("generated/index.json"),
        help="Path where the compact dataset index will be written.",
    )
    parser.add_argument(
        "--mesh-dir",
        type=Path,
        default=Path("generated/mesh/brake_discs"),
        help="Directory containing GLB files used for measured dimensions.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=sorted(brake_disc_presets()),
        help="Optional subset of preset names to generate.",
    )
    return parser.parse_args()


def measured_dimensions(mesh_dir: Path, dataset_id: str) -> dict[str, float] | None:
    mesh_path = mesh_dir / f"{dataset_id}.glb"
    if not mesh_path.exists():
        return None
    try:
        import trimesh
    except ImportError:
        return None

    mesh = trimesh.load(mesh_path, force="mesh")
    if mesh.is_empty:
        return None
    x, y, z = (round(float(value), 1) for value in mesh.extents)
    return {"x": x, "y": y, "z": z}


def main() -> int:
    args = parse_args()
    presets = brake_disc_presets()
    names = args.only or list(presets)
    last_change = datetime.now().strftime(METADATA_DATETIME_FORMAT)

    index_items = []
    for name in names:
        spec = presets[name]
        dimensions_mm = measured_dimensions(args.mesh_dir, spec.dataset_id)
        index_items.append(brake_disc_index_item(spec, dimensions_mm, last_change))
        model = make_brake_disc(spec)
        path = export_step(
            model,
            args.output_dir / f"{spec.dataset_id}.step",
            dataset_id=spec.dataset_id,
            display_name=spec.display_name,
            description=spec.description,
        )
        args.metadata_dir.mkdir(parents=True, exist_ok=True)
        (args.metadata_dir / f"{spec.dataset_id}.json").write_text(
            json.dumps(brake_disc_metadata(spec, dimensions_mm, last_change), indent=2) + "\n",
            encoding="utf-8",
        )
        print(path)

    args.index_path.parent.mkdir(parents=True, exist_ok=True)
    args.index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "asset_layout": "flat",
                "models": index_items,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
