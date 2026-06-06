# CAD Modeling Notes

These notes capture practical lessons from the playground pipe experiments. They
are intended to save time when adding more complex hollow castings.

## Hollow Pipe Strategy

- Prefer modeling complex hollow flow parts as `outer solid - bore solid`.
- For side inlets, make the inlet bore overlap the receiving tube bore. Do not
  let the inlet only touch the outside wall, because that can leave a sealed
  sliver or an internal obstacle.
- When joining a side inlet into a main tube, build and fuse the outer bodies,
  build and fuse the bore bodies, then subtract the fused bore from the fused
  outer body.
- Use matching profiles at shared interfaces. This helps avoid leaks, lips, and
  boolean artifacts.

## Sweeps and Lofts

- `cq.Solid.sweep_multi()` works well for a tapered or morphing bend when each
  section wire is placed perpendicular to the local path tangent.
- `cq.Solid.sweep()` with an outer wire plus inner wires can produce shells or
  near-zero-volume compounds in this CadQuery/OpenCascade setup. Check volume
  and validity before trusting it.
- `cq.Solid.makeTorus()` angle arguments clip the tube cross-section here; they
  are not a good way to make a quarter-bend pipe.
- For straight transitions, `cq.Solid.makeLoft()` over section wires is often
  more robust than `sweep_multi()` over a line.
- A single sweep over an arc plus a straight segment can become an invalid
  compound. Splitting into a bend sweep plus a straight loft, then fusing, was
  more stable.

## Profile Placement

- For curved pipes, sample the path with `positionAt(t)` and `tangentAt(t)`.
- Pass the path tangent as the profile normal when creating circle or ellipse
  wires.
- Use a consistent profile x-direction, such as `cq.Vector(0, 0, 1)`, so ellipse
  squash does not twist unexpectedly along the bend.
- Use `smoothstep(t)` for gradual cross-section changes. It prevents a harsh
  derivative change at the start or end of taper/squash transitions.

## Area-Preserving Squash

To squash a circular bore by 30 percent while preserving area:

```python
minor_radius = circle_radius * 0.7
major_radius = circle_radius / 0.7
```

The ellipse area remains equal to the circle area because:

```text
pi * (r * 0.7) * (r / 0.7) = pi * r^2
```

## Validation

Always validate both CAD and mesh outputs:

```python
shape = model.val()
print(shape.ShapeType(), shape.isValid(), shape.Volume())
```

For generated GLB files:

```python
import trimesh

mesh = trimesh.load("path/to/model.glb", force="mesh")
print(mesh.extents, mesh.is_empty)
```

Also verify the local browser serves both the model page and GLB asset.
