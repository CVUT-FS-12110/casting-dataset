#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = REPO_ROOT / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from casting_dataset.assets import export_glb, export_section_pngs, measured_dimensions
from casting_dataset.step import export_step
from categories.reindex import rebuild_index


CATALOG_ID = "playground-tapered-tube-001"
CATEGORY = "playground"
CREATED = "26-06-06 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

LENGTH_MM = 300.0
LARGE_OUTER_DIAMETER_MM = 80.0
NARROWING_RATIO = 0.20
WALL_THICKNESS_MM = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a tapered playground tube.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "temp",
        help="Root directory for playground outputs.",
    )
    parser.add_argument(
        "--only-step",
        action="store_true",
        help="Generate only STEP plus metadata/index; skip GLB mesh and section images.",
    )
    return parser.parse_args()


def make_tapered_tube() -> object:
    import cadquery as cq

    large_outer_radius = LARGE_OUTER_DIAMETER_MM / 2
    small_outer_radius = large_outer_radius * (1 - NARROWING_RATIO)
    large_inner_radius = large_outer_radius - WALL_THICKNESS_MM
    small_inner_radius = small_outer_radius - WALL_THICKNESS_MM

    if small_inner_radius <= 0:
        raise ValueError("Tube wall thickness leaves no inner bore at the narrow end.")

    taper_per_mm = (large_inner_radius - small_inner_radius) / LENGTH_MM
    cut_extension = 1.0
    inner_start_radius = large_inner_radius + taper_per_mm * cut_extension
    inner_end_radius = small_inner_radius - taper_per_mm * cut_extension

    outer = cq.Solid.makeCone(
        large_outer_radius,
        small_outer_radius,
        LENGTH_MM,
        pnt=(0, 0, 0),
        dir=(0, 0, 1),
    )
    inner = cq.Solid.makeCone(
        inner_start_radius,
        inner_end_radius,
        LENGTH_MM + cut_extension * 2,
        pnt=(0, 0, -cut_extension),
        dir=(0, 0, 1),
    )
    return cq.Workplane("XY").add(outer.cut(inner))


def output_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "step": output_dir / "step" / CATEGORY / f"{CATALOG_ID}.step",
        "mesh": output_dir / "mesh" / CATEGORY / f"{CATALOG_ID}.glb",
        "metadata": output_dir / "metadata" / CATEGORY / f"{CATALOG_ID}.json",
        "sections": output_dir / "sections" / CATEGORY,
    }


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def metadata(dimensions_mm: dict[str, float] | None, last_change: str) -> dict[str, object]:
    data: dict[str, object] = {
        "full_id": CATALOG_ID,
        "nice_name": "Tapered Tube",
        "description": (
            "Open hollow tube with an 80 mm large-end outside diameter, "
            "20% outside-diameter taper, 300 mm length, and 5 mm wall."
        ),
        "created": CREATED,
        "last_change": last_change,
        "source": "Synthetic playground, MC/ZK",
        "material": ["cast iron"],
        "category": CATEGORY,
        "parameters_mm": {
            "length": LENGTH_MM,
            "large_outer_diameter": LARGE_OUTER_DIAMETER_MM,
            "small_outer_diameter": LARGE_OUTER_DIAMETER_MM * (1 - NARROWING_RATIO),
            "wall_thickness": WALL_THICKNESS_MM,
        },
    }
    if dimensions_mm:
        data["dimensions_mm"] = dimensions_mm
        data["dimensions_label"] = (
            f"{dimensions_mm['x']:.1f} x {dimensions_mm['y']:.1f} x "
            f"{dimensions_mm['z']:.1f} mm"
        )
    return data


def main() -> int:
    args = parse_args()
    paths = output_paths(args.output_dir)
    last_change = datetime.now().strftime(DATETIME_FORMAT)

    step_path = export_step(
        make_tapered_tube(),
        paths["step"],
        dataset_id=CATALOG_ID,
        display_name="Tapered Tube",
        description="Open hollow tube tapering from 80 mm OD to 64 mm OD over 300 mm.",
    )
    print(step_path)

    if not args.only_step:
        glb_path = export_glb(step_path, paths["mesh"])
        print(glb_path)
        for section_path in export_section_pngs(glb_path, paths["sections"], CATALOG_ID):
            print(section_path)

    dimensions_mm = measured_dimensions(paths["mesh"])
    write_json(paths["metadata"], metadata(dimensions_mm, last_change))
    print(paths["metadata"])
    print(rebuild_index(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
