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


CATALOG_ID = "playground-side-squashed-inlet-into-main-tube-001"
CATEGORY = "playground"
CREATED = "26-06-06 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

MAIN_TUBE_OUTER_DIAMETER_MM = 110.0
MAIN_TUBE_WALL_THICKNESS_MM = 6.0
MAIN_TUBE_LENGTH_MM = 360.0

INLET_CENTERLINE_RADIUS_MM = 120.0
INLET_OUTER_DIAMETER_MM = 80.0
INLET_NARROWING_RATIO = 0.20
INLET_WALL_THICKNESS_MM = 5.0
INLET_END_SQUASH_RATIO = 0.70
INLET_BEND_ANGLE_DEGREES = 90.0
INLET_SECTION_COUNT = 9
PENETRATION_SECTION_COUNT = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a squashed side inlet through a main exhaust tube wall."
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


def lerp(start: float, end: float, amount: float) -> float:
    return start + (end - start) * amount


def make_side_squashed_inlet_into_main_tube() -> object:
    import cadquery as cq

    main_outer_radius = MAIN_TUBE_OUTER_DIAMETER_MM / 2
    main_inner_radius = main_outer_radius - MAIN_TUBE_WALL_THICKNESS_MM
    inlet_outer_radius = INLET_OUTER_DIAMETER_MM / 2
    inlet_narrow_outer_radius = inlet_outer_radius * (1 - INLET_NARROWING_RATIO)
    inlet_inner_radius = inlet_outer_radius - INLET_WALL_THICKNESS_MM
    inlet_narrow_inner_radius = inlet_narrow_outer_radius - INLET_WALL_THICKNESS_MM

    if main_inner_radius <= 0 or inlet_narrow_inner_radius <= 0:
        raise ValueError("Wall thickness leaves no inner bore.")

    main_outer = cq.Solid.makeCylinder(
        main_outer_radius,
        MAIN_TUBE_LENGTH_MM,
        pnt=(-MAIN_TUBE_LENGTH_MM / 2, 0, 0),
        dir=(1, 0, 0),
    )
    main_bore = cq.Solid.makeCylinder(
        main_inner_radius,
        MAIN_TUBE_LENGTH_MM + 20,
        pnt=(-MAIN_TUBE_LENGTH_MM / 2 - 10, 0, 0),
        dir=(1, 0, 0),
    )

    vertical_axis = cq.Vector(0, 0, 1)
    inlet_outer, inlet_bore = inlet_bend_solids(
        cq,
        vertical_axis,
        inlet_outer_radius,
        inlet_narrow_outer_radius,
        inlet_inner_radius,
        inlet_narrow_inner_radius,
        main_outer_radius,
    )
    penetration_outer, penetration_bore = penetration_solids(
        cq,
        vertical_axis,
        inlet_narrow_outer_radius,
        inlet_narrow_inner_radius,
        main_outer_radius,
    )

    outer = main_outer.fuse(inlet_outer).fuse(penetration_outer)
    bore = main_bore.fuse(inlet_bore).fuse(penetration_bore)
    return cq.Workplane("XY").add(outer.cut(bore))


def inlet_bend_solids(
    cq,
    vertical_axis,
    inlet_outer_radius: float,
    inlet_narrow_outer_radius: float,
    inlet_inner_radius: float,
    inlet_narrow_inner_radius: float,
    main_outer_radius: float,
) -> tuple[object, object]:
    start_x = -INLET_CENTERLINE_RADIUS_MM
    start_y = main_outer_radius + INLET_CENTERLINE_RADIUS_MM
    end_x = 0
    end_y = main_outer_radius
    path = (
        cq.Workplane("XY")
        .moveTo(start_x, start_y)
        .radiusArc((end_x, end_y), INLET_CENTERLINE_RADIUS_MM)
        .val()
    )
    outer_profiles = []
    inner_profiles = []

    for index in range(INLET_SECTION_COUNT):
        amount = index / (INLET_SECTION_COUNT - 1)
        blend = smoothstep(amount)
        center = path.positionAt(amount)
        tangent = path.tangentAt(amount)
        outer_radius = lerp(inlet_outer_radius, inlet_narrow_outer_radius, amount)
        inner_radius = lerp(inlet_inner_radius, inlet_narrow_inner_radius, amount)
        squash = lerp(1.0, INLET_END_SQUASH_RATIO, blend)

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

    return (
        cq.Solid.sweep_multi(outer_profiles, path, makeSolid=True, isFrenet=False),
        cq.Solid.sweep_multi(inner_profiles, path, makeSolid=True, isFrenet=False),
    )


def penetration_solids(
    cq,
    vertical_axis,
    inlet_narrow_outer_radius: float,
    inlet_narrow_inner_radius: float,
    main_outer_radius: float,
) -> tuple[object, object]:
    outer_profiles = []
    inner_profiles = []
    tangent = cq.Vector(0, -1, 0)
    outer_z_radius = inlet_narrow_outer_radius * INLET_END_SQUASH_RATIO
    outer_lateral_radius = inlet_narrow_outer_radius / INLET_END_SQUASH_RATIO
    inner_z_radius = inlet_narrow_inner_radius * INLET_END_SQUASH_RATIO
    inner_lateral_radius = inlet_narrow_inner_radius / INLET_END_SQUASH_RATIO

    for index in range(PENETRATION_SECTION_COUNT):
        amount = index / (PENETRATION_SECTION_COUNT - 1)
        center = cq.Vector(0, lerp(main_outer_radius, 0, amount), 0)
        outer_profiles.append(
            cq.Wire.makeEllipse(
                outer_z_radius,
                outer_lateral_radius,
                center,
                tangent,
                vertical_axis,
            )
        )
        inner_profiles.append(
            cq.Wire.makeEllipse(
                inner_z_radius,
                inner_lateral_radius,
                center,
                tangent,
                vertical_axis,
            )
        )

    return (
        cq.Solid.makeLoft(outer_profiles, ruled=False),
        cq.Solid.makeLoft(inner_profiles, ruled=False),
    )


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
    main_inner_radius = MAIN_TUBE_OUTER_DIAMETER_MM / 2 - MAIN_TUBE_WALL_THICKNESS_MM
    inlet_narrow_outer_diameter = INLET_OUTER_DIAMETER_MM * (1 - INLET_NARROWING_RATIO)
    inlet_narrow_inner_radius = inlet_narrow_outer_diameter / 2 - INLET_WALL_THICKNESS_MM
    inlet_inner_minor = inlet_narrow_inner_radius * INLET_END_SQUASH_RATIO
    inlet_inner_major = inlet_narrow_inner_radius / INLET_END_SQUASH_RATIO
    inlet_inner_area = math.pi * inlet_inner_minor * inlet_inner_major
    original_inlet_area = math.pi * inlet_narrow_inner_radius * inlet_narrow_inner_radius
    main_inner_area = math.pi * main_inner_radius * main_inner_radius

    data: dict[str, object] = {
        "full_id": CATALOG_ID,
        "nice_name": "Side Squashed Inlet Into Main Tube",
        "description": (
            "Main round exhaust tube with one tapered, squashed 90 degree side inlet "
            "cut through the wall into the main bore."
        ),
        "created": CREATED,
        "last_change": last_change,
        "source": "Synthetic playground, MC/ZK",
        "material": ["cast iron"],
        "category": CATEGORY,
        "parameters_mm": {
            "main_tube_outer_diameter": MAIN_TUBE_OUTER_DIAMETER_MM,
            "main_tube_wall_thickness": MAIN_TUBE_WALL_THICKNESS_MM,
            "main_tube_length": MAIN_TUBE_LENGTH_MM,
            "main_tube_inner_area": round(main_inner_area, 3),
            "inlet_centerline_radius": INLET_CENTERLINE_RADIUS_MM,
            "inlet_bend_angle_degrees": INLET_BEND_ANGLE_DEGREES,
            "inlet_outer_diameter": INLET_OUTER_DIAMETER_MM,
            "inlet_narrow_outer_diameter_before_squash": inlet_narrow_outer_diameter,
            "inlet_wall_thickness": INLET_WALL_THICKNESS_MM,
            "inlet_end_squash_ratio": INLET_END_SQUASH_RATIO,
            "inlet_inner_minor_diameter": round(inlet_inner_minor * 2, 3),
            "inlet_inner_major_diameter": round(inlet_inner_major * 2, 3),
            "inlet_inner_area": round(inlet_inner_area, 3),
            "original_narrow_inner_circle_area": round(original_inlet_area, 3),
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
        make_side_squashed_inlet_into_main_tube(),
        paths["step"],
        dataset_id=CATALOG_ID,
        display_name="Side Squashed Inlet Into Main Tube",
        description=(
            "Main round tube with a tapered, squashed side inlet bore opened into "
            "the main flow passage."
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
