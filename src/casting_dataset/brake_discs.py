from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from math import cos, pi, sin, tau


BRAKE_DISC_CREATED = "26-06-05 00-00-00"
BRAKE_DISC_SOURCE = "Synthetic, MC/ZK"
BRAKE_DISC_MATERIAL = ["Pearlite", "Pearlite-ferrite"]
BRAKE_DISC_CATEGORY = "Brake discs"
METADATA_DATETIME_FORMAT = "%y-%m-%d %H-%M-%S"


@dataclass(frozen=True)
class BrakeDiscSpec:
    dataset_id: str
    name: str
    display_name: str
    description: str
    outer_diameter: float
    friction_inner_diameter: float
    thickness: float
    center_bore_diameter: float
    hub_diameter: float
    hat_height: float
    hat_wall_thickness: float
    bolt_count: int
    bolt_circle_diameter: float
    bolt_hole_diameter: float
    has_hat: bool = True
    has_mounting_flange: bool = True
    mounting_flange_thickness: float | None = None
    mounting_flange_outer_diameter: float | None = None
    mounting_flange_position: str = "disc_side"
    ventilated: bool = False
    vane_count: int = 0
    vane_thickness: float = 4.0
    vane_inner_diameter: float | None = None
    vane_outer_diameter: float | None = None
    curved_vanes: bool = False
    drilled_rows: tuple[tuple[int, float, float], ...] = ()
    slot_count: int = 0
    slot_length: float = 42.0
    slot_width: float = 7.0
    slot_angle_deg: float = 18.0
    drum_in_hat: bool = False
    drum_inner_diameter: float | None = None
    drum_depth: float = 0.0
    internal_spline_count: int = 0
    internal_spline_groove_depth: float = 0.0
    internal_spline_groove_width: float = 0.0


def brake_disc_presets() -> dict[str, BrakeDiscSpec]:
    """Representative brake disc examples from docs/categories/brake_disc.md."""
    return {
        "brake_disc-001": BrakeDiscSpec(
            dataset_id="brake_disc-001",
            name="brake_disc-001",
            display_name="Compact Solid Hat Disc",
            description="Small solid rear-style brake disc with a shallow hat and mounting pattern.",
            outer_diameter=252,
            friction_inner_diameter=126,
            thickness=12,
            center_bore_diameter=62,
            hub_diameter=128,
            hat_height=18,
            hat_wall_thickness=8,
            bolt_count=4,
            bolt_circle_diameter=100,
            bolt_hole_diameter=12,
        ),
        "brake_disc-002": BrakeDiscSpec(
            dataset_id="brake_disc-002",
            name="brake_disc-002",
            display_name="Straight-Vane Ventilated Disc",
            description="Passenger-car ventilated brake disc with straight radial vanes and a low hat.",
            outer_diameter=300,
            friction_inner_diameter=150,
            thickness=26,
            center_bore_diameter=68,
            hub_diameter=154,
            hat_height=8,
            hat_wall_thickness=9,
            bolt_count=5,
            bolt_circle_diameter=112,
            bolt_hole_diameter=13,
            ventilated=True,
            vane_count=32,
            vane_thickness=4.5,
            mounting_flange_thickness=6.0,
        ),
        "brake_disc-003": BrakeDiscSpec(
            dataset_id="brake_disc-003",
            name="brake_disc-003",
            display_name="Staggered Spiral-Vane Ventilated Disc",
            description="Performance-style ventilated brake disc with segmented spiral cooling vanes and a low hat.",
            outer_diameter=340,
            friction_inner_diameter=166,
            thickness=30,
            center_bore_diameter=72,
            hub_diameter=166,
            hat_height=8,
            hat_wall_thickness=10,
            bolt_count=5,
            bolt_circle_diameter=120,
            bolt_hole_diameter=14,
            ventilated=True,
            vane_count=36,
            vane_thickness=4.5,
            curved_vanes=True,
            mounting_flange_thickness=6.0,
        ),
        "brake_disc-004": BrakeDiscSpec(
            dataset_id="brake_disc-004",
            name="brake_disc-004",
            display_name="Three-Row Cross-Drilled Ventilated Disc",
            description="Ventilated brake disc with straight vanes and three concentric rows of cross-drilled face holes.",
            outer_diameter=330,
            friction_inner_diameter=160,
            thickness=28,
            center_bore_diameter=70,
            hub_diameter=160,
            hat_height=8,
            hat_wall_thickness=9,
            bolt_count=5,
            bolt_circle_diameter=114.3,
            bolt_hole_diameter=13,
            ventilated=True,
            vane_count=34,
            drilled_rows=((34, 102, 5.5), (34, 126, 6.0), (34, 150, 5.5)),
            mounting_flange_thickness=6.0,
        ),
        "brake_disc-005": BrakeDiscSpec(
            dataset_id="brake_disc-005",
            name="brake_disc-005",
            display_name="Angled-Slot Ventilated Disc",
            description="Ventilated brake disc with straight vanes and repeated shallow angled slots on the friction faces.",
            outer_diameter=330,
            friction_inner_diameter=160,
            thickness=28,
            center_bore_diameter=70,
            hub_diameter=160,
            hat_height=8,
            hat_wall_thickness=9,
            bolt_count=5,
            bolt_circle_diameter=114.3,
            bolt_hole_diameter=13,
            ventilated=True,
            vane_count=34,
            slot_count=18,
            slot_length=48,
            slot_width=7,
            slot_angle_deg=22,
            mounting_flange_thickness=6.0,
        ),
        "brake_disc-006": BrakeDiscSpec(
            dataset_id="brake_disc-006",
            name="brake_disc-006",
            display_name="Heavy Straight-Vane Ventilated Disc",
            description="Large thick ventilated brake disc with dense straight vanes and a heavy-duty hub pattern.",
            outer_diameter=380,
            friction_inner_diameter=188,
            thickness=34,
            center_bore_diameter=92,
            hub_diameter=190,
            hat_height=10,
            hat_wall_thickness=12,
            bolt_count=6,
            bolt_circle_diameter=139.7,
            bolt_hole_diameter=15,
            ventilated=True,
            vane_count=42,
            vane_thickness=5.5,
            mounting_flange_thickness=7.0,
        ),
        "brake_disc-007": BrakeDiscSpec(
            dataset_id="brake_disc-007",
            name="brake_disc-007",
            display_name="Deep-Hat Parking-Drum Disc",
            description="Rear brake disc with a deep hat cavity for an integrated parking-brake drum and a far-end mounting flange.",
            outer_diameter=310,
            friction_inner_diameter=168,
            thickness=14,
            center_bore_diameter=68,
            hub_diameter=176,
            hat_height=54,
            hat_wall_thickness=10,
            bolt_count=5,
            bolt_circle_diameter=112,
            bolt_hole_diameter=13,
            mounting_flange_thickness=6.0,
            mounting_flange_outer_diameter=168,
            mounting_flange_position="inner_side",
            drum_in_hat=True,
            drum_inner_diameter=168,
            drum_depth=42,
        ),
        "brake_disc-008": BrakeDiscSpec(
            dataset_id="brake_disc-008",
            name="brake_disc-008",
            display_name="Flat Toothed-Bore Disc",
            description="Flat non-ventilated annular disc with a toothed internal bore and no hat or bolt flange.",
            outer_diameter=292,
            friction_inner_diameter=92,
            thickness=18,
            center_bore_diameter=92,
            hub_diameter=0,
            hat_height=0,
            hat_wall_thickness=0,
            bolt_count=0,
            bolt_circle_diameter=0,
            bolt_hole_diameter=0,
            has_hat=False,
            has_mounting_flange=False,
            ventilated=False,
            vane_count=0,
            vane_thickness=4.0,
            internal_spline_count=24,
            internal_spline_groove_depth=8.0,
            internal_spline_groove_width=5.5,
        ),
        "brake_disc-009": BrakeDiscSpec(
            dataset_id="brake_disc-009",
            name="brake_disc-009",
            display_name="Offset Tube-Hub Inner-Flange Ventilated Disc",
            description="Ventilated friction ring offset from an inner mounting flange by a cylindrical tube hub.",
            outer_diameter=326,
            friction_inner_diameter=176,
            thickness=24,
            center_bore_diameter=130,
            hub_diameter=220,
            hat_height=50,
            hat_wall_thickness=8,
            bolt_count=5,
            bolt_circle_diameter=250,
            bolt_hole_diameter=12,
            mounting_flange_thickness=6.0,
            mounting_flange_outer_diameter=286,
            mounting_flange_position="inner_side",
            ventilated=True,
            vane_count=30,
            vane_thickness=4.0,
        ),
    }


def make_brake_disc(spec: BrakeDiscSpec):
    """Build a CadQuery solid for a brake disc specification."""
    try:
        import cadquery as cq
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on local CAD install
        raise RuntimeError(
            "CadQuery is required to build brake disc STEP models. Install dependencies with "
            "`python -m pip install -r requirements.txt` using Python 3.10-3.12."
        ) from exc

    if spec.internal_spline_count and not spec.has_hat and not spec.ventilated:
        model = _internal_spline_rotor(cq, spec)
    else:
        model = _ventilated_rotor(cq, spec) if spec.ventilated else _solid_rotor(cq, spec)
    hat = _hat(cq, spec)
    if hat is not None:
        model = model.union(hat)
    model = _cut_mounting_pattern(cq, model, spec)

    if spec.internal_spline_count and spec.has_hat:
        model = _cut_internal_splines(cq, model, spec)
    if spec.drilled_rows:
        model = _cut_drilled_pattern(cq, model, spec)
    if spec.slot_count:
        model = _cut_slots(cq, model, spec)
    if spec.drum_in_hat:
        model = _cut_drum_cavity(cq, model, spec)

    return _soften_edges(model)


def _ring(cq, outer_diameter: float, inner_diameter: float, height: float, z_center: float):
    return (
        cq.Workplane("XY")
        .workplane(offset=z_center - height / 2)
        .circle(outer_diameter / 2)
        .circle(inner_diameter / 2)
        .extrude(height)
    )


def _solid_rotor(cq, spec: BrakeDiscSpec):
    return _ring(cq, spec.outer_diameter, spec.friction_inner_diameter, spec.thickness, 0)


def _internal_spline_rotor(cq, spec: BrakeDiscSpec):
    points = _internal_spline_points(
        spec.internal_spline_count,
        spec.center_bore_diameter / 2,
        spec.internal_spline_groove_depth,
    )
    return (
        cq.Workplane("XY")
        .workplane(offset=-spec.thickness / 2)
        .circle(spec.outer_diameter / 2)
        .polyline(points)
        .close()
        .extrude(spec.thickness)
    )


def _ventilated_rotor(cq, spec: BrakeDiscSpec):
    plate_thickness = max(6.0, spec.thickness * 0.28)
    air_gap = spec.thickness - 2 * plate_thickness
    plate_offset = air_gap / 2 + plate_thickness / 2
    model = _ring(
        cq,
        spec.outer_diameter,
        spec.friction_inner_diameter,
        plate_thickness,
        plate_offset,
    )
    model = model.union(
        _ring(cq, spec.outer_diameter, spec.friction_inner_diameter, plate_thickness, -plate_offset)
    )

    inner = spec.vane_inner_diameter or spec.friction_inner_diameter + 10
    outer = spec.vane_outer_diameter or spec.outer_diameter - 18
    for index in range(spec.vane_count):
        angle = 360.0 * index / spec.vane_count
        vane = (
            _curved_vane(cq, inner / 2, outer / 2, air_gap, spec.vane_thickness, angle)
            if spec.curved_vanes
            else _straight_vane(cq, inner / 2, outer / 2, air_gap, spec.vane_thickness, angle)
        )
        model = model.union(vane)
    return model


def _straight_vane(
    cq,
    inner_radius: float,
    outer_radius: float,
    height: float,
    width: float,
    angle: float,
):
    length = outer_radius - inner_radius
    radius = (inner_radius + outer_radius) / 2
    return (
        cq.Workplane("XY")
        .box(length, width, height, centered=(True, True, True))
        .translate((radius, 0, 0))
        .rotate((0, 0, 0), (0, 0, 1), angle)
    )


def _curved_vane(
    cq,
    inner_radius: float,
    outer_radius: float,
    height: float,
    width: float,
    angle: float,
):
    segments = 7
    total_sweep = 24.0
    result = None
    for segment in range(segments):
        t0 = segment / segments
        t1 = (segment + 1) / segments
        radius = inner_radius + (outer_radius - inner_radius) * (t0 + t1) / 2
        local_angle = angle + total_sweep * (t0 + t1) / 2
        length = (outer_radius - inner_radius) / segments * 1.35
        part = (
            cq.Workplane("XY")
            .box(length, width, height, centered=(True, True, True))
            .translate((radius, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), local_angle)
        )
        result = part if result is None else result.union(part)
    return result


def _hat(cq, spec: BrakeDiscSpec):
    if not spec.has_hat:
        return None

    hat = (
        cq.Workplane("XY")
        .workplane(offset=-spec.thickness / 2)
        .circle(spec.hub_diameter / 2)
        .circle(spec.center_bore_diameter / 2)
        .extrude(-spec.hat_height)
    )
    if not spec.has_mounting_flange:
        return hat

    flange_thickness = spec.mounting_flange_thickness or spec.hat_wall_thickness
    flange_outer_diameter = spec.mounting_flange_outer_diameter or spec.friction_inner_diameter + 18
    if spec.mounting_flange_position == "inner_side":
        flange_z = -spec.thickness / 2 - spec.hat_height + flange_thickness / 2
    else:
        flange_z = -spec.thickness / 2 - flange_thickness / 2

    flange = _ring(
        cq,
        flange_outer_diameter,
        spec.center_bore_diameter,
        flange_thickness,
        flange_z,
    )
    return hat.union(flange)


def _cut_mounting_pattern(cq, model, spec: BrakeDiscSpec):
    if spec.bolt_count <= 0 or spec.bolt_hole_diameter <= 0:
        return model

    points = _polar_points(spec.bolt_count, spec.bolt_circle_diameter / 2)
    flange_thickness = spec.mounting_flange_thickness or spec.hat_wall_thickness
    if spec.has_mounting_flange and spec.mounting_flange_position == "inner_side":
        flange_bottom_z = -spec.thickness / 2 - spec.hat_height
        bottom_z = flange_bottom_z - 1.0
        top_z = flange_bottom_z + flange_thickness + 1.0
    else:
        bottom_z = -spec.thickness / 2 - spec.hat_height - flange_thickness - 2.0
        top_z = spec.thickness / 2 + 2.0

    cutter = (
        cq.Workplane("XY")
        .workplane(offset=bottom_z)
        .pushPoints(points)
        .circle(spec.bolt_hole_diameter / 2)
        .extrude(top_z - bottom_z)
    )
    return model.cut(cutter)


def _cut_internal_splines(cq, model, spec: BrakeDiscSpec):
    if spec.internal_spline_groove_depth <= 0 or spec.internal_spline_groove_width <= 0:
        return model

    inner_radius = spec.center_bore_diameter / 2
    groove_radius = inner_radius + spec.internal_spline_groove_depth / 2
    cutter_height = spec.thickness + spec.hat_height + 20
    for index in range(spec.internal_spline_count):
        angle = 360.0 * index / spec.internal_spline_count
        cutter = (
            cq.Workplane("XY")
            .box(
                spec.internal_spline_groove_depth * 1.8,
                spec.internal_spline_groove_width,
                cutter_height,
                centered=(True, True, True),
            )
            .translate((groove_radius, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        model = model.cut(cutter)
    return model


def _cut_drilled_pattern(cq, model, spec: BrakeDiscSpec):
    for row_index, (count, radius, diameter) in enumerate(spec.drilled_rows):
        phase = _drilled_row_phase(spec, row_index, count)
        points = _polar_points(count, radius, phase)
        cutter = cq.Workplane("XY").pushPoints(points).circle(diameter / 2).extrude(160)
        model = model.cut(cutter.translate((0, 0, -80)))
    return model


def _drilled_row_phase(spec: BrakeDiscSpec, row_index: int, hole_count: int) -> float:
    if spec.vane_count <= 0:
        return row_index * 360.0 / (hole_count * 2)
    if spec.vane_count % hole_count == 0 or hole_count % spec.vane_count == 0:
        vane_pitch = 360.0 / spec.vane_count
        return vane_pitch * (0.5 + row_index)
    return row_index * 360.0 / (hole_count * 2)


def _cut_slots(cq, model, spec: BrakeDiscSpec):
    top_z = spec.thickness / 2
    depth = min(2.0, spec.thickness * 0.12)
    radius = (spec.outer_diameter / 2 + spec.friction_inner_diameter / 2) / 2
    for index in range(spec.slot_count):
        angle = 360.0 * index / spec.slot_count
        for z, sign in ((top_z - depth / 2, 1), (-top_z + depth / 2, -1)):
            cutter = (
                cq.Workplane("XY")
                .box(spec.slot_length, spec.slot_width, depth, centered=(True, True, True))
                .translate((radius, 0, z))
                .rotate((0, 0, 0), (0, 0, 1), angle + sign * spec.slot_angle_deg)
            )
            model = model.cut(cutter)
    return model


def _cut_drum_cavity(cq, model, spec: BrakeDiscSpec):
    if spec.drum_inner_diameter is None or spec.drum_depth <= 0:
        return model
    protected_end_thickness = (
        spec.mounting_flange_thickness or spec.hat_wall_thickness
        if spec.has_mounting_flange and spec.mounting_flange_position == "inner_side"
        else 0.0
    )
    if spec.has_mounting_flange and spec.mounting_flange_position == "inner_side":
        cavity_depth = max(spec.hat_height - protected_end_thickness, 0.0)
    else:
        cavity_depth = min(spec.drum_depth, max(spec.hat_height - protected_end_thickness, 0.0))
    if cavity_depth <= 0:
        return model
    disc_side_z = -spec.thickness / 2
    far_end_z = disc_side_z - spec.hat_height
    cavity = (
        cq.Workplane("XY")
        .workplane(offset=disc_side_z)
        .circle(spec.drum_inner_diameter / 2)
        .circle(spec.center_bore_diameter / 2)
        .extrude(-cavity_depth)
    )
    return model.cut(cavity)


def _soften_edges(model):
    try:
        return model.edges().fillet(0.8)
    except Exception:
        return model


def _polar_points(count: int, radius: float, phase_deg: float = 0.0) -> list[tuple[float, float]]:
    phase = phase_deg * pi / 180.0
    return [
        (radius * cos(phase + 2 * pi * index / count), radius * sin(phase + 2 * pi * index / count))
        for index in range(count)
    ]


def _internal_spline_points(count: int, root_radius: float, groove_depth: float):
    points = []
    for index in range(count * 2):
        radius = root_radius + (groove_depth if index % 2 else 0.0)
        angle = tau * index / (count * 2)
        points.append((radius * cos(angle), radius * sin(angle)))
    return points


def preset_with_name(name: str, **changes: object) -> BrakeDiscSpec:
    """Return a named preset with optional dataclass field overrides."""
    return replace(brake_disc_presets()[name], **changes)


def brake_disc_metadata(
    spec: BrakeDiscSpec,
    dimensions_mm: dict[str, float] | None = None,
    last_change: str | None = None,
) -> dict[str, object]:
    """Return stable catalog metadata for generated brake disc artifacts."""
    change_time = last_change or datetime.now().strftime(METADATA_DATETIME_FORMAT)
    metadata: dict[str, object] = {
        "full_id": spec.dataset_id,
        "nice_name": spec.display_name,
        "description": spec.description,
        "created": BRAKE_DISC_CREATED,
        "last_change": change_time,
        "source": BRAKE_DISC_SOURCE,
        "material": BRAKE_DISC_MATERIAL,
        "category": BRAKE_DISC_CATEGORY,
    }
    if dimensions_mm:
        metadata["dimensions_mm"] = dimensions_mm
        metadata["dimensions_label"] = (
            f"{dimensions_mm['x']:.1f} x {dimensions_mm['y']:.1f} x "
            f"{dimensions_mm['z']:.1f} mm"
        )
    return metadata


def brake_disc_index_item(
    spec: BrakeDiscSpec,
    dimensions_mm: dict[str, float] | None = None,
    last_change: str | None = None,
) -> dict[str, object]:
    """Return compact catalog data for generated/index.json."""
    change_time = last_change or datetime.now().strftime(METADATA_DATETIME_FORMAT)
    item: dict[str, object] = {
        "id": spec.dataset_id,
        "name": spec.display_name,
        "description": spec.description,
        "created": BRAKE_DISC_CREATED,
        "last_change": change_time,
        "source": BRAKE_DISC_SOURCE,
        "material": BRAKE_DISC_MATERIAL,
        "category": BRAKE_DISC_CATEGORY,
    }
    if dimensions_mm:
        item["dimensions_mm"] = dimensions_mm
        item["dimensions_label"] = (
            f"{dimensions_mm['x']:.1f} x {dimensions_mm['y']:.1f} x "
            f"{dimensions_mm['z']:.1f} mm"
        )
    return item
