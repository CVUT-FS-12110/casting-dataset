#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
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


CATALOG_ID = "playground-squashed-tapered-quarter-bend-tube-001"
CATEGORY = "playground"
CREATED = "26-06-06 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

CENTERLINE_RADIUS_MM = 120.0
LARGE_OUTER_DIAMETER_MM = 80.0
NARROWING_RATIO = 0.20
WALL_THICKNESS_MM = 5.0
BEND_ANGLE_DEGREES = 90.0
END_SQUASH_RATIO = 0.70
SECTION_COUNT = 9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a tapered, squashed quarter-circle playground tube."
    )
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


def smoothstep(value: float) -> float:
    return value * value * (3 - 2 * value)


def make_squashed_tapered_quarter_bend_tube() -> object:
    import cadquery as cq

    large_outer_radius = LARGE_OUTER_DIAMETER_MM / 2
    small_outer_radius = large_outer_radius * (1 - NARROWING_RATIO)
    large_inner_radius = large_outer_radius - WALL_THICKNESS_MM
    small_inner_radius = small_outer_radius - WALL_THICKNESS_MM

    if small_inner_radius <= 0:
        raise ValueError("Tube wall thickness leaves no inner bore at the narrow end.")

    path = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .radiusArc((CENTERLINE_RADIUS_MM, CENTERLINE_RADIUS_MM), CENTERLINE_RADIUS_MM)
        .val()
    )
    vertical_axis = cq.Vector(0, 0, 1)
    outer_profiles = []
    inner_profiles = []

    for index in range(SECTION_COUNT):
        t = index / (SECTION_COUNT - 1)
        blend = smoothstep(t)
        center = path.positionAt(t)
        tangent = path.tangentAt(t)
        outer_radius = large_outer_radius + (small_outer_radius - large_outer_radius) * t
        inner_radius = large_inner_radius + (small_inner_radius - large_inner_radius) * t
        squash = 1 + (END_SQUASH_RATIO - 1) * blend

        outer_profiles.append(
            cq.Wire.makeEllipse(
                outer_radius * squash,
                outer_radius / squash,
                center,
                tangent,
                vertical_axis,
            )
        )
        inner_profiles.append(
            cq.Wire.makeEllipse(
                inner_radius * squash,
                inner_radius / squash,
                center,
                tangent,
                vertical_axis,
            )
        )

    outer = cq.Solid.sweep_multi(
        outer_profiles,
        path,
        makeSolid=True,
        isFrenet=False,
    )
    bore = cq.Solid.sweep_multi(
        inner_profiles,
        path,
        makeSolid=True,
        isFrenet=False,
    )
    return cq.Workplane("XY").add(outer.cut(bore))


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
    arc_length = CENTERLINE_RADIUS_MM * math.pi / 2
    small_outer_diameter = LARGE_OUTER_DIAMETER_MM * (1 - NARROWING_RATIO)
    small_inner_radius = small_outer_diameter / 2 - WALL_THICKNESS_MM
    end_inner_minor = small_inner_radius * END_SQUASH_RATIO
    end_inner_major = small_inner_radius / END_SQUASH_RATIO
    end_inner_area = math.pi * end_inner_minor * end_inner_major
    original_inner_area = math.pi * small_inner_radius * small_inner_radius

    data: dict[str, object] = {
        "full_id": CATALOG_ID,
        "nice_name": "Squashed Tapered Quarter-Bend Tube",
        "description": (
            "Open hollow 90 degree bend that narrows from a circular large end "
            "to an area-preserving elliptical narrow end."
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
            "large_outer_diameter": LARGE_OUTER_DIAMETER_MM,
            "small_outer_diameter_before_squash": small_outer_diameter,
            "wall_thickness_before_squash": WALL_THICKNESS_MM,
            "end_squash_ratio": END_SQUASH_RATIO,
            "end_inner_minor_diameter": round(end_inner_minor * 2, 3),
            "end_inner_major_diameter": round(end_inner_major * 2, 3),
            "end_inner_area": round(end_inner_area, 3),
            "original_small_inner_circle_area": round(original_inner_area, 3),
            "profile_sections": SECTION_COUNT,
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
        make_squashed_tapered_quarter_bend_tube(),
        paths["step"],
        dataset_id=CATALOG_ID,
        display_name="Squashed Tapered Quarter-Bend Tube",
        description=(
            "Open hollow tube with smooth bend, taper, and area-preserving "
            "circle-to-ellipse outlet transition."
        ),
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
