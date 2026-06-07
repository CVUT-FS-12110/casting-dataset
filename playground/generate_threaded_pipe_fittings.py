#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_SRC = REPO_ROOT / "src"
if str(REPO_SRC) not in sys.path:
    sys.path.insert(0, str(REPO_SRC))

from casting_dataset.assets import export_section_pngs, measured_dimensions
from casting_dataset.step import export_step
from categories.reindex import rebuild_index


CATEGORY = "threaded_pipe_fittings"
SOURCE = "Synthetic playground from docs/categories/Threaded Pipe Fittings.md, MC/ZK"
CREATED = "26-06-07 00-00-00"
DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"

R1_MAJOR_DIAMETER_MM = 33.249
R34_MAJOR_DIAMETER_MM = 26.441
R1_TPI = 11.0
R1_PITCH_MM = 25.4 / R1_TPI
BSPT_DIAMETER_TAPER = 1.0 / 16.0
THREAD_RIDGE_RADIUS_MM = 0.42
THREAD_GROOVE_WIDTH_MM = 0.9
FEMALE_SOCKET_LIP_RADIUS_MM = 1.4
FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM = 1.4
THIN_BODY_DIAMETER_MM = 36.0
ELBOW_BODY_DIAMETER_MM = 38.0
R1_FEMALE_SOCKET_DIAMETER_MM = 42.0
R34_FEMALE_SOCKET_DIAMETER_MM = 36.0
FEMALE_SOCKET_DEPTH_MM = 22.0
FEMALE_SOCKET_BLEND_MM = 9.0


@dataclass(frozen=True)
class Fitting:
    catalog_id: str
    nice_name: str
    description: str
    make: Callable[[], object]
    parameters_mm: dict[str, object]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the Threaded Pipe Fittings R 1 inch playground dataset."
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
    parser.add_argument(
        "--only",
        choices=[f"{CATEGORY}-{index:03d}" for index in range(1, 16)],
        help="Generate just one fitting id for debugging.",
    )
    return parser.parse_args()


def axis_vector(cq, axis: str):
    return {
        "x": cq.Vector(1, 0, 0),
        "y": cq.Vector(0, 1, 0),
        "z": cq.Vector(0, 0, 1),
    }[axis]


def solid_to_axis(solid, axis: str):
    if axis == "x":
        return solid.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "y":
        return solid.rotate((0, 0, 0), (1, 0, 0), -90)
    return solid


def hex_prism(cq, af: float, length: float, axis: str = "z", center=(0, 0, 0)):
    circum_diameter = af / math.cos(math.pi / 6)
    solid = (
        cq.Workplane("XY")
        .polygon(6, circum_diameter)
        .extrude(length)
        .translate((0, 0, -length / 2))
        .val()
    )
    return solid_to_axis(solid, axis).translate(center)


def cyl(cq, radius: float, length: float, axis: str = "z", center=(0, 0, 0)):
    direction = axis_vector(cq, axis)
    start = cq.Vector(*center) - direction.multiply(length / 2)
    return cq.Solid.makeCylinder(radius, length, start, direction)


def cone(cq, radius1: float, radius2: float, length: float, axis: str = "z", center=(0, 0, 0)):
    direction = axis_vector(cq, axis)
    start = cq.Vector(*center) - direction.multiply(length / 2)
    return cq.Solid.makeCone(radius1, radius2, length, start, direction)


def union_all(solids: list[object]):
    result = solids[0]
    for solid in solids[1:]:
        result = result.fuse(solid)
    return result


def cut_all(solid, cutters: list[object]):
    result = solid
    for cutter in cutters:
        result = result.cut(cutter)
    return result


def compound_workplane(cq, solids: list[object]):
    return cq.Workplane("XY").add(cq.Compound.makeCompound(solids))


def vector_tuple(vector) -> tuple[float, float, float]:
    return (float(vector.x), float(vector.y), float(vector.z))


def male_thread_body(cq, length: float, axis: str, center=(0, 0, 0), large_end_positive=True):
    drop = length * BSPT_DIAMETER_TAPER / 2
    large_radius = R1_MAJOR_DIAMETER_MM / 2
    small_radius = large_radius - drop
    if large_end_positive:
        return cone(cq, small_radius, large_radius, length, axis, center)
    return cone(cq, large_radius, small_radius, length, axis, center)


def cone_dir(
    cq,
    radius1: float,
    radius2: float,
    length: float,
    center: tuple[float, float, float],
    direction,
):
    direction = direction.normalized()
    start = cq.Vector(*center) - direction.multiply(length / 2)
    if abs(radius1 - radius2) < 1e-6:
        return cq.Solid.makeCylinder(radius1, length, start, direction)
    return cq.Solid.makeCone(radius1, radius2, length, start, direction)


def cyl_dir(cq, radius: float, length: float, start, direction):
    return cq.Solid.makeCylinder(radius, length, start, direction.normalized())


def male_thread_body_dir(cq, length: float, center, direction, large_end_positive=True):
    drop = length * BSPT_DIAMETER_TAPER / 2
    large_radius = R1_MAJOR_DIAMETER_MM / 2
    small_radius = large_radius - drop
    if large_end_positive:
        return cone_dir(cq, small_radius, large_radius, length, center, direction)
    return cone_dir(cq, large_radius, small_radius, length, center, direction)


def male_thread_ridges(
    cq,
    length: float,
    axis: str,
    center=(0, 0, 0),
    large_end_positive=True,
    count: int | None = None,
) -> list[object]:
    direction = axis_vector(cq, axis)
    return swept_thread_ridges_dir(
        cq, length, center, direction, R1_MAJOR_DIAMETER_MM / 2 - length * BSPT_DIAMETER_TAPER / 4
    )


def male_thread_ridges_dir(
    cq,
    length: float,
    center,
    direction,
    large_end_positive=True,
    count: int | None = None,
) -> list[object]:
    direction = direction.normalized()
    return swept_thread_ridges_dir(
        cq, length, center, direction, R1_MAJOR_DIAMETER_MM / 2 - length * BSPT_DIAMETER_TAPER / 4
    )


def swept_thread_ridges_dir(
    cq,
    length: float,
    center,
    direction,
    helix_radius: float,
    ridge_radius: float = THREAD_RIDGE_RADIUS_MM,
) -> list[object]:
    direction = direction.normalized()
    usable = max(length - 2.8, R1_PITCH_MM)
    start = cq.Vector(*center) - direction.multiply(usable / 2)
    helix = cq.Wire.makeHelix(R1_PITCH_MM, usable, helix_radius, start, direction)
    profile = cq.Wire.makeCircle(ridge_radius, helix.positionAt(0), helix.tangentAt(0))
    return [cq.Solid.sweep(profile, [], helix, makeSolid=True, isFrenet=True)]


def female_thread_groove_cuts(
    cq,
    port_center: tuple[float, float, float],
    inward: tuple[float, float, float],
    depth: float,
    base_bore_diameter: float,
    major_diameter: float = R1_MAJOR_DIAMETER_MM,
) -> list[object]:
    direction = cq.Vector(*inward).normalized()
    base_radius = base_bore_diameter / 2
    root_radius = major_diameter / 2 + 0.25
    groove_radius = min(max((root_radius - base_radius) * 0.42, 0.42), 0.72)
    helix_radius = base_radius + groove_radius * 0.55
    usable_depth = max(depth - 3.0, R1_PITCH_MM)
    start = cq.Vector(*port_center) + direction.multiply(1.5)
    helix = cq.Wire.makeHelix(R1_PITCH_MM, usable_depth, helix_radius, start, direction)
    profile = cq.Wire.makeCircle(groove_radius, helix.positionAt(0), helix.tangentAt(0))
    lead_center = cq.Vector(*port_center) + direction.multiply(0.45)
    return [
        cq.Solid.sweep(profile, [], helix, makeSolid=True, isFrenet=True),
        cq.Solid.makeCone(
            root_radius + 1.0,
            base_radius,
            1.8,
            lead_center - direction.multiply(0.9),
            direction,
        )
    ]


def female_thread_ridges(
    cq,
    port_center: tuple[float, float, float],
    inward: tuple[float, float, float],
    depth: float,
    base_bore_diameter: float,
    major_diameter: float = R1_MAJOR_DIAMETER_MM,
) -> list[object]:
    return []


def female_socket_outer(
    cq,
    port_center: tuple[float, float, float],
    inward: tuple[float, float, float],
    socket_diameter: float,
    body_diameter: float,
    depth: float = FEMALE_SOCKET_DEPTH_MM,
    blend_length: float = FEMALE_SOCKET_BLEND_MM,
    round_outer_edges: bool = True,
    protruding_outer_round: bool = True,
) -> list[object]:
    direction = cq.Vector(*inward).normalized()
    port = cq.Vector(*port_center)
    lip_radius = FEMALE_SOCKET_LIP_RADIUS_MM
    outer_edge_radius = FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM
    socket_radius = socket_diameter / 2
    body_radius = body_diameter / 2
    lip_center = port + direction.multiply(lip_radius)
    blend_start = port + direction.multiply(depth)
    solids = [
        cyl_dir(cq, socket_radius, depth, port, direction),
        cone_dir(
            cq,
            socket_radius,
            body_radius,
            blend_length,
            vector_tuple(blend_start + direction.multiply(blend_length / 2)),
            direction,
        ),
    ]
    if round_outer_edges:
        solids.append(cq.Solid.makeTorus(socket_radius - lip_radius, lip_radius, lip_center, direction))
        if protruding_outer_round:
            solids.append(
                cq.Solid.makeTorus(
                    socket_radius,
                    outer_edge_radius,
                    port + direction.multiply(outer_edge_radius * 0.5),
                    direction,
                )
            )
    return solids


def female_mouth_round(
    cq,
    port_center: tuple[float, float, float],
    inward: tuple[float, float, float],
    outer_diameter: float,
    radius: float = 2.0,
) -> list[object]:
    direction = cq.Vector(*inward).normalized()
    port = cq.Vector(*port_center)
    outer_radius = outer_diameter / 2
    return [
        cq.Solid.makeTorus(
            outer_radius - radius,
            radius,
            port + direction.multiply(radius),
            direction,
        ),
        cq.Solid.makeTorus(
            outer_radius,
            radius,
            port + direction.multiply(radius * 0.5),
            direction,
        ),
    ]


def through_bore(cq, radius: float, length: float, axis: str, center=(0, 0, 0)):
    return cyl(cq, radius, length + 8, axis, center)


def arc_segment(cq, radius: float, angle_degrees: float, body_diameter: float, bore_diameter: float):
    angle = math.radians(angle_degrees)
    mid = (radius * math.sin(angle / 2), radius * (1 - math.cos(angle / 2)))
    end = (radius * math.sin(angle), radius * (1 - math.cos(angle)))
    path = cq.Workplane("XY").moveTo(0, 0).threePointArc(mid, end).val()
    start_tangent = path.tangentAt(0).normalized()
    outer_wire = cq.Wire.makeCircle(body_diameter / 2, path.positionAt(0), start_tangent)
    bore_wire = cq.Wire.makeCircle(bore_diameter / 2, path.positionAt(0), start_tangent)
    outer = cq.Solid.sweep(outer_wire, [], path, makeSolid=True, isFrenet=False)
    bore = cq.Solid.sweep(bore_wire, [], path, makeSolid=True, isFrenet=False)
    return outer, bore, path.positionAt(1), path.tangentAt(1).normalized()


def elbow_female_female(
    cq,
    angle_degrees: float,
    radius: float,
    straight: float,
    body_diameter: float,
    socket_diameter: float,
    use_socket_body: bool,
):
    bore_diameter = 27.0
    outer_arc, bore_arc, end, end_tangent = arc_segment(
        cq, radius, angle_degrees, body_diameter, bore_diameter
    )
    start_port = cq.Vector(-straight, 0, 0)
    start_dir = cq.Vector(1, 0, 0)
    end_port = end + end_tangent.multiply(straight)
    solids = [
        outer_arc,
        cyl(cq, body_diameter / 2, straight, "x", (-straight / 2, 0, 0)),
        cq.Solid.makeCylinder(body_diameter / 2, straight, end, end_tangent),
    ]
    if use_socket_body:
        solids += female_socket_outer(
            cq, vector_tuple(start_port), vector_tuple(start_dir), socket_diameter, body_diameter
        )
        solids += female_socket_outer(
            cq,
            vector_tuple(end_port),
            vector_tuple(end_tangent.multiply(-1)),
            socket_diameter,
            body_diameter,
        )
    else:
        solids += female_mouth_round(cq, vector_tuple(start_port), vector_tuple(start_dir), body_diameter)
        solids += female_mouth_round(
            cq, vector_tuple(end_port), vector_tuple(end_tangent.multiply(-1)), body_diameter
        )
    cuts = [
        bore_arc,
        cyl(cq, bore_diameter / 2, straight + 6, "x", (-straight / 2 - 3, 0, 0)),
        cq.Solid.makeCylinder(bore_diameter / 2, straight + 6, end - end_tangent.multiply(3), end_tangent),
    ]
    cuts += female_thread_groove_cuts(cq, vector_tuple(start_port), vector_tuple(start_dir), 22, bore_diameter)
    cuts += female_thread_groove_cuts(
        cq, vector_tuple(end_port), vector_tuple(end_tangent.multiply(-1)), 22, bore_diameter
    )
    ridges = female_thread_ridges(
        cq, vector_tuple(start_port), vector_tuple(start_dir), 22, bore_diameter
    )
    ridges += female_thread_ridges(
        cq, vector_tuple(end_port), vector_tuple(end_tangent.multiply(-1)), 22, bore_diameter
    )
    return cq.Compound.makeCompound([cut_all(union_all(solids), cuts)] + ridges)


def elbow_female_male(
    cq,
    angle_degrees: float,
    radius: float,
    female_straight: float,
    male_length: float,
    body_diameter: float,
    socket_diameter: float,
    use_socket_body: bool,
):
    bore_diameter = 27.0
    outer_arc, bore_arc, end, end_tangent = arc_segment(
        cq, radius, angle_degrees, body_diameter, bore_diameter
    )
    start_port = cq.Vector(-female_straight, 0, 0)
    start_dir = cq.Vector(1, 0, 0)
    male_center = end + end_tangent.multiply(male_length / 2)
    thread_ridges = male_thread_ridges_dir(
        cq, male_length, vector_tuple(male_center), end_tangent, large_end_positive=False
    )
    solids = [
        outer_arc,
        cyl(cq, body_diameter / 2, female_straight, "x", (-female_straight / 2, 0, 0)),
        male_thread_body_dir(cq, male_length, vector_tuple(male_center), end_tangent, large_end_positive=False),
    ]
    if use_socket_body:
        solids += female_socket_outer(
            cq, vector_tuple(start_port), vector_tuple(start_dir), socket_diameter, body_diameter
        )
    else:
        solids += female_mouth_round(cq, vector_tuple(start_port), vector_tuple(start_dir), body_diameter)
    cuts = [
        bore_arc,
        cyl(cq, bore_diameter / 2, female_straight + 6, "x", (-female_straight / 2 - 3, 0, 0)),
        cq.Solid.makeCylinder(bore_diameter / 2, male_length + 6, end - end_tangent.multiply(3), end_tangent),
    ]
    cuts += female_thread_groove_cuts(cq, vector_tuple(start_port), vector_tuple(start_dir), 22, bore_diameter)
    female_ridges = female_thread_ridges(
        cq, vector_tuple(start_port), vector_tuple(start_dir), 22, bore_diameter
    )
    return cq.Compound.makeCompound([cut_all(union_all(solids), cuts)] + thread_ridges + female_ridges)


def make_coupling():
    import cadquery as cq

    body = union_all(
        [
            hex_prism(cq, 46, 50, "z"),
        ]
    )
    body = union_all(
        [body]
        + female_socket_outer(cq, (0, 0, -25), (0, 0, 1), 46, 46, 20, 2, False)
        + female_socket_outer(cq, (0, 0, 25), (0, 0, -1), 46, 46, 20, 2, False)
    )
    cuts = [through_bore(cq, 31 / 2, 58, "z")]
    cuts += female_thread_groove_cuts(cq, (0, 0, -25), (0, 0, 1), 22, 31)
    cuts += female_thread_groove_cuts(cq, (0, 0, 25), (0, 0, -1), 22, 31)
    ridges = female_thread_ridges(cq, (0, 0, -25), (0, 0, 1), 22, 31)
    ridges += female_thread_ridges(cq, (0, 0, 25), (0, 0, -1), 22, 31)
    return compound_workplane(cq, [cut_all(body, cuts)] + ridges)


def make_round_coupling():
    import cadquery as cq

    body = cyl(cq, R1_FEMALE_SOCKET_DIAMETER_MM / 2, 50, "z")
    body = union_all(
        [body]
        + female_socket_outer(
            cq,
            (0, 0, -25),
            (0, 0, 1),
            R1_FEMALE_SOCKET_DIAMETER_MM,
            R1_FEMALE_SOCKET_DIAMETER_MM,
            20,
            2,
        )
        + female_socket_outer(
            cq,
            (0, 0, 25),
            (0, 0, -1),
            R1_FEMALE_SOCKET_DIAMETER_MM,
            R1_FEMALE_SOCKET_DIAMETER_MM,
            20,
            2,
        )
    )
    cuts = [through_bore(cq, 31 / 2, 58, "z")]
    cuts += female_thread_groove_cuts(cq, (0, 0, -25), (0, 0, 1), 22, 31)
    cuts += female_thread_groove_cuts(cq, (0, 0, 25), (0, 0, -1), 22, 31)
    ridges = female_thread_ridges(cq, (0, 0, -25), (0, 0, 1), 22, 31)
    ridges += female_thread_ridges(cq, (0, 0, 25), (0, 0, -1), 22, 31)
    return compound_workplane(cq, [cut_all(body, cuts)] + ridges)


def make_reducer():
    import cadquery as cq

    body = union_all(
        [
            male_thread_body(cq, 20, "z", (0, 0, -10), large_end_positive=True),
            cyl(cq, R34_FEMALE_SOCKET_DIAMETER_MM / 2, 20, "z", (0, 0, 10)),
            hex_prism(cq, 46, 14, "z", (0, 0, 7)),
        ]
    )
    body = union_all(
        [body]
        + female_socket_outer(
            cq,
            (0, 0, 20),
            (0, 0, -1),
            R34_FEMALE_SOCKET_DIAMETER_MM,
            R34_FEMALE_SOCKET_DIAMETER_MM,
            18,
            2,
        )
    )
    cuts = [through_bore(cq, 24 / 2, 48, "z")]
    cuts += female_thread_groove_cuts(cq, (0, 0, 20), (0, 0, -1), 18, 24, R34_MAJOR_DIAMETER_MM)
    threaded = cut_all(body, cuts)
    ridges = male_thread_ridges(cq, 20, "z", (0, 0, -10), large_end_positive=True)
    ridges += female_thread_ridges(cq, (0, 0, 20), (0, 0, -1), 18, 24, R34_MAJOR_DIAMETER_MM)
    return compound_workplane(cq, [threaded] + ridges)


def make_nipple():
    import cadquery as cq

    body = union_all(
        [
            male_thread_body(cq, 20, "z", (0, 0, -22.5), large_end_positive=True),
            cyl(cq, 39.5 / 2, 25, "z", (0, 0, 0)),
            male_thread_body(cq, 20, "z", (0, 0, 22.5), large_end_positive=False),
            hex_prism(cq, 46, 25, "z", (0, 0, 0)),
        ]
    ).cut(through_bore(cq, 27 / 2, 72, "z"))
    ridges = (
        male_thread_ridges(cq, 20, "z", (0, 0, -22.5), large_end_positive=True)
        + male_thread_ridges(cq, 20, "z", (0, 0, 22.5), large_end_positive=False)
    )
    return compound_workplane(cq, [body] + ridges)


def make_plug():
    import cadquery as cq

    head = hex_prism(cq, 46, 11, "z", (0, 0, 7))
    dome = cq.Solid.makeSphere(18, cq.Vector(0, 0, 12)).cut(cyl(cq, 40, 36, "z", (0, 0, 29)))
    solids = [male_thread_body(cq, 18, "z", (0, 0, -7.5), large_end_positive=True), head, dome]
    ridges = male_thread_ridges(cq, 18, "z", (0, 0, -7.5), large_end_positive=True)
    return compound_workplane(cq, [union_all(solids)] + ridges)


def make_square_head_pipe_plug():
    import cadquery as cq

    round_body = cyl(cq, 18, 11, "z", (0, 0, 6.5))
    square_head = (
        cq.Workplane("XY")
        .rect(24, 24)
        .extrude(8)
        .translate((0, 0, 12))
        .val()
    )
    solids = [
        male_thread_body(cq, 18, "z", (0, 0, -7.5), large_end_positive=True),
        round_body,
        square_head,
    ]
    ridges = male_thread_ridges(cq, 18, "z", (0, 0, -7.5), large_end_positive=True)
    return compound_workplane(cq, [union_all(solids)] + ridges)


def make_arc_fitting(angle: float, radius: float, outer_diameter: float, bore_diameter: float):
    import cadquery as cq

    body = elbow_female_female(
        cq, angle, radius, 28, THIN_BODY_DIAMETER_MM, R1_FEMALE_SOCKET_DIAMETER_MM, True
    )
    return cq.Workplane("XY").add(body)


def make_45_elbow_female_male():
    import cadquery as cq

    body = elbow_female_male(
        cq, 45, 70, 34, 22, THIN_BODY_DIAMETER_MM, R1_FEMALE_SOCKET_DIAMETER_MM, True
    )
    return cq.Workplane("XY").add(body)


def make_90_elbow_female_male():
    import cadquery as cq

    body = elbow_female_male(
        cq, 90, 58, 34, 22, THIN_BODY_DIAMETER_MM, R1_FEMALE_SOCKET_DIAMETER_MM, True
    )
    return cq.Workplane("XY").add(body)


def make_sharp_elbow_female_female(angle_degrees: float):
    import cadquery as cq

    radius = 28 if angle_degrees == 90 else 42
    straight = 24 if angle_degrees == 90 else 26
    body = elbow_female_female(
        cq, angle_degrees, radius, straight, ELBOW_BODY_DIAMETER_MM, ELBOW_BODY_DIAMETER_MM, False
    )
    return cq.Workplane("XY").add(body)


def make_tee(reduced_branch: bool = False):
    import cadquery as cq

    branch_outer = 33 if reduced_branch else THIN_BODY_DIAMETER_MM
    branch_bore = 24 if reduced_branch else 27
    outer = union_all(
        [
            cyl(cq, THIN_BODY_DIAMETER_MM / 2, 100, "x"),
            cyl(cq, branch_outer / 2, 50, "y", (0, 25, 0)),
        ]
    )
    branch_socket = R34_FEMALE_SOCKET_DIAMETER_MM if reduced_branch else R1_FEMALE_SOCKET_DIAMETER_MM
    outer = union_all(
        [outer]
        + female_socket_outer(
            cq, (-50, 0, 0), (1, 0, 0), R1_FEMALE_SOCKET_DIAMETER_MM, THIN_BODY_DIAMETER_MM
        )
        + female_socket_outer(
            cq, (50, 0, 0), (-1, 0, 0), R1_FEMALE_SOCKET_DIAMETER_MM, THIN_BODY_DIAMETER_MM
        )
        + female_socket_outer(
            cq, (0, 50, 0), (0, -1, 0), branch_socket, branch_outer
        )
    )
    port_specs = [
        ((-50, 0, 0), (1, 0, 0), 27, R1_MAJOR_DIAMETER_MM),
        ((50, 0, 0), (-1, 0, 0), 27, R1_MAJOR_DIAMETER_MM),
        (
            (0, 50, 0),
            (0, -1, 0),
            branch_bore,
            R34_MAJOR_DIAMETER_MM if reduced_branch else R1_MAJOR_DIAMETER_MM,
        ),
    ]
    bores = [
        cyl(cq, 27 / 2, 112, "x"),
        cyl(cq, branch_bore / 2, 60, "y", (0, 25, 0)),
    ]
    cuts = bores
    ridges = []
    for port, inward, bore, major in port_specs:
        cuts += female_thread_groove_cuts(cq, port, inward, 22, bore, major)
        ridges += female_thread_ridges(cq, port, inward, 22, bore, major)
    return compound_workplane(cq, [cut_all(outer, cuts)] + ridges)


def make_cross():
    import cadquery as cq

    lips = []
    for port, inward in [
        ((-50, 0, 0), (1, 0, 0)),
        ((50, 0, 0), (-1, 0, 0)),
        ((0, -50, 0), (0, 1, 0)),
        ((0, 50, 0), (0, -1, 0)),
    ]:
        lips += female_socket_outer(
            cq, port, inward, R1_FEMALE_SOCKET_DIAMETER_MM, THIN_BODY_DIAMETER_MM
        )
    outer = union_all(
        [
            cyl(cq, THIN_BODY_DIAMETER_MM / 2, 100, "x"),
            cyl(cq, THIN_BODY_DIAMETER_MM / 2, 100, "y"),
        ]
        + lips
    )
    cuts = [cyl(cq, 27 / 2, 112, "x"), cyl(cq, 27 / 2, 112, "y")]
    ridges = []
    for port, inward in [
        ((-50, 0, 0), (1, 0, 0)),
        ((50, 0, 0), (-1, 0, 0)),
        ((0, -50, 0), (0, 1, 0)),
        ((0, 50, 0), (0, -1, 0)),
    ]:
        cuts += female_thread_groove_cuts(cq, port, inward, 22, 27)
        ridges += female_thread_ridges(cq, port, inward, 22, 27)
    return compound_workplane(cq, [cut_all(outer, cuts)] + ridges)


def make_union():
    import cadquery as cq

    center_tube = cyl(cq, 20, 30, "x").cut(cyl(cq, 27 / 2, 38, "x"))
    left = union_all(
        [
            male_thread_body(cq, 20, "x", (-32.5, 0, 0), large_end_positive=True),
            cyl(cq, 20, 28, "x", (-12, 0, 0)),
        ]
    ).cut(cyl(cq, 27 / 2, 54, "x", (-19, 0, 0)))
    right = union_all(
        [
            male_thread_body(cq, 20, "x", (32.5, 0, 0), large_end_positive=False),
            cyl(cq, 20, 28, "x", (12, 0, 0)),
        ]
    ).cut(cyl(cq, 27 / 2, 54, "x", (19, 0, 0)))
    core = union_all([left, center_tube, right])
    ridges = (
        male_thread_ridges(cq, 20, "x", (-32.5, 0, 0), large_end_positive=True)
        + male_thread_ridges(cq, 20, "x", (32.5, 0, 0), large_end_positive=False)
    )
    nut = hex_prism(cq, 60, 22, "x").cut(cyl(cq, 36 / 2, 28, "x"))
    return compound_workplane(cq, [core, nut] + ridges)


def fittings() -> list[Fitting]:
    return [
        Fitting(f"{CATEGORY}-001", "Nipple", "R1 male-to-male adapter for joining two female threaded pipe ends.", make_nipple, {"overall_length": 65, "outer_diameter": 39.5, "bore_diameter": 27, "hex_af": 46, "hex_length": 25}),
        Fitting(f"{CATEGORY}-002", "Hex Coupling", "R1 hexagonal female-to-female fitting for joining two threaded pipe ends with wrench flats.", make_coupling, {"overall_length": 50, "body_af": 46, "bore_diameter": 31, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-003", "Coupling", "R1 round female-to-female pipe coupling for joining two threaded pipe ends.", make_round_coupling, {"overall_length": 50, "outer_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 31, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-004", "Reducer", "R1 reducer fitting for connecting a male threaded pipe end to a smaller female threaded line.", make_reducer, {"overall_length": 40, "body_diameter": 46, "male_thread_length": 20, "female_thread_depth": 18, "female_bore_diameter": 24, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-005", "Plug", "R1 threaded closure plug for sealing an unused female port.", make_plug, {"overall_length": 25, "head_af": 46, "thread_length": 18}),
        Fitting(f"{CATEGORY}-006", "Square Head Pipe Plug", "R1 round pipe plug with a square drive head for closing a threaded female port.", make_square_head_pipe_plug, {"overall_length": 30, "round_body_diameter": 36, "square_head_size": 24, "thread_length": 18}),
        Fitting(f"{CATEGORY}-007", "Bend 90 FF", "R1 female-to-female long bend for turning a fluid line through 90 degrees.", lambda: make_arc_fitting(90, 58, 46, 27), {"centerline_radius": 58, "straight_socket_length": 28, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "bend_angle_degrees": 90, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-008", "Bend 90 FM", "R1 street bend for connecting a female socket to a male threaded outlet at 90 degrees.", make_90_elbow_female_male, {"centerline_radius": 58, "female_socket_length": 34, "male_thread_length": 22, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "bend_angle_degrees": 90, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-009", "Bend 45 FF", "R1 female-to-female long bend for a gentler 45 degree change of direction in a fluid line.", lambda: make_arc_fitting(45, 70, 46, 27), {"centerline_radius": 70, "straight_socket_length": 28, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "bend_angle_degrees": 45, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-010", "Bend 45 FM", "R1 street bend for connecting a female socket to a male threaded outlet at 45 degrees.", make_45_elbow_female_male, {"centerline_radius": 70, "female_socket_length": 34, "male_thread_length": 22, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "bend_angle_degrees": 45, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-011", "Elbow 90 FF", "R1 compact female-to-female elbow for a sharp but castable 90 degree turn.", lambda: make_sharp_elbow_female_female(90), {"centerline_radius": 28, "straight_socket_length": 24, "body_diameter": ELBOW_BODY_DIAMETER_MM, "female_socket_diameter": ELBOW_BODY_DIAMETER_MM, "bore_diameter": 27, "female_thread_depth": 22, "bend_angle_degrees": 90, "end_outer_radius": 2.0}),
        Fitting(f"{CATEGORY}-012", "Elbow 45 FF", "R1 compact female-to-female elbow for a sharp but castable 45 degree turn.", lambda: make_sharp_elbow_female_female(45), {"centerline_radius": 42, "straight_socket_length": 26, "body_diameter": ELBOW_BODY_DIAMETER_MM, "female_socket_diameter": ELBOW_BODY_DIAMETER_MM, "bore_diameter": 27, "female_thread_depth": 22, "bend_angle_degrees": 45, "end_outer_radius": 2.0}),
        Fitting(f"{CATEGORY}-013", "Tee", "R1 three-port fitting for branching a fluid line at right angles.", lambda: make_tee(False), {"main_center_to_end": 50, "branch_center_to_end": 50, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-014", "Reducing Tee", "R1 three-port branch fitting for splitting a fluid line to a smaller branch.", lambda: make_tee(True), {"main_center_to_end": 50, "branch_center_to_end": 50, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "r1_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "r34_socket_diameter": R34_FEMALE_SOCKET_DIAMETER_MM, "main_bore_diameter": 27, "branch_bore_diameter": 24, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
        Fitting(f"{CATEGORY}-015", "Cross", "R1 four-port fitting for distributing a fluid line in two perpendicular directions.", make_cross, {"center_to_end": 50, "thin_body_diameter": THIN_BODY_DIAMETER_MM, "female_socket_diameter": R1_FEMALE_SOCKET_DIAMETER_MM, "bore_diameter": 27, "socket_lip_radius": FEMALE_SOCKET_LIP_RADIUS_MM, "socket_outer_edge_radius": FEMALE_SOCKET_OUTER_EDGE_RADIUS_MM}),
    ]


def output_paths(output_dir: Path, catalog_id: str) -> dict[str, Path]:
    return {
        "step": output_dir / "step" / CATEGORY / f"{catalog_id}.step",
        "mesh": output_dir / "mesh" / CATEGORY / f"{catalog_id}.glb",
        "metadata": output_dir / "metadata" / CATEGORY / f"{catalog_id}.json",
        "sections": output_dir / "sections" / CATEGORY,
    }


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def export_model_glb(model: object, glb_path: Path, tolerance: float = 1.6) -> Path:
    import trimesh

    shape = model.val()
    vertices, faces = shape.tessellate(tolerance)
    mesh = trimesh.Trimesh(
        vertices=[vector_tuple(vertex) for vertex in vertices],
        faces=[tuple(face) for face in faces],
        process=False,
    )
    if mesh.is_empty:
        raise RuntimeError(f"Could not tessellate model for GLB: {glb_path}")
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(glb_path)
    return glb_path


def metadata(fitting: Fitting, dimensions_mm: dict[str, float] | None, last_change: str):
    data: dict[str, object] = {
        "full_id": fitting.catalog_id,
        "nice_name": fitting.nice_name,
        "description": fitting.description,
        "created": CREATED,
        "last_change": last_change,
        "source": SOURCE,
        "material": ["galvanized steel"],
        "category": CATEGORY,
        "thread": {
            "standard": "ISO 7-1 / EN 10226-1 BSPT",
            "designation": "R1",
            "tpi": R1_TPI,
            "pitch_mm": round(R1_PITCH_MM, 3),
            "major_diameter_mm": R1_MAJOR_DIAMETER_MM,
            "diameter_taper": "1:16",
            "geometry_note": "Male threads are continuous swept helical ridges; female threads are continuous helical groove cuts aligned to the socket bore.",
            "effective_turns_by_depth": {
                "18_mm": round(max(18 - 3.0, R1_PITCH_MM) / R1_PITCH_MM, 2),
                "20_mm": round(max(20 - 3.0, R1_PITCH_MM) / R1_PITCH_MM, 2),
                "22_mm": round(max(22 - 3.0, R1_PITCH_MM) / R1_PITCH_MM, 2),
            },
        },
        "parameters_mm": fitting.parameters_mm,
    }
    if dimensions_mm:
        data["dimensions_mm"] = dimensions_mm
        data["dimensions_label"] = (
            f"{dimensions_mm['x']:.1f} x {dimensions_mm['y']:.1f} x {dimensions_mm['z']:.1f} mm"
        )
    return data


def validate_model(model: object, catalog_id: str) -> None:
    shape = model.val()
    volume = shape.Volume()
    print(f"{catalog_id}: {shape.ShapeType()} valid={shape.isValid()} volume={volume:.3f}")
    if not shape.isValid() or volume <= 0:
        raise RuntimeError(f"Invalid CAD model: {catalog_id}")


def main() -> int:
    args = parse_args()
    last_change = datetime.now().strftime(DATETIME_FORMAT)

    selected = [f for f in fittings() if args.only in (None, f.catalog_id)]
    for fitting in selected:
        paths = output_paths(args.output_dir, fitting.catalog_id)
        model = fitting.make()
        validate_model(model, fitting.catalog_id)
        step_path = export_step(
            model,
            paths["step"],
            dataset_id=fitting.catalog_id,
            display_name=fitting.nice_name,
            description=fitting.description,
        )
        print(step_path)

        if not args.only_step:
            glb_path = export_model_glb(model, paths["mesh"])
            print(glb_path)
            for section_path in export_section_pngs(glb_path, paths["sections"], fitting.catalog_id):
                print(section_path)

        dimensions_mm = measured_dimensions(paths["mesh"])
        write_json(paths["metadata"], metadata(fitting, dimensions_mm, last_change))
        print(paths["metadata"])

    print(rebuild_index(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
