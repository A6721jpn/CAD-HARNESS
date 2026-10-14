# C-S2 output and runtime contract

Output a single JSON object admitted by `design/cad-harness-verify-v4/schemas/s2-capability-plan.schema.json`:

- `schema`: `cad-harness.plan.v4c`; `profile`: `c-s2`; `family`: `step_direct_edit`.
- `asset_id`, `source_sha256`: the immutable reference-role STEP input.
- `selection`: exact prepared `face_id`, `signature`, `adjacent_face_ids`.
- `kernel_tolerance_mm`: explicit construction/selection numerical setting, never a user acceptance tolerance or permission to alter geometry silently.
- `operation.kind`: `offset` or `replace`; `operation.reconnect`: `extend_intersect_trim`.
- Offset: explicit signed `distance_mm`, positive along the original face's outward orientation. The actual OCCT per-face engine supports feasible planar and curved cases; arbitrary offsets are not guaranteed.
- Replace: `replacement_asset_id`, `replacement_source_sha256`, `replacement_selection`, and explicit positive `extension_limit_mm`. Both selected source and replacement supports must be planar. The immutable finite replacement patch must cover the whole resulting replacement face. Unsupported supports, insufficient coverage and infeasible bounded intersections are explicit failures.

No extra fields, Python, expressions, arbitrary paths, hidden fallback or recovered-history claims. No image/engraving/rebuild family is admitted by this profile.

Runtime uses only `target=plan`, `stage=initial|parse_repair|repair`, authenticated `inputs`, approved `selection` and real `observations`/`answer` where applicable. Request text is unchanged. Inputs contain source identity, measured facts, face adjacency and honest normal/coverage metadata, not checker targets or files. The generator cannot access raw STEP, private cards or library APIs.

The strict S2 judge card defines dimensions, thickness opposed sets/direction/domain, preservation regions, face-count targets and numerical uncertainty independently of the plan. No acceptance values are supplied by this skill. Missing values or unsupported certificates remain UNVERIFIED. A region occupancy-volume comparison is not a maximum surface-distance certificate. Numerical uncertainty never enlarges user tolerance.

Continuous thickness certificates require convex planar material throughout the entire declared ray-domain prism. Unrelated curved features outside that prism do not invalidate a supported local certificate. Other continuous domains remain UNVERIFIED; explicitly sampled criteria report sampled scope only, never global extrema. Acceptance is fixed independently of construction settings.

The native deliverable is one valid operative PartDesign Body/Tip plus STEP; new edit parameters must drive recompute after restoration. Independent worker verification checks both reopened representations against exact original input and the committed card. No source-file modification, silent selector remapping, automatic bridge/feature deletion or post-result acceptance changes are permitted.
