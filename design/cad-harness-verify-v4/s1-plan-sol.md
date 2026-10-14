# S1 implementation plan — sol

**Ready to start after non-numeric agreement; not started by this document.** Resolve the three concrete findings in `addendum-c-sign-sol.md`. C-Q remains a nonblocking parameter/authorization queue for offline development, not permission to invent trial defaults.

S1 delivers C1 STEP attachment + measured facts, C2 deterministic image-to-contour + parametric extrusion + min-R, C3 font engraving, and the corresponding deterministic judges. It must be end-to-end on independent dev inputs, not a set of schemas or mock echoes. It does **not** execute a pilot after S1: C-EXIT requires S2, S3, applicable fresh holdouts and final freeze before the complete U1–U5 pilot.

## 1. Fixed design decisions

- Keep `tools/eval_verify_v4.py` as the public facade. No separate competing evaluator or ad hoc pilot driver.
- Existing v3/v4 unchanged-scope contracts and the original holdout remain intact. Add an explicit capability profile; never let an old manifest select a new behavior implicitly.
- New S1 families emit a **typed plan**, not arbitrary file-reading construction source. Supported family discriminators: `reference_fixture` and `contour_extrude`; engraving is a declared operation on the constructed holder/part.
- Preserve the original request and genuine answers. Add an explicitly authorized `inputs` runtime field for authenticated initial facts/contours and `selection` for approved references/regions. `observations` remains actual previous output/parse errors/failed checks, never an initial-attachment loophole.
- Generated-source imports remain FreeCAD/Part/Sketcher/math, with file/network/shell/document-lifecycle/probe operations forbidden. Only trusted CLI workers read STEP, PNG or font bytes. No generated Draft import or unrestricted font path.
- Use the observed DPC-019 bundled Python 3.11 / FreeCAD 1.1.4 / OCCT 7.8.1 processing environment. Host Python 3.12 is the supervisor, not a substitute numeric/CAD environment. Pin actual dependency/font bytes and versions, not the stale versions in an R1 example.
- Implementers never open pilot attachments, their derived measurements, masks, contours or selections. All dev assets are independently authored. Only the custodian processes an actual pilot input after recipes are locked; its processing and outputs remain outside implementer-readable development evidence.
- No numeric trial gate from either draft is a default. Missing user acceptance values stay absent and block the applicable preparation/final freeze, while dev cards supply independently chosen test parameters.

## 2. Exact integration/file map

Names below are proposed files to create/change on agreement. No implementation file is changed by this plan.

### Existing modules to extend, preserving their existing-profile behavior

| File | Concrete change | Observable completion |
| --- | --- | --- |
| `tools/eval_verify_v4.py` | Add profile-aware dispatch for `prepare-step`, `image-to-contour`, `text-outline`, `compile-plan` and `judge`; extend the existing `preflight`/`request`/`freeze`/`run` path rather than bypass it. New commands take manifests/asset IDs, not unbound ambient paths. | Offline S1 request reaches compilation, actual native verification and evidence summary from one facade. Old recorded requests/backfill/aggregate paths continue to work. |
| `tools/cad_verify_v4_agent.py` | Make bundle/protocol selection explicit by capability profile. Validate new `inputs`/`selection` structures and `target=plan` only for the C profile. Retain the existing four-key protocol for unchanged profiles. | Unknown keys, wrong profile and factual provenance mismatch fail; a permitted fact packet reaches the S1 model envelope without rewriting the request or exposing checker gold. |
| `tools/cad_verify_v4_freeze.py` | Bind profile-specific code/skill/schema/dependency/recipe/font/judge/input commitments and final user cards. Make generator identity phase-specific: unchanged holdout Sol/xhigh, pilot Astra/max per DECISIONS.md. Preserve manifest-only live authorization and exclusive single-use claims. | Wrong model/profile, missing card, changed image/mask/contour/font/STEP or a mutable dependency prevents live admission. Existing manifests are not rewritten. |
| `tools/cad_verify_v4_live.py` | Add the typed-plan route and explicit trusted-worker invocation kind, bounded by the frozen profile. Preserve quota checks, identical-resend bytes, provider-unavailability clock exclusion, P/R limits, raw capture and incomplete accounting. | A mocked model response drives the real deterministic S1 path on dev inputs; there is no alternate CLI flag/environment path that authorizes a live trial. |
| `tools/cad_verify_v4_ledger.py` | Record STEP preparation, mask/trace, font outline, compile and judge work as linked deterministic operations, with all input/output hashes, times and failure reasons. Keep physical model attempts/charges separate. | All preparatory/native work is visible without fabricated provider-token events; nulls remain null. Model-judge invocations, if authorized later, are real charged attempts. |
| `tools/cad_verify_v4_pilot.py` | Reuse its read-only inventory/confinement and immutable-bundle verification. Add/reference the new prepared-asset records; do not force directly supplied user requests through a nonexistent historical JSONL. Do not turn this bundle function into an eligibility or quality oracle. | Bundle integrity establishes bytes/provenance, not contact/fidelity success. Direct intake and historical extraction remain distinguishable. |

**Original freeze safety:** the current freeze hashes a broad tool set. Adding/changing tools must not silently invalidate/replace the original trial identity. Keep the original executable snapshot/manifest independently verifiable; introduce the new profile and binding set in a new implementation/final execution commitment. No copying results from a changed program under the old manifest, and no rewriting the old commitment to make verification pass.

### New deterministic modules

| File | Responsibility / interface boundary |
| --- | --- |
| `tools/cad_verify_v4_inputs.py` | `prepare_step(input_manifest, asset_id, recipe, out)` and prepared-packet verification. Resolve opaque assets, import only in the native worker, extract units/source axes/placements/topology/face atlas and measured facts with uncertainty. Retain the original shape hash, and mark ambiguous selections/coverage explicitly. |
| `tools/cad_verify_v4_contours.py` | `prepare_contour(...)`, canonical-loop validation, pixel-to-physical transform and independent min-R/fidelity evidence. Separate original mask, traced loops and any approved processed loops. No image-dependent policy search. |
| `tools/cad_verify_v4_text.py` | Registered-font verification, glyph outlines/layout and engraving geometry input. Resolve a font ID to hash-bound bytes; record glyph coverage and license. No font fallback, arbitrary paths or substituted text. |
| `tools/cad_verify_v4_plans.py` | Pure-data validation of S1 plans, references, units, permitted operations, parameter sources, dependency graph and output requirements. Reject paths, executable expressions, cyclic references and unsupported operations before invoking CAD. Importable/testable in host Python without loading native/numeric libraries. |
| `tools/cad_verify_v4_compile.py` | Trusted compilation of validated plans into the existing stock/rib/pocket operations, new contour extrusion and engraving. Require operative size/thickness/placement/depth parameters, not detached properties. No judge/gold logic in generated construction. |
| `tools/cad_verify_v4_worker.py` | Owned headless execution/verification entry point in the pinned bundled environment. Import immutable references only in authorized roles; create candidate documents, compile, close, export and independently reimport under the existing cleanup/PID guarantees. Keep reference bodies out of the single-part deliverable. |
| `tools/cad_verify_v4_judges.py` | S1 solid validity, original/reference contact and declared-dimension comparison, image/contour fidelity, tool-radius/accessibility and engraving evidence. Emit measured values/bounds plus PASS/FAIL/UNVERIFIED; never let a missing numeric card or sampling gap produce PASS. |

Numerical/native imports stay inside the workers/functions requiring them. No attempt to import the bundled Python 3.11 extensions into the host Python 3.12 interpreter. Reuse existing ownership/cleanup, guard, stream and journal helpers; do not fork or relax them.

## 3. Concrete contract/schema resources

Create the following versioned, strict-schema resources under `design/cad-harness-verify-v4/schemas/`:

- `capability-manifest.schema.json`: profile/families, exact module and runtime identities, phase/generator/judge identities, limits, recipe/font/judge/user-card commitments and custody. S1 offline readiness is not final v4 live readiness.
- `input-manifest.schema.json`: asset IDs, type, original SHA/size, permitted role, units/coordinate source and immutable bundle mapping. CLI-side paths never become generator authority.
- `prepared-inputs.schema.json`: measurement method/version, source SHA, source axes and transform, bound/uncertainty/coverage fields, unique face/region atlas IDs and derived contour/font IDs.
- `contour.schema.json`: original image/mask/recipe identities; closed oriented loop hierarchy; line/arc/curve representation; topology/component mapping; pixel and physical frames; size/scale definition; approximation bounds and min-R report references. A bare polygon plus an asserted `min_radius` is not sufficient evidence.
- `capability-plan.schema.json`: discriminated S1 family, authenticated input/selection IDs, geometry/placement parameters, optional engraving operations, preservation/contact constraints and output requirements. No raw filenames, Python snippets or arbitrary expressions.
- `judge-card.schema.json` and `judge-result.schema.json`: criterion/ROI, target and authoritative source, units, user tolerance, numerical uncertainty and coverage, method identity, evidence hashes and verdict. No populated fake default tolerance.

Create `design/cad-harness-verify-v4/capability-policy.json` with the approved C profile, zero live authorization during development, accepted dependency registry/recipes, question references and pending final-freeze conditions. Keep the original policy and old contracts byte-preserved for their existing profile.

Create `skills/cad-harness-v4/c-s1.md` and `skills/cad-harness-v4/contracts-c-s1.md`: the new factual-input/typed-plan protocol, permitted S1 families, intent/selection/clarification rules, parameter provenance and diagnostic interpretation. Bundle them explicitly for the C profile; do not inject them into the original holdout bundle. Modeling prose and source I/O restrictions remain unchanged.

Proposed bundled font resources: `skills/cad-harness-v4/fonts/DejaVuSansMono.ttf` and `fonts/LICENSE_DEJAVU`, copied later from the independently inspected installed asset and pinned by the registry. This is a proposed agreed library choice, not an already executed copy or universal Unicode guarantee. Unsupported glyph/shaping requirements fail clearly.

## 4. C1 execution and evidence

1. Worker validates input byte identity and STEP units/coordinate mapping before construction. Record import warnings, original topology and coverage; never silently heal the truth reference.
2. Facts distinguish axis-aligned bounds, principal directions, actual thickness and local geometry. Do not swap source Y for an inferred principal axis, infer glass thickness from a Z span or infer clearance from overall bounds.
3. Face IDs bind the source digest plus geometric/adjacency signatures. Reordered entities should not select the wrong face; symmetric/duplicate signatures must become explicit ambiguity, not an arbitrary tie-break presented as intent.
4. Model receives only the permitted fact/selection packet and chooses an S1 plan. The CLI can resolve exact references during construction/evaluation; generated code cannot read them.
5. Construct the single intended output part. Reference placements are checking context, not an exported assembly. S1 does not silently acquire S2 freeform offset/healing just to make a holder conform to a reference.
6. Check declared contact/protected regions and registered motion/dimension criteria against exact source geometry, with uncertainty recorded. Simple declared rigid translations are not a six-DOF/friction/material retention certificate. An unsupported physical claim is unassessable, not a bbox-fit pass.

Completion requires actual independent-fixture input → facts → plan → native output → reimport/measure evidence, including wrong-frame, same-bbox/different-geometry and protected-contact negatives. A copied attachment and successful hash check alone do not complete C1.

## 5. C2 execution and evidence

1. Registered policy fixes decoding/foreground/alpha/connectivity and coordinate conventions on independent dev fixtures. The production recipe cannot pick a different threshold or smoothing strength after viewing a pilot result.
2. Trace closed loops and retain nesting, winding, components and critical features. Smoothing/curve approximation has a declared error bound and must not silently delete, bridge, fill or reshape components. Ambiguous input/policy produces a recorded error/clarification, not a guessed contour.
3. Establish physical scale from the approved card before interpreting a radius in millimetres. Do not report physical min-R from normalized pixels without the transform.
4. Compile `contour_extrude` with operative thickness and size. Native recompute/export must preserve the parameter effects. A static Shape with inert custom numbers is not parametric behavior.
5. Independently judge original mask → canonical contour and canonical contour → constructed output. Commit raw image/mask, recipe, transforms, intermediate/final contours and all reports; original pixels remain checker-only.
6. Test continuous curve curvature and nonsmooth concave corners **and** planar tool-center accessibility/narrow channels. A Shapely buffer or vertex-only radius field is not a proof. Straight segments and convex outside corners must not be misclassified as inaccessible concave features.
7. Re-evaluate physical constraints when size changes: scaling a previously valid outline down may invalidate min-R. Do not retain a stale preparation report or silently widen the logo outline to hide the violation.

Missing user scale/fidelity/component decisions remain C-Q. The custodian's actual pilot preprocessing runs only after the required values/recipe are fixed, once for that attempt. No implementer runs the CLI on a pilot PNG to find convenient parameters. A failed preparation is retained, not tuned and repeated in-place.

## 6. C3 execution and evidence

1. Font resolution is registry-only: SHA, version/metadata, glyph coverage and license; never an ambient Windows font lookup or missing-glyph fallback.
2. Plan supplies actual text, support selection, frame, alignment and approved geometric parameters. CLI creates the glyph contours and recessed operation. User request text remains unchanged.
3. Preserve counters/holes, actual material removal, depth direction and remaining material. Raised text, painted labels, object names or metadata are not engraving.
4. Verify text/size/depth/placement parameters actually control geometry through normal recompute and independent reimport. If a trusted parametric feature is required, freeze its implementation/dependencies and data-only persistence; do not imply portability without them or accept an inert one-shot solid.
5. Native/measured evidence handles geometric properties; Astra/user assess semantic correspondence/readability under the agreed rubric. No numeric glyph/depth/readability range from an R1 example is adopted.

## 7. S1 judges and exact obligations

| Judge | Required implementation | Must reject / mark unverified |
| --- | --- | --- |
| Solid/native/reimport | OCCT/FreeCAD validity, intended solid/Body/Tip/native recompute, independent FCStd and STEP evidence, unchanged original inputs and owned cleanup | No-exception-only success, missing required native features, wrong part count, invalid or unclosed output, missing export/reimport evidence |
| Reference/dimension/contact | Registered source-frame geometry/ROI, correct installed pose and preserved-dimension mapping; region-specific contact/separation and explicitly defined play measurements | Bbox-only physical-fit claims, arbitrary alignment hiding movement, wrong opposing face, ambiguous selection, undefined motion/contact policy or uncertainty exceeding the decision margin |
| Image IoU | Frozen original mask and model silhouette in the same registered frame/scale, including components/holes; exact rasterization/coverage convention | Self-comparison only to an already modified contour, score-optimizing alignment, unregistered thresholds or area agreement concealing topology loss |
| Boundary distance | Symmetric image/contour/output boundary distance with physical transform, approximation/coverage bounds and method identity | One-sided/minimum distance mislabeled Hausdorff; sampled maximum claimed as exact continuous maximum without a justified bound |
| Min-R/accessibility | Independent continuous-boundary radius and declared planar tool-center feasibility, current size transform and allowed contour-change policy | Blind trust in `contour.json` metadata, a buffer operation called a certificate, inaccessible narrow channels, unapproved contour edits, invalidation after scale change |
| Engraving / unchanged dimensions | Actual recess, glyph counters, remaining wall, native parameter effects and explicit preserved-region comparisons | Raised/painted labels, through-cuts contrary to intent, filled counters, changed surrounding geometry or inert editable-looking metadata |

Numerical upper/lower bounds and uncertainty must be separate from the user acceptance limit. If a required bound cannot be resolved within frozen resources, result is UNVERIFIED/non-success, not a widened tolerance. This implementation must demonstrate the claimed bound/method on dev data before final freeze; naming an algorithm is not completion.

All missing acceptance values are on C-Q4–Q8. New-family counts/gates/reservations and any actual model judging are C-Q9; resource amendments, if needed, are C-Q10. None requires a hard-coded placeholder or stops generic offline implementation.

## 8. Concrete tests and independent fixture handoff

Create **two cohesive suites**, avoiding one test file per forwarding function:

### `tools/test_verify_v4_s1.py` — host-side schemas/protocol/security/accounting, no live/native launches

- Input/capability profile mismatch, altered image/mask/contour/STEP/font/recipe/card, unresolved or escaping asset paths and changed coordinate provenance prevent execution.
- Old profiles reject the new fields; C-profile initial facts enter only through the declared field. `observations` cannot be a semantic substitute for attachment input. The actual new envelope exposes no gold, future input, original raw asset path or hidden source.
- Typed plans reject unsupported operations, executable expressions, ambiguous/cyclic selectors and invalid units/scales before worker launch. Missing critical numeric cards prevent final freeze, not dev-mode operation with explicit independent fixture cards.
- Default policy never authorizes live work. Frozen phase-specific model identities cannot be replaced by ambient model roles or CLI flags. A pilot-profile manifest binds Astra/max explicitly; original holdout identity stays unchanged.
- Worker/stream failure preserves partial evidence; deterministic preparation events do not become fake model charges/tokens. Existing overload/slot/quota tests cover the extended envelope, including byte-identical resend and no hidden model/judge call.
- Final v4 live preflight cannot treat an S1-only completion flag as S1–S3 completion, omit a user task, pool best results across manifests or substitute a historical exposed holdout for fresh validation.

These tests target admission, isolation and false-pass bugs, not source strings, file copies, forwarding echoes or documentation wording.

### `tools/test_verify_v4_s1_native.py` — actual independent dev geometry under the bundled environment

- **C1:** independent unit/pose/reference fixtures, duplicate/split/reordered faces, same bounds with different local contact geometry, thin/curved references, open/corrupt shapes and reference bytes unchanged. Verify real prepared facts and wrong-face/pose failures.
- **C2:** independently authored analytic masks/curves covering concavity, nested counters, alpha/polarity, narrow features and ambiguous components. Compare against separately calculated truth. Detect a local silhouette change hidden by high area overlap; wrong scale/origin; topology lost by smoothing; valid/invalid min-R and channel access; stale min-R after size change.
- **C3:** independently chosen text/font fixtures with counters, transformed placement, supported/missing glyphs, wrong cut sign, through-wall failure and actual depth/size effects. Verify normal native recompute and FCStd/STEP behavior, not merely values of properties.
- **Judges:** independently reviewed positive, decisive-negative and boundary/uncertainty cases. Include analytic distance/radius cases and a local deviation missed by coarse samples. Do not derive expected values by running the same compiler or approximation as its own oracle.
- **End-to-end:** fake model plan → real trusted S1 processing/native worker → independent judge/export/reimport → ledger summary. Separately exercise actual S1 facade commands on dev data. Label injected-model evidence as development/mock, never fresh holdout/pilot success.

Independent fixture sources and expected contracts live under **`design/cad-harness-verify-v4/dev-c-s1/`** with `manifest.json`, `inputs/`, `controls/` and `expected/`. An appointed independent fixture author supplies/reviews the concrete asset values and analytic/native oracles. Implementers may use these dev assets only; fixtures must not be authored by measuring a pilot or by making a scalar mutation of one. A source script and an expected output from the same unreviewed generator are not independent controls.

Run the pure-data suite with host Python. Run the numeric/native suite and smoke with the pinned bundled Python/FreeCAD headless runtime, not an accidental host interpreter lacking NumPy/Part. Existing mocked `test_verify_v3`, `test_verify_v4`, `test_verify_v4_freeze`, `test_verify_v4_pilot` and `test_verify_v4_live` remain required regressions. A module import probe or mocked success response is not native smoke proof.

No test or dev fixture is created/run by this planning document.

## 9. Execution sequence on agreement

1. Establish the C-profile schemas, instruction bundle, immutable asset/recipe/font registry and separate native-worker boundary. Preserve the original implementation snapshot and confirm existing regression behavior.
2. Implement C1 preparation and data transport, then C2 contour/compile/judge integration and C3 engraving, using only independent dev fixtures. Implement evidence/metric behavior alongside each feature, not as an optional final layer.
3. Exercise pure-data failure boundaries and actual dev geometry end-to-end; review compiler/parameter effects, fidelity/radius/contact evidence, uncertainty and independent oracles. No live model smoke is needed or authorized.
4. Obtain S1 implementation review, record its lock and dependency/recipe identities, and continue S2/S3. **Do not author fresh evaluation material against changing code or run an early S1 pilot.** Final integrated code/skill/judges are locked before fresh family authoring/control validation; final execution freeze binds all approved inputs/cards/budgets afterward.
5. At the final v4 point only, the separately appointed custodian prepares actual pilot inputs once with the dev-locked recipe, without implementer access or tuning. Run applicable fresh holdouts and the complete U1–U5 pilot in the C-EXIT order under the final manifest. A failed cycle preserves all evidence and requires new authorization/fresh affected-family validation and a complete new pilot cycle, not selected task retakes or pooled successes.

The S1 review can complete while C-Q is open, but no relevant final preparation or freeze may substitute values. One final v4 result still requires all five user tasks and existing exit gates; S1 implementation alone is not a narrowed completion claim.

## 10. Handoff acceptance

S1 is ready for its review only when the planned features and required judges work on actual independent dev fixtures; normal parameter changes drive geometry; forbidden data/import paths fail closed; original inputs remain immutable; native/export/reimport and owned cleanup evidence exists; all affected contracts/callers and tests agree; and missing-user values remain explicit final-freeze blockers rather than chosen defaults.

Unknowns include final physical/fidelity tolerances, some geometric play/contact decision conventions, final numeric resource allowances, family counts/pass gates/budgets and Astra-judging reservations. They are not implementation stubs: the implementation takes explicit cards, rejects unsupported/unknown live conditions and reports uncertainty honestly. Installed library presence is not evidence that the full S1 feature works. Actual feature smoke, not invented performance or quota percentages, determines implementation readiness.

Status: **plan only**, ready to execute after non-numeric consensus. No pilot attachments/private holdout opened, no implementation change, no live call and no commit by this document.

Signed: **sol** (`openai-codex/gpt-6.1-sol`).
