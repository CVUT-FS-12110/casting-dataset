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


CATALOG_ID = "playground-squashed-bend-to-large-tube-001"
CATEGORY = "playground"
CREATED = "26-06-06 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

CENTERLINE_RADIUS_MM = 120.0
INLET_OUTER_DIAMETER_MM = 80.0
NARROWING_RATIO = 0.20
INLET_WALL_THICKNESS_MM = 5.0
END_SQUASH_RATIO = 0.70
BEND_ANGLE_DEGREES = 90.0

LARGE_TUBE_OUTER_DIAMETER_MM = 110.0
LARGE_TUBE_WALL_THICKNESS_MM = 6.0
ELLIPSE_TO_ROUND_TRANSITION_MM = 100.0
LARGE_TUBE_STRAIGHT_LENGTH_MM = 120.0

BEND_SECTION_COUNT = 9
TRANSITION_SECTION_COUNT = 6
STRAIGHT_SECTION_COUNT = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a squashed tapered bend flowing into a larger tube."
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


def make_squashed_bend_to_large_tube() -> object:
    import cadquery as cq

    inlet_outer_radius = INLET_OUTER_DIAMETER_MM / 2
    narrow_outer_radius = inlet_outer_radius * (1 - NARROWING_RATIO)
    inlet_inner_radius = inlet_outer_radius - INLET_WALL_THICKNESS_MM
    narrow_inner_radius = narrow_outer_radius - INLET_WALL_THICKNESS_MM
    large_outer_radius = LARGE_TUBE_OUTER_DIAMETER_MM / 2
    large_inner_radius = large_outer_radius - LARGE_TUBE_WALL_THICKNESS_MM

    if narrow_inner_radius <= 0 or large_inner_radius <= 0:
        raise ValueError("Wall thickness leaves no inner bore.")

    bend_path = (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .radiusArc((CENTERLINE_RADIUS_MM, CENTERLINE_RADIUS_MM), CENTERLINE_RADIUS_MM)
        .val()
    )
    vertical_axis = cq.Vector(0, 0, 1)
    bend_outer_profiles = []
    bend_inner_profiles = []

    for index in range(BEND_SECTION_COUNT):
        amount = index / (BEND_SECTION_COUNT - 1)
        blend = smoothstep(amount)
        center = bend_path.positionAt(amount)
        tangent = bend_path.tangentAt(amount)
        outer_radius = lerp(inlet_outer_radius, narrow_outer_radius, amount)
        inner_radius = lerp(inlet_inner_radius, narrow_inner_radius, amount)
        squash = lerp(1.0, END_SQUASH_RATIO, blend)

        bend_outer_profiles.append(
            cq.Wire.makeEllipse(
                outer_radius * squash,
                outer_radius / squash,
                center,
                tangent,
                vertical_axis,
            )
        )
        bend_inner_profiles.append(
            cq.Wire.makeEllipse(
                inner_radius * squash,
                inner_radius / squash,
                center,
                tangent,
                vertical_axis,
            )
        )

    bend_outer = cq.Solid.sweep_multi(
        bend_outer_profiles,
        bend_path,
        makeSolid=True,
        isFrenet=False,
    )
    bend_bore = cq.Solid.sweep_multi(
        bend_inner_profiles,
        bend_path,
        makeSolid=True,
        isFrenet=False,
    )
    straight_outer_profiles, straight_inner_profiles = straight_transition_profiles(
        cq,
        vertical_axis,
        narrow_outer_radius,
        narrow_inner_radius,
        large_outer_radius,
        large_inner_radius,
    )
    straight_outer = cq.Solid.makeLoft(straight_outer_profiles, ruled=False)
    straight_bore = cq.Solid.makeLoft(straight_inner_profiles, ruled=False)

    outer = bend_outer.fuse(straight_outer)
    bore = bend_bore.fuse(straight_bore)
    return cq.Workplane("XY").add(outer.cut(bore))


def straight_transition_profiles(
    cq,
    vertical_axis,
    narrow_outer_radius: float,
    narrow_inner_radius: float,
    large_outer_radius: float,
    large_inner_radius: float,
) -> tuple[list[object], list[object]]:
    outlet_x = CENTERLINE_RADIUS_MM
    outlet_y = CENTERLINE_RADIUS_MM
    tangent = cq.Vector(1, 0, 0)
    outer_profiles = []
    inner_profiles = []
    stations = [
        (0.0, 0.0),
        (ELLIPSE_TO_ROUND_TRANSITION_MM * 0.25, 0.25),
        (ELLIPSE_TO_ROUND_TRANSITION_MM * 0.5, 0.5),
        (ELLIPSE_TO_ROUND_TRANSITION_MM * 0.75, 0.75),
        (ELLIPSE_TO_ROUND_TRANSITION_MM, 1.0),
        (ELLIPSE_TO_ROUND_TRANSITION_MM + LARGE_TUBE_STRAIGHT_LENGTH_MM, 1.0),
    ]

    for offset, amount in stations:
        blend = smoothstep(amount)
        center = cq.Vector(outlet_x + offset, outlet_y, 0)
        outer_z_radius = lerp(narrow_outer_radius * END_SQUASH_RATIO, large_outer_radius, blend)
        outer_lateral_radius = lerp(narrow_outer_radius / END_SQUASH_RATIO, large_outer_radius, blend)
        inner_z_radius = lerp(narrow_inner_radius * END_SQUASH_RATIO, large_inner_radius, blend)
        inner_lateral_radius = lerp(narrow_inner_radius / END_SQUASH_RATIO, large_inner_radius, blend)

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

    return outer_profiles, inner_profiles


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
    bend_length = CENTERLINE_RADIUS_MM * math.pi / 2
    narrow_outer_diameter = INLET_OUTER_DIAMETER_MM * (1 - NARROWING_RATIO)
    narrow_inner_radius = narrow_outer_diameter / 2 - INLET_WALL_THICKNESS_MM
    squashed_inner_minor = narrow_inner_radius * END_SQUASH_RATIO
    squashed_inner_major = narrow_inner_radius / END_SQUASH_RATIO
    squashed_inner_area = math.pi * squashed_inner_minor * squashed_inner_major
    large_inner_radius = LARGE_TUBE_OUTER_DIAMETER_MM / 2 - LARGE_TUBE_WALL_THICKNESS_MM
    large_inner_area = math.pi * large_inner_radius * large_inner_radius

    data: dict[str, object] = {
        "full_id": CATALOG_ID,
        "nice_name": "Squashed Bend Into Large Tube",
        "description": (
            "Continuous hollow 90 degree inlet bend that narrows, squashes to an "
            "area-preserving ellipse, then smoothly expands into a larger round tube."
        ),
        "created": CREATED,
        "last_change": last_change,
        "source": "Synthetic playground, MC/ZK",
        "material": ["cast iron"],
        "category": CATEGORY,
        "parameters_mm": {
            "centerline_radius": CENTERLINE_RADIUS_MM,
            "bend_centerline_length": round(bend_length, 3),
            "bend_angle_degrees": BEND_ANGLE_DEGREES,
            "inlet_outer_diameter": INLET_OUTER_DIAMETER_MM,
            "narrow_outer_diameter_before_squash": narrow_outer_diameter,
            "inlet_wall_thickness": INLET_WALL_THICKNESS_MM,
            "end_squash_ratio": END_SQUASH_RATIO,
            "squashed_inner_minor_diameter": round(squashed_inner_minor * 2, 3),
            "squashed_inner_major_diameter": round(squashed_inner_major * 2, 3),
            "squashed_inner_area": round(squashed_inner_area, 3),
            "large_tube_outer_diameter": LARGE_TUBE_OUTER_DIAMETER_MM,
            "large_tube_wall_thickness": LARGE_TUBE_WALL_THICKNESS_MM,
            "large_tube_inner_area": round(large_inner_area, 3),
            "ellipse_to_round_transition_length": ELLIPSE_TO_ROUND_TRANSITION_MM,
            "large_tube_straight_length": LARGE_TUBE_STRAIGHT_LENGTH_MM,
            "total_centerline_length": round(
                bend_length + ELLIPSE_TO_ROUND_TRANSITION_MM + LARGE_TUBE_STRAIGHT_LENGTH_MM,
                3,
            ),
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
        make_squashed_bend_to_large_tube(),
        paths["step"],
        dataset_id=CATALOG_ID,
        display_name="Squashed Bend Into Large Tube",
        description=(
            "Continuous hollow inlet with smooth bend, taper, squashed outlet, "
            "and larger round receiving tube."
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
