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


CATALOG_ID = "playground-quarter-bend-tube-001"
CATEGORY = "playground"
CREATED = "26-06-06 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

CENTERLINE_RADIUS_MM = 120.0
OUTER_DIAMETER_MM = 80.0
WALL_THICKNESS_MM = 5.0
BEND_ANGLE_DEGREES = 90.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a quarter-circle playground tube.")
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


def make_quarter_bend_tube() -> object:
    import cadquery as cq

    outer_radius = OUTER_DIAMETER_MM / 2
    inner_radius = outer_radius - WALL_THICKNESS_MM
    if inner_radius <= 0:
        raise ValueError("Tube wall thickness leaves no inner bore.")

    path = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .radiusArc((CENTERLINE_RADIUS_MM, CENTERLINE_RADIUS_MM), CENTERLINE_RADIUS_MM)
        .val()
    )
    outer_wire = cq.Wire.makeCircle(
        outer_radius,
        cq.Vector(0, 0, 0),
        cq.Vector(0, 1, 0),
    )
    inner_wire = cq.Wire.makeCircle(
        inner_radius,
        cq.Vector(0, 0, 0),
        cq.Vector(0, 1, 0),
    )
    solid = cq.Solid.sweep(
        outer_wire,
        [inner_wire],
        path,
        makeSolid=True,
        isFrenet=False,
        transitionMode="round",
    )
    return cq.Workplane("XY").add(solid)


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
    arc_length = CENTERLINE_RADIUS_MM * 3.141592653589793 / 2
    data: dict[str, object] = {
        "full_id": CATALOG_ID,
        "nice_name": "Quarter-Bend Tube",
        "description": (
            "Open hollow tube swept through a 90 degree quarter-circle bend, "
            "for connecting perpendicular surfaces."
        ),
        "created": CREATED,
        "last_change": last_change,
        "source": "Synthetic playground, MC/ZK",
        "material": ["cast iron"],
        "category": CATEGORY,
        "parameters_mm": {
            "centerline_radius": CENTERLINE_RADIUS_MM,
            "centerline_arc_length": round(arc_length, 3),
            "bend_angle_degrees": BEND_ANGLE_DEGREES,
            "outer_diameter": OUTER_DIAMETER_MM,
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
        make_quarter_bend_tube(),
        paths["step"],
        dataset_id=CATALOG_ID,
        display_name="Quarter-Bend Tube",
        description="Open hollow tube swept along a 90 degree quarter-circle axis.",
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
