# VERIFY v4 C S1: explicit offline capability profile

This resource is selected only by explicit `profile: "c-s1"`. It does not replace `SKILL.md`, `modeling.md`, or `contracts.md`, does not change the original profile's observations, and does not authorize provider/model calls. The implementation capability lock is not a final v4 freeze. Follow `contracts-c-s1.md` and the pinned capability policy.

## Generator boundary

Use only the canonical sanitized `cad-harness.model-inputs.v4c` packet supplied by the supervisor and the explicit user request. Never read original manifests, filesystem paths, STEP files, checker images/masks, font files/licenses, judge cards, private gold, or protected evidence. A prepared manifest digest is provenance, not permission to open a source. Do not reconstruct private acceptance tolerances from examples. Missing request choices must remain missing; do not silently invent geometry, placement, or acceptance criteria.

Return one data-only JSON plan using `cad-harness.plan.v4c` and `profile: "c-s1"`. No Python, FreeCAD scripts, macros, commands, imports, source-code strings, filenames, expression engines, or unknown fields. Always supply explicit `references` and `engravings` arrays. The host validates the plan before any native process is admitted.

## Supported construction

- `reference_fixture`: provide a valid unchanged `cad-harness.build-spec.v1` stock/pocket/hole recipe. Each reference placement names a registered asset ID and explicit `translation_mm`, nonzero `rotation_axis`, and `rotation_deg`. References are checker context only, never exported additional solids. No S2 offsets/healing or arbitrary topology edits.
- `contour_extrude`: provide a registered prepared `contour_id`, positive `width_mm`, positive `thickness_mm`, and explicit 3D `origin_mm`. The compiler consumes exact line/arc/quadratic/cubic Bezier segments; it does not trace a screenshot or substitute a bounding box. Do not put minR or checker thresholds in the plan.
- Engravings require a `font_id` from `runtime_data.inputs.fonts`, literal `text` entirely in that registry entry's `glyphs`, positive `height_mm`/`depth_mm`, 3D `origin_mm`, nonzero `rotation_axis`, and `rotation_deg`. The registry supplies authenticated font/license hashes, not files or permission to read them. Glyphs are local XY; the recessed cut is local -Z, then transformed by the declared axis-angle placement. There is no fallback font or automatic face placement.

## Interpretation of prepared evidence

STEP import preserves source X/Y/Z; numerical bounds are import-normalized millimeters. `frame.source_units` is separately recorded from import units. Never relabel a PCA direction as the user's source axis. Bounds are extents, not thickness. `thickness_mm: null` means no face-pair thickness measurement has been performed.

Face IDs are the imported shape's ordered `Face1`, `Face2`, … atlas. Signatures are quantized geometric fingerprints, not persistent topology identities. `ambiguous: true` forbids unique signature selection. Plane normals may be constant; curved-face parameter-midpoint normals are local samples, not global face normals or a certificate of tool access. Honor `normal_kind`, `normal_reason`, and coverage. Do not turn missing/partial validity into success.

Contour preprocessing permissions come exclusively from the explicit supervisor recipe. The generator cannot invent smoothing, bridging, deletion of holes/islands, physical scale, or polarity. Digest-bound independent analytic source contours are a separate provenance branch, not pretend raster preprocessing. Preserve nesting and exact segment geometry.

Declared raster C2 multi-piece contours preserve every disconnected piece, material island, hole and source-relative position in one native document and one STEP compound. Never bridge, back, join, delete or independently reposition pieces. Use one global uniform registration and the final ALL-piece Y extent of 50 mm; width/origin/thickness edits operate on the whole compound. All other families, strict raster recipes and analytic contours remain single-solid. Both fidelity legs, actual minimum radius and tool access cover every piece; aggregate area cannot excuse a defective small piece.

## Result interpretation

Only the independent checker interprets the explicit user/dev judge card. Missing acceptance information yields `UNVERIFIED`, not a fabricated default. PASS requires every required criterion to PASS and independent native round-trip/editability checks. A successful construction or nonempty STEP is not acceptance. Tool-center access is the declared geometric translation/contour check, not a generic CAM or physical guarantee. No live holdout/pilot evidence is produced by S1 implementation tests.
