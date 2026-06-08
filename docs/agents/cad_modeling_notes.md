# CAD Modeling Notes

These notes capture practical lessons from the playground pipe experiments. They
are intended to save time when adding more complex hollow castings.

## Threaded Fitting Baseline

- Treat pipe fittings as cast bodies first, then add functional thread detail.
  Do not build a fitting from separate "thread objects" floating near a tube.
- For R1 pipe fittings, keep the part metadata explicit about the thread
  family. The playground R1 fittings use ISO 7-1 / EN 10226-1 BSPT proportions:
  11 TPI, 25.4 / 11 mm pitch, 55 degree flank angle, 1:16 diameter taper, and
  a 33.249 mm R1 major diameter.
- Use a real helical sweep for threads. Stacked rings or short circular groove
  segments read as broken geometry and are especially obvious inside female
  sockets.
- For male BSPT threads, model the tapered root body first, then sweep a
  triangular helical ridge and fuse it into the root body. Give the ridge root a
  small overlap into the body before fusing, otherwise the mesh can look like a
  separate material sitting on the surface.
- Place male ridges relative to the smallest useful thread diameter, not the
  average taper diameter. This avoids ridges hovering above or slicing through
  the conical body.
- For female BSPT threads, subtract a triangular helical groove from the socket
  bore. The triangle base should start at or slightly overlap the bore surface;
  the point cuts outward into the surrounding material. If the base is placed
  inside the wall, the result looks inverted.
- Align female thread cuts to the exact socket bore axis and bore diameter. A
  small axis or diameter mismatch makes the thread visible on only part of the
  circumference, as if the screw is eccentric.
- Add a short lead-in/chamfer cut at female mouths so the first thread does not
  start as a hard boolean edge at the opening.
- Use `cq.Wire.makeHelix(pitch, height, radius, start, direction)` and sweep a
  triangular profile with `cq.Solid.sweep(..., isFrenet=True)`. Build the
  triangle from the helix start point, its tangent, and the radial vector from
  the thread axis. This keeps the profile oriented to the screw instead of to a
  global plane.
- Validate thread depth and turns from the pitch and usable length. For example,
  an R1 thread length of 18-22 mm gives roughly 6.5-8.2 effective turns after a
  small lead allowance.

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
- For tees and crosses, build the whole outer casting from fused cylinders and
  socket solids, then subtract all bores and thread grooves in one pass. Closing
  an unused shoulder after making a cross-like body is error-prone; create only
  the actual branches that the fitting needs.
- Keep cast tube walls visually thin unless the real fitting needs a socket or
  wrench feature. Oversized bodies make tees, crosses, and bends look like
  machined blocks rather than cast pipe fittings.
- Female threaded sockets need enough wall thickness around the thread, but the
  reinforcement should read as the socket body, not as a small bead at the end.
  Blend from socket diameter to tube diameter with a short smooth transition.
- Add a small full-round or torus-like radius on the outside diameter at female
  socket mouths. This radius belongs on the largest outer perimeter of the
  opening, not on the inner bore/thread edge.
- Keep socket end radii modest. Large mouth radii can deform hex flats or make
  the socket look bulbous.
- Avoid tangent-only fuses and cuts. Give overlapping solids and cutters a small
  positive overlap so OpenCascade has real volume to resolve.

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
- Bends and elbows should follow one continuous centerline. Do not place both
  threaded ends along the same global axis; rotate each end to follow the local
  tube tangent.
- For long bends, keep a smooth curved tube with straight threaded tails long
  enough to contain the screw. For compact elbows, use a tighter centerline
  radius and a slightly thicker uniform body rather than separate end bosses and
  a thin middle.
- If a compact elbow starts to look like two screws smashed together, increase
  the straight tail length or centerline radius slightly. The thread solids
  should come close, but not overlap.
- For wave or bridge-like parts, use one smooth swept tube on a wavy axis. Do
  not approximate it as a collection of straight tubes unless the source part is
  actually segmented.

## Profile Placement

- For curved pipes, sample the path with `positionAt(t)` and `tangentAt(t)`.
- Pass the path tangent as the profile normal when creating circle or ellipse
  wires.
- Use a consistent profile x-direction, such as `cq.Vector(0, 0, 1)`, so ellipse
  squash does not twist unexpectedly along the bend.
- Use `smoothstep(t)` for gradual cross-section changes. It prevents a harsh
  derivative change at the start or end of taper/squash transitions.
- For multi-port fittings, define each port with a point and an inward direction.
  Reuse that pair for socket solids, bore cuts, mouth radii, and thread grooves
  so every feature shares the same axis.
- When a threaded feature looks disconnected or only partially visible, inspect
  axis direction, helix start point, bore diameter, and taper radius before
  changing the visual profile. Most of these defects come from placement, not
  from thread styling.

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
