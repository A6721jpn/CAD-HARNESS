# C S1 data and runtime contracts

All new schema tags end in `.v4c` and carry `profile: "c-s1"`. JSON objects are closed to unknown fields; numbers must be finite; booleans are not numbers. Duplicate JSON keys are rejected by the existing ledger parser. All file writes are exclusive. There are no live model/provider calls, hidden acceptance defaults, scripts in plans, or native imports in host admission.

## Schema resources

`design/cad-harness-verify-v4/schemas/` contains `input-manifest.schema.json`, `prepared-inputs.schema.json`, `contour.schema.json`, `capability-plan.schema.json`, `judge-card.schema.json`, `judge-result.schema.json`, `capability-manifest.schema.json`, and precise supporting `step-facts`, `step-recipe`, `contour-recipe`, `contour-source`, and `text-outline` schemas. `capability-policy.json` is the zero-live implementation policy. The standalone plan schema embeds the unchanged build-spec schema; semantic admission still uses the existing `cad_spec.validate_spec`.

## Runtime envelope

The request remains verbatim text. For this profile, `runtime_data.target` is `plan`; stage is `initial`, `parse_repair`, or `repair`. `inputs` is exactly the authenticated model-input projection, including the verified font registry. Optional `selection` is a list of exact `{asset_id, face_id, signature}` entries, with unique, unambiguous original faces. Original-profile keys and observation semantics remain unchanged.

Plan-repair `observations` expose only measured numeric diagnostics, criterion IDs/statuses, numerical uncertainty, safe native error codes and candidate bounds/volume. Checker targets/acceptance thresholds, source paths, masks, recipes and cards are not sent to the generator. Parse repair may see its own invalid response and validation error. A caller cannot replace the authenticated facts or selection with fabricated runtime data.

Completed native geometry failures may consume the single repair slot. Transport/capture failure, missing dependencies, invalid ownership/cleanup evidence or implementation drift stop `INCOMPLETE`; they are not converted to model-repairable geometry failures. Partial streams and the failed work event remain on disk.

Request, input-manifest, prepared-packet and checker-card bytes are pinned before request admission and rechecked before each model/native phase and before accepting a candidate. Changing a card between repair stages invalidates the episode instead of silently replacing its criteria.

## Host APIs

`tools.cad_verify_v4_inputs`:

- `load_manifest(path) -> dict`: validates manifest and every asset, including byte length, SHA256, kind/role, file signature and font-license registry. Paths are relative to manifest parent, canonical slash-separated names. Absolute/drive-relative/ADS paths, traversal, symlinks/junctions/reparse points, special files, and lexical `pilot-user` / `v4-holdout-private` components are rejected before protected filesystem lookup. JSON contour/facts assets must satisfy their exact data schemas. A font has mandatory `glyphs` string and `license_asset_id`; the referenced UTF-8 license is registered with `kind: "license", role: "license"` and a `.txt` or extensionless name.
- `resolve_asset(manifest_path, asset_id, expected_kind=None) -> {record, path, digest}`: `record` is a detached manifest asset record; `path` is an absolute `Path`; `digest` is verified lowercase SHA256. Unknown IDs/missing assets never resolve to defaults.
- `verify_prepared(packet_or_path, manifest_path) -> dict`: strict prepared admission, all original asset digests, manifest digest, STEP before/after provenance, face atlas validity, and contour hash closure. Pure host code; native contour geometry checks are performed separately by the compiler/checker, not falsely claimed here.
- `model_inputs(packet, manifest_path=None) -> dict`: closed allowlist projection, deterministic sorted asset IDs. With a manifest, it re-admits original provenance and exports `fonts: {font_id: {font_sha256, glyphs, license_sha256}}` after verifying font and license bytes. Without one, `fonts` is empty, not invented. Output schema is `cad-harness.model-inputs.v4c`; no paths, recipes, checker masks, license contents, original files, judge cards, or private gold. STEP projection retains source units/axes, bounds, topology, face atlas, and validity/coverage; contour projection retains only geometry/units/topology/nominal width.
- `guarded_path(path, regular=True) -> Path`: lexical-private rejection and no-link/no-reparse confinement; reusable by trusted native consumers.

`tools.cad_verify_v4_plans`:

- `validate_profile(profile) -> "c-s1"`: no implicit selection or aliases.
- `validate_document(value, schema_name) -> dict`: host-only strict schema validation. Names: `inputs`, `prepared`, `step-facts`, `step-recipe`, `contour`, `contour-source`, `contour-recipe`, `text-outline`, `plan`, `judge-card`, `judge-result`, `capability`.
- `validate_plan(value, manifest_path=None, prepared=None) -> dict`: validates family-specific data, existing build-spec semantics, finite nonzero rotation axes, original reference/font IDs/roles and glyph registry when the manifest is supplied, and selected prepared contour when supplied. Engraving supports full axis-angle 3D placement; no silent horizontal-only restriction.
- `validate_judge_card(value) -> dict`: exact metric-specific fields, finite explicit tolerances and criterion IDs. Missing metric acceptance fields or linear tolerance remain missing for `UNVERIFIED`; base schema/profile/source/criteria are mandatory. Present null/nonfinite tolerances are rejected, never defaulted. No user values are inferred from pilot data.

## C1 native API

`inspect_step(manifest_path, asset_id, recipe, out) -> prepared_packet` runs only in a native interpreter with actual FreeCAD/Part. `recipe` is exactly `{schema: "cad-harness.step-recipe.v4c", profile: "c-s1", source_axes: ["X","Y","Z"], source_units: "mm"|"cm"|"m"|"inch", signature_precision_mm: positive}`. STEP length declarations must agree with the explicit source-unit attestation; unsupported/mixed units fail. `Part.Shape.read` imports actual geometry into millimeters. Null/invalid/faceless geometry fails.

The resulting facts contain `source_sha256`, `bounds_mm`, actual topology counts, separate `frame.source_units` and `import_units`, ordered face IDs, area/center/bounds, normals with validity, signature ambiguity, coverage, and input manifest/asset hashes before and after. No bbox-derived thickness: `thickness_mm` is null with a reason. Fingerprints SHA256 the canonical tuple of surface type, area quantized by precision squared, center/bounds quantized by precision, and unit normal rounded to 12 decimals. Identical fingerprints are explicitly ambiguous. Plane normals are constant; other sampled normals carry `local_surface_normal_not_global_face_normal`; unavailable normals are null. Before/after input changes fail, not produce stale successful evidence.

`out` may be a new directory, an already-allocated empty guarded directory, or an exclusive `.json` file. Directory output is `prepared.json`; the packet contains the inspected asset only. The worker/supervisor combines prepared assets explicitly. This helper does not write `result.json` or claim geometric acceptance.

## Contour provenance branches

Raster-derived `cad-harness.contour.v4c` contains exact line/arc loops, source mask row runs, source loops, explicit recipe, registered pixel transform, source/decoded/mask/recipe/record hashes, conservative approximation bounds, topology and processing provenance. Source manifest/image digests bind the original image, not a self-comparison.

Independent analytic input uses `cad-harness.contour-source.v4c` with explicit units, bounds, nominal width, exact loops, and `source_image_asset_id`. Its prepared contour branch binds `source_sha256` to that raw registered file, carries `source_image_asset_id` / `source_image_sha256`, exact geometric equality to the raw source, pixel registration, topology, and `provenance: {kind: "independent_analytic_source"}`. It never fabricates raster masks, extraction recipes, preprocessing reports, or source-loop observations. Native contour validation independently checks geometry in either branch.

## Judge card and result

Card source is `independent_dev` or `user`; criteria use explicit IDs and metric kinds `solid_valid`, `bounds`, `volume`, `image_iou`, `boundary_hausdorff`, `min_radius`, `tool_access`, `reference_gap`, `reference_clearance`, `reference_contact`, `translation_clearance`, `reference_play`, `unchanged_dimension`, `engraving`, or `native_roundtrip`. Exact per-metric parameters are in `judge-card.schema.json`. No checker card is generator context.

- Fidelity has two separately registered legs. Min-R and disk-center access remeasure the actual output section, not the prepared contour or a report; section Z is explicit or the declared extrusion's mid-thickness. Min-R uses a numerical interval, not an allowance that silently lowers the radius target.
- Image checking redecodes the bound original image with an explicit channel and foreground/alpha policy. Luminance is integer Rec.601 `(299R+587G+114B+500)//1000`. The checker independently hashes decoded RGBA and canonical row-run masks, requires the committed image/mask and pixel registration, and then measures fidelity. A different mask or convenient registration cannot silently become the baseline.
- `reference_gap` measures a declared parallel planar pair, signed gap/spread and projected overlap. `reference_clearance` checks the minimum distance over complete selected original faces, including curved faces; strict separation uses the lower numerical bound. `reference_contact` bounds the exact selected-face/common-solid contact area, not an invented inflated contact band.
- `translation_clearance` certifies overlap limits only over its declared interval; it is not maximum play. `reference_play` bounds the connected collision-free translation component about the registered datum, with explicit total/positive/negative convention, search interval, positional resolution, volume uncertainty and maximum. Actual interpenetrating samples provide stop barriers; only joined positive-clearance intervals prove a lower reachable bound. Missing stop evidence is UNVERIFIED, never a guessed endpoint. Neither metric proves rotations, friction, compliance or six-DOF fit.
- All acceptance and uncertainty quantities are explicit card data. Missing quantities remain UNVERIFIED. Native roundtrip requires explicit bounds/volume limits and an editable-document requirement.

Result tag is `cad-harness.judgement.v4c`, with `status` and `checks`. Each check has `{id, metric, status, measured, target, tolerance, uncertainty, evidence}`; status is PASS/FAIL/UNVERIFIED. Measurements/evidence are finite data-only JSON, not executable payloads. No missing target or uncertainty is converted to PASS.

## Capability implementation lock

`cad-harness.capability-manifest.v4c` binds code/resources, host and native dependency identities, recipes, optional independent-dev inputs, and the immutable original-profile snapshot. `stage: "implementation"`, `status: "offline_locked"`, `authorization: null`, and `final_v4_ready: false` are mandatory. It does not authorize live work. Original profile resources and observation semantics are intentionally unchanged.

Recipe registry IDs are canonical filename stems (without `.json`), not filenames containing dots. Recipe schema and duplicate IDs are checked before native identity work; only the S1 STEP and contour recipe schemas are admitted.

The implementation lock binds both phase generator identities and the Astra Max judge identity, its same-model-as-pilot caveat, and authoritative user-visual role. Judge and run authorization remain null. C-profile freeze rejects generator/launcher overrides; original-profile freeze rejects C-only asset arguments rather than silently omitting them.
