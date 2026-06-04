from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_SRC = Path(__file__).resolve().parents[2]
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from casting_dataset.brake_discs import (
    brake_disc_index_item,
    brake_disc_metadata,
    brake_disc_presets,
    make_brake_disc,
)
from casting_dataset.step import export_step


def generate_one(preset_name: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Generate {preset_name} STEP model.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated/step/brake_discs"),
        help="Directory where the STEP file will be written.",
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("generated/metadata/brake_discs"),
        help="Directory where the JSON metadata file will be written.",
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
    args = parser.parse_args(argv)

    def measured_dimensions(dataset_id: str) -> dict[str, float] | None:
        mesh_path = args.mesh_dir / f"{dataset_id}.glb"
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

    spec = brake_disc_presets()[preset_name]
    path = export_step(
        make_brake_disc(spec),
        args.output_dir / f"{spec.dataset_id}.step",
        dataset_id=spec.dataset_id,
        display_name=spec.display_name,
        description=spec.description,
    )
    args.metadata_dir.mkdir(parents=True, exist_ok=True)
    (args.metadata_dir / f"{spec.dataset_id}.json").write_text(
        json.dumps(brake_disc_metadata(spec, measured_dimensions(spec.dataset_id)), indent=2) + "\n",
        encoding="utf-8",
    )
    args.index_path.parent.mkdir(parents=True, exist_ok=True)
    args.index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "asset_layout": "flat",
                "models": [
                    brake_disc_index_item(item, measured_dimensions(item.dataset_id))
                    for item in brake_disc_presets().values()
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(path)
    return 0
