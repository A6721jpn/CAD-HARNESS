---
name: freecad-modeling
description: Interpret dimensioned mechanical part descriptions and choose editable native FreeCAD PartDesign constructions for the CAD harness. The CLI owns execution, checks, budgets, and artifacts.
---

# FreeCAD modeling judgment

Interpret the user's dimensions, placement, and machining targets without adding or dropping requirements. Distinguish diameter from radius, pitch from total span, and absolute coordinates from dimensions. Report unsupported or ambiguous requirements through the driver's output contract; do not approximate them silently.

For supported geometry, return the declarative specification requested by the driver. Choose geometric intent, not a feature graph. The deterministic compiler chooses its recipe. Do not request or read evaluation gold, fixtures, reports, or description hashes.

For a supported declarative spec, compute shared world-frame datums and unit conversions once. For equally spaced holes clockwise from +Y, use the first center offset (R*sin(a), R*cos(a)) and one angular-step rotation: each next offset is (x*cos(d)+y*sin(d), y*cos(d)-x*sin(d)), with angles in radians and R half the pitch-circle diameter. Reuse these common quantities rather than separately deriving every angle; retain intermediate precision and check radius and closure internally. Derive pocket bounds and top_z from the same shared datum. Emit the required numeric build-spec directly as compact JSON without redundant derivations; never add, omit, or approximate required geometry to save time.

Keep Profile, support, Body membership, dependencies, and Tip consistent. Face attachment is preferred for top-face machining when reliable; explicit placement is acceptable. Put dress-up features after the main cuts. Select edges by position and direction rather than fixed topology indices. Avoid UseAllEdges and extra machining.

Profile links belong to the native feature that consumes a Sketch; a final Fillet/Chamfer/Pattern need not have its own Profile. Radius constraints may drive diameters, and symmetric half-width constraints may drive full widths. Preserve actual driving dimensions rather than notes or unused custom properties.

Use the failed expected/actual measurements to revise an unconfirmed interpretation or agent source. Do not change the user request, grading tolerances, confirmed spec, compiler, or harness environment. Repeating an identical failed spec is not a repair.

The driver supplies the units/defaults, schema and output contract separately. The CLI creates and closes documents, runs probes, exports and reimports files, classifies failures, and limits attempts and time. Do not perform shell, file, network, or lifecycle operations from generated construction code.
