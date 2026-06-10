# Brake Discs 3D Model Dataset

## Goal
Create a compact but representative collection of common cast-iron brake disc CAD models for:
- classification,
- embedding learning,
- retrieval/similarity search,
- synthetic dataset generation.

The dataset should cover the most common real-world brake disc geometries while avoiding rare or exotic designs.

---

# Recommended Core Model Set

# List of Discs

| Full ID | Nice name | Description |
| --- | --- | --- |
| brake_discs-001 | Compact Solid Hat Disc | Small solid rear-style brake disc with a shallow hat and mounting pattern. |
| brake_discs-002 | Straight-Vane Ventilated Disc | Passenger-car ventilated brake disc with straight radial vanes and a low hat. |
| brake_discs-003 | Staggered Spiral-Vane Ventilated Disc | Performance-style ventilated brake disc with segmented spiral cooling vanes and a low hat. |
| brake_discs-004 | Three-Row Cross-Drilled Ventilated Disc | Ventilated brake disc with straight vanes and three concentric rows of cross-drilled face holes. |
| brake_discs-005 | Angled-Slot Ventilated Disc | Ventilated brake disc with straight vanes and repeated shallow angled slots on the friction faces. |
| brake_discs-006 | Heavy Straight-Vane Ventilated Disc | Large thick ventilated brake disc with dense straight vanes and a heavy-duty hub pattern. |
| brake_discs-007 | Deep-Hat Parking-Drum Disc | Rear brake disc with a deep hat cavity for an integrated parking-brake drum and a far-end mounting flange. |
| brake_discs-008 | Flat Toothed-Bore Disc | Flat non-ventilated annular disc with a toothed internal bore and no hat or bolt flange. |
| brake_discs-009 | Offset Tube-Hub Inner-Flange Ventilated Disc | Ventilated friction ring offset from an inner mounting flange by a cylindrical tube hub. |

## 1. Small Solid Disc

### Purpose
Rear axle discs for small city cars.

### Geometry
- Solid (non-ventilated)
- Simple flat structure
- Minimal offset
- 4–5 mounting holes

### Typical Dimensions
- Diameter: 240–260 mm
- Thickness: 10–13 mm

### Importance
Baseline geometry and simplest topology.

---

## 2. Standard Ventilated Disc

### Purpose
Most common front brake discs in passenger vehicles.

### Geometry
- Two friction plates
- Internal cooling vanes
- Low center hat/tube, approximately one friction-plate layer tall
- Thin mounting plate with bolt holes

### Typical Dimensions
- Diameter: 280–320 mm
- Thickness: 22–30 mm

### Variants
- Straight radial vanes
- Curved vanes

### Importance
Main representative of modern brake discs.

---

## 3. Curved-Vane Ventilated Disc

### Purpose
Higher airflow cooling for sport/performance vehicles.

### Geometry
- Spiral/curved internal vanes
- Directional airflow structure
- Asymmetric internal topology
- Low center hat/tube, approximately one friction-plate layer tall
- Thin mounting plate with bolt holes

### Typical Dimensions
- Diameter: 300–360 mm

### Importance
Adds important internal topology variation.

---

## 4. Drilled Disc

### Purpose
Performance-oriented cooling and gas evacuation.

### Geometry
- Ventilated structure
- Circular drilled hole patterns
- Low center hat/tube, approximately one friction-plate layer tall
- Thin mounting plate with bolt holes

### Typical Dimensions
- Diameter: 300–380 mm

### Variants
- Dense small holes
- Sparse large holes

### Importance
Strongly visually distinctive category.

---

## 5. Slotted Disc

### Purpose
Performance and utility braking.

### Geometry
- Machined radial or spiral slots
- No drilled holes
- Low center hat/tube, approximately one friction-plate layer tall
- Thin mounting plate with bolt holes

### Typical Dimensions
- Diameter: 300–380 mm

### Importance
Different surface topology than drilled discs.

---

## 6. Heavy-Duty SUV / Van Disc

### Purpose
SUVs, pickups, utility vehicles.

### Geometry
- Thick ventilated structure
- Large thermal mass
- Low but robust center hat/tube
- Thin mounting plate with bolt holes

### Typical Dimensions
- Diameter: 330–400 mm

### Importance
Important scale and proportion variation.

---

## 7. Drum-in-Hat Disc

### Purpose
Rear discs with integrated parking brake drum.

### Geometry
- Deep internal drum cavity
- More complex cross-section
- Thin tube-style offset body similar to the tube-connected variant
- No mounting flange at the disc-side/tube-root level
- No annular plate at the disc-side/tube-root level; the hat is open there
- Tube inner diameter aligns with the friction-ring inner diameter, so there is
  no inner step at the tube root
- Single mounting flange located on the top/far end of the thin tube, away from
  the friction-ring side
- Bolt holes visibly cut into that smaller inner end flange
- Drum cavity stops before the far-end flange so the mounting plate remains
  intact

### Importance
Very common modern automotive geometry.

---

## 8. Internal-Spline Disc Without Flange

### Purpose
Disc mounted through an internal spline profile instead of a bolt-hole flange.

### Geometry
- Simple solid, non-ventilated annular disc
- No hat
- No mounting flange
- No bolt holes or bolt-hole boss
- No separate center hub feature
- No raised center region; the model is one flat-thickness disc body
- Internal spline grooves cut directly into the central bore, replacing the
  usual flange/bolt-hole mounting interface

### Importance
Adds a no-flange, no-hub topology with a distinctive internal torque-transfer
interface.

---

## 9. Tube-Connected Inner-Flange Disc

### Purpose
Disc where the friction ring is offset from the mounting face by a cylindrical tube.

### Geometry
- Ventilated friction ring
- Cylindrical middle tube
- Mounting flange connected to the inner side of the tube relative to the
  friction ring
- Full-height end mounting flange, not a near-zero-thickness plate
- Bolt holes placed in the outer annulus of the inner-side mounting flange,
  outside the cylindrical tube wall
- The tube should visibly overlap/intersect the friction ring so the parts read
  as one connected casting, not as barely touching bodies

### Importance
Adds a clear offset-disc shape with separated friction-ring and mounting-flange
regions.

---

# Optional Extended Models

## 10. Combined Drilled + Slotted Disc
- Combination of holes and slots
- Common aftermarket/performance style

## 11. Truck / Bus Disc
- Very large heavy-duty geometry
- Diameter typically 400–500+ mm

## 12. Two-Piece Rotor
- Cast iron friction ring
- Aluminum center hat
- Bolted assembly structure

---

# Recommended Dataset Minimum

A compact but representative dataset should include:

1. Small solid disc
2. Standard ventilated disc
3. Curved-vane ventilated disc
4. Drilled disc
5. Slotted disc
6. Heavy-duty SUV disc
7. Drum-in-hat disc
8. Internal-spline disc without flange
9. Tube-connected inner-flange disc

This already covers most commonly encountered brake disc geometries.

---

# Suggested Parametric Variations

For synthetic generation, randomly vary:

## Global Dimensions
- outer diameter
- inner diameter
- thickness
- offset
- hub diameter

## Mounting Features
- bolt count
- bolt circle diameter
- center bore size
- flange thickness
- flange location along the hub tube
- internal spline count and groove depth

## Ventilation
- vane count
- vane thickness
- straight vs curved vanes

## Surface Features
- drilled hole patterns
- slot patterns
- chamfers
- fillets

## Realism Features
- wear
- rust
- manufacturing tolerances
- edge rounding
