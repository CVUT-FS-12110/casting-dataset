from __future__ import annotations

import tempfile
from collections.abc import Iterable
from pathlib import Path


SECTION_AXES = {
    "x": ((1.0, 0.0, 0.0), (1, 2), "YZ"),
    "y": ((0.0, 1.0, 0.0), (0, 2), "XZ"),
    "z": ((0.0, 0.0, 1.0), (0, 1), "XY"),
}


def export_glb(step_path: Path, glb_path: Path) -> Path:
    """Convert a STEP file to a cached GLB mesh."""
    try:
        import gmsh
        import trimesh
    except ImportError as exc:  # pragma: no cover - depends on local CAD install
        raise RuntimeError(f"Missing mesh conversion dependency: {exc.name}") from exc

    glb_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        stl_path = Path(tmp_dir) / "model.stl"

        gmsh.initialize(interruptible=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("Mesh.MeshSizeMin", 1.5)
            gmsh.option.setNumber("Mesh.MeshSizeMax", 14.0)
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 16)
            gmsh.option.setNumber("Mesh.MinimumCirclePoints", 40)
            gmsh.merge(str(step_path))
            gmsh.model.mesh.generate(2)
            gmsh.write(str(stl_path))
        finally:
            gmsh.finalize()

        mesh = trimesh.load(stl_path)
        mesh.export(glb_path)

    return glb_path


def measured_dimensions(glb_path: Path) -> dict[str, float] | None:
    if not glb_path.exists():
        return None
    try:
        import trimesh
    except ImportError:
        return None

    mesh = trimesh.load(glb_path, force="mesh")
    if mesh.is_empty:
        return None
    x, y, z = (round(float(value), 1) for value in mesh.extents)
    return {"x": x, "y": y, "z": z}


def export_section_pngs(glb_path: Path, output_dir: Path, model_id: str) -> list[Path]:
    try:
        import trimesh
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - depends on local CAD install
        raise RuntimeError(f"Missing section rendering dependency: {exc.name}") from exc

    mesh = trimesh.load(glb_path, force="mesh")
    if mesh.is_empty:
        raise RuntimeError(f"Could not load mesh for sections: {glb_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for axis, (normal, projection, label) in SECTION_AXES.items():
        origin = mesh.bounds.mean(axis=0)
        section = mesh.section(plane_origin=origin, plane_normal=normal)
        target = output_dir / f"{model_id}-{axis}.png"
        _draw_section_png(
            section.discrete if section is not None else [],
            projection,
            label,
            target,
            Image,
            ImageDraw,
        )
        outputs.append(target)
    return outputs


def _draw_section_png(
    polylines: Iterable,
    projection: tuple[int, int],
    label: str,
    target: Path,
    image_module,
    draw_module,
) -> None:
    size = 560
    margin = 42
    lines = [line[:, projection] for line in polylines if len(line) > 1]
    image = image_module.new("RGB", (size, size), "#f7f9fb")
    draw = draw_module.Draw(image)
    draw.rectangle((0, 0, size - 1, size - 1), outline="#d8dee6")
    draw.text((14, 12), f"{label} section", fill="#1f2933")

    if not lines:
        draw.text((margin, size // 2), "No section at model center", fill="#52616f")
        image.save(target)
        return

    all_points = [point for line in lines for point in line]
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    span_x = max(max_x - min_x, 1e-6)
    span_y = max(max_y - min_y, 1e-6)
    scale = min((size - margin * 2) / span_x, (size - margin * 2) / span_y)

    def pixel(point):
        x = margin + (point[0] - min_x) * scale
        y = size - margin - (point[1] - min_y) * scale
        return (x, y)

    for line in lines:
        draw.line([pixel(point) for point in line], fill="#101820", width=2, joint="curve")

    image.save(target)
