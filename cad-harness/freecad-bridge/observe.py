"""Independent B-Rep observation: no spreadsheet, sketches or compiler imports.

All reported measurements come from the supplied shape. Expected input values
are used only by compare_spec(), after measurement has completed.
"""
import math

import FreeCAD as App
import Part


TOL = 1e-6  # mm (volume comparison also uses a relative tolerance).


def _near(a, b):
    return abs(a - b) <= TOL


def measure(shape):
    """Measure the axis-aligned, XY two-hole plate from native geometry alone."""
    if shape.isNull():
        raise ValueError("Cannot measure a null shape")
    box = shape.BoundBox
    holes = []
    for face in shape.Faces:
        surface = face.Surface
        if not isinstance(surface, Part.Cylinder):
            continue
        if abs(abs(surface.Axis.z) - 1) > TOL:
            continue
        x, y = surface.Center.x, surface.Center.y
        radius = surface.Radius
        openings = []
        for z in (box.ZMin, box.ZMax):
            # Require an inner wire on the actual end face, not merely a
            # circular edge somewhere in the shape (e.g. a blind-hole floor).
            found = False
            for end in shape.Faces:
                if not isinstance(end.Surface, Part.Plane):
                    continue
                if not (_near(end.BoundBox.ZMin, z) and _near(end.BoundBox.ZMax, z)):
                    continue
                for wire in end.Wires:
                    if wire.isSame(end.OuterWire):
                        continue
                    for edge in wire.Edges:
                        curve = edge.Curve
                        if isinstance(curve, Part.Circle):
                            found |= (_near(curve.Center.x, x) and _near(curve.Center.y, y)
                                      and _near(curve.Center.z, z) and _near(curve.Radius, radius))
            openings.append(bool(found))
        probe = Part.makeCylinder(radius / 2, box.ZLength + 2,
                                  App.Vector(x, y, box.ZMin - 1), App.Vector(0, 0, 1))
        blocked_volume = shape.common(probe).Volume
        full_wall = _near(face.BoundBox.ZMin, box.ZMin) and _near(face.BoundBox.ZMax, box.ZMax)
        holes.append({"center_mm": [x, y], "diameter_mm": 2 * radius,
                      "z_span_mm": [face.BoundBox.ZMin, face.BoundBox.ZMax],
                      "end_openings": openings, "blocked_probe_volume_mm3": blocked_volume,
                      "through": all(openings) and full_wall and blocked_volume <= TOL})
    holes.sort(key=lambda hole: hole["center_mm"])
    expected_volume = (box.XLength * box.YLength
                       - sum(math.pi * (h["diameter_mm"] / 2)**2 for h in holes)) * box.ZLength
    return {"valid": shape.isValid(), "solid_count": len(shape.Solids),
            "size_mm": [box.XLength, box.YLength, box.ZLength],
            "bounds_mm": [box.XMin, box.YMin, box.ZMin, box.XMax, box.YMax, box.ZMax],
            "hole_count": len(holes), "holes": holes,
            "through": len(holes) == 2 and all(h["through"] for h in holes),
            "volume_mm3": shape.Volume, "formula_volume_mm3": expected_volume,
            "volume_formula_matches": math.isclose(shape.Volume, expected_volume, rel_tol=1e-9, abs_tol=TOL)}


def compare_spec(observation, spec):
    """Return mismatches; never replace measured values with requested values."""
    dims = {k: float(v[:-3]) for k, v in spec["dimensions"].items()}
    errors = []
    for key in ("valid", "through", "volume_formula_matches"):
        if not observation[key]:
            errors.append(key)
    if observation["solid_count"] != 1 or observation["hole_count"] != 2:
        errors.append("solid/hole count")
    expected_bounds = [-dims["L"]/2, -dims["W"]/2, 0, dims["L"]/2, dims["W"]/2, dims["T"]]
    if any(not _near(a, b) for a, b in zip(observation["bounds_mm"], expected_bounds)):
        errors.append("centered envelope")
    pitch = dims["L"] - 2*dims["e"]
    for hole, x in zip(observation["holes"], (-pitch/2, pitch/2)):
        if not (_near(hole["center_mm"][0], x) and _near(hole["center_mm"][1], 0)
                and _near(hole["diameter_mm"], dims["D"])):
            errors.append("hole diameter/center")
    volume = (dims["L"]*dims["W"] - 2*math.pi*(dims["D"]/2)**2)*dims["T"]
    if not math.isclose(observation["volume_mm3"], volume, rel_tol=1e-9, abs_tol=TOL):
        errors.append("requested volume")
    return errors
