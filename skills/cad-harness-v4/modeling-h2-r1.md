---
name: freecad-modeling
description: Interpret dimensioned mechanical part descriptions and choose editable native FreeCAD PartDesign constructions for the CAD harness. The CLI owns execution, checks, budgets, and artifacts.
---

# FreeCAD modeling judgment

Interpret the user's dimensions, placement, and machining targets without adding or dropping requirements. Distinguish diameter from radius, pitch from total span, and absolute coordinates from dimensions. Report unsupported or ambiguous requirements through the driver's output contract; do not approximate them silently.

For supported geometry, return the declarative specification requested by the driver. Choose geometric intent, not a feature graph. The deterministic compiler chooses its recipe. Do not request or read evaluation gold, fixtures, reports, or description hashes.

For a supported declarative spec, resolve relative datums to world coordinates in one unit before emitting numbers. For a circle measured clockwise from +Y, use x = cx + R*sin(a), y = cy + R*cos(a), with angles in radians and R half the pitch-circle diameter. Derive pocket bounds from its center and half spans, and top_z from the world Z datum.

Keep Profile, support, Body membership, dependencies, and Tip consistent. Face attachment is preferred for top-face machining when reliable; explicit placement is acceptable. Put dress-up features after the main cuts. Select edges by position and direction rather than fixed topology indices. Avoid UseAllEdges and extra machining.

Profile links belong to the native feature that consumes a Sketch; a final Fillet/Chamfer/Pattern need not have its own Profile. Radius constraints may drive diameters, and symmetric half-width constraints may drive full widths. Preserve actual driving dimensions rather than notes or unused custom properties.

Use the failed expected/actual measurements to revise an unconfirmed interpretation or agent source. Do not change the user request, grading tolerances, confirmed spec, compiler, or harness environment. Repeating an identical failed spec is not a repair.

The driver supplies the units/defaults, schema and output contract separately. The CLI creates and closes documents, runs probes, exports and reimports files, classifies failures, and limits attempts and time. Do not perform shell, file, network, or lifecycle operations from generated construction code.
