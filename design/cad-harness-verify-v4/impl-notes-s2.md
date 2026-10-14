# S2 implementation notes — sol

**S2 is implemented and verified for offline review under the separate `c-s2` profile.** This is not final v4 readiness, live authorization, pilot adoption, or a holdout result. S3 was not started.

## Boundaries and preservation

- Used independently authored synthetic development fixtures only. No `pilot-user/` file, private holdout, or attachment-derived pilot geometry was opened or used.
- Made zero live harness generator/judge calls. Replay responses are explicitly mocked; local FreeCAD geometry operations and independent reopening actually ran.
- Ran no pilot/holdout and authored no fresh holdout cohort. Made no commit.
- Installed or changed no runtime packages. Original 163-call allocation/custody, original-profile behavior, existing active limits and shared P1/R1/CAD-attempt limits remain unchanged.
- Preserved the observed pre-S2 S1 bound source set before editing shared files: `s1-profile-snapshot.zip`, 98 files, 935955 bytes, SHA256 `f1f0276822bea29e1da951a449b2ff5203c989e7a204cc1e721f0de0124bb816`. Its extracted original `c-s1` executable completed preflight; the owned temporary extraction was removed. The relay reports S1 commit `3e975c2`; this archive is an observed source snapshot, not an independently checked Git-commit equivalence claim. ZIP timestamps are canonical serialization metadata.
- The earlier `original-profile-snapshot.zip` remains unchanged, SHA256 `763fb69bdef88cb3ba62c7fb646ebcc3bd16e80585356bd732eefeddf506447d`. Old manifests/results were not rewritten. Running old frozen stages requires their matching original implementation, not changed root code under old hashes.

## Files and CLI/skill split

| Area | Files / responsibility |
| --- | --- |
| C4 native editor | `tools/cad_verify_v4_s2_edit.py`: host-safe plan admission, immutable source/selection verification, actual OCCT edit/reconnect, frozen native proxy and operation history. |
| Independent C6 judges | `tools/cad_verify_v4_s2_judges.py`: reload original STEP independently; actual candidate solid, face count, dimensions, preservation, thickness and native roundtrip. No editor/compiler imports as an oracle. |
| Stage contracts | `tools/cad_verify_v4_s2_contracts.py`; eight `schemas/s2-*.schema.json` files for inputs, prepared data, STEP facts/recipe, plan, judge card/result and capability manifest. |
| Policy and skill | `policy-c-s2.json`, `skills/cad-harness-v4/c-s2.md`, `contracts-c-s2.md`. Offline-only, one-solid direct-edit family; no S3 or generated-source I/O expansion. |
| Shared facade/infrastructure | Existing `eval_verify_v4.py`, `cad_verify_v4_s1.py`, `cad_verify_v4_inputs.py`, `cad_verify_v4_plans.py`, `cad_verify_v4_agent.py`, `cad_verify_v4_worker.py`, `cad_verify_v4_compile.py`, `cad_verify_v4_freeze.py`, `cad_verify_v4_pilot.py`. Explicit stage dispatch reuses the existing supervisor, accounting, replay and lock path rather than creating a competing runner. |
| Independent dev controls | `dev-c-s2/generate.py`; host `test_verify_v4_s2.py`; native `test_verify_v4_s2_edit_native.py` and `test_verify_v4_s2_judges_native.py` under `tools/`. |

The CLI owns import, identity, topology, geometry, recompute and measurement. The skill chooses intended faces, edit side/amount/replacement, preservation intent and explicit registered conventions; it cannot read attachments, execute code, guess missing user tolerances or override an unresolved check.

Supported facade paths: `preflight`, `prepare-step`, `merge-prepared`, `compile-plan`, `judge`, recorded `request`, development `run`, `prepared-bundle`, and implementation-only `freeze`, with explicit `--profile c-s2`. Image/text operations remain in their existing profile. Live holdout/pilot and authorization-bearing freeze requests are rejected for `c-s2`.

## C4 actual edit contract

`step_direct_edit` plans bind original asset ID/SHA256 and a unique face signature, face ID and complete shared-edge adjacency. S2 preparation includes actual adjacency and signature precision. Selection is revalidated against the original geometry; no `FaceN`-only or nearest-face fallback is used. Input file bytes, units and original X/Y/Z are preserved.

- **Offset:** actual `BRepOffset_MakeOffset.SetOffsetOnFace`, with signed outward distance and intersection-based extension/trimming/reconnection. Development proves planar, oblique, cylindrical and cubic B-spline swept cases, including both offset signs. Arbitrary offset feasibility is not guaranteed.
- **Replace:** a separately hash-bound finite STEP face supplies a planar support. The selected original support must also be planar. The editor extends within the declared bound, intersects with an unrestricted analytic-plane halfspace, and checks that the immutable finite replacement patch covers the entire resulting replacement face. Tilted replacement is exercised; insufficient coverage, unsupported curved replacement supports and infeasible reconnection are explicit errors.
- **Provenance:** actual OCCT offset history and chained Boolean `Modified`/`Generated` history are recorded separately from geometric coincidence. Unknown/deleted lineage is explicit; displaced geometry is not attributed by nearest-face guessing.
- **Native editability:** a trusted, data-only `DirectEditProxy` persists embedded original/replacement BREP, hashes, facts and plan. `OffsetDistance` or `ReplacementShift` drives real recompute after reopening. Failed edits clear Shape/status rather than retaining a stale valid result. This is new operative edit history, not recovered original STEP feature history.
- **Output:** one valid solid with complete closed boundary shells in one operative Body/Tip, plus STEP. Original reference/support geometry is embedded as data, not exported as extra solids. Native portability requires the frozen extension; no extension-free recovered-history claim is made.

## C6 measurement semantics

Cards are stage-specific and separate acceptance tolerances from numerical uncertainty. Missing required values are rejected; unavailable certificates remain UNVERIFIED, never PASS. Numerical error is propagated and reported rather than silently added to user tolerance.

- **Thickness distribution:** explicit opposed original surface sets, fixed output regions, direction, domain, material-chord convention and coverage. Missing/multiple hits and wrong opposing sets are not thickness. Continuous certificates require convex planar material throughout the complete declared ray-domain prism, with complete opposing coverage; unrelated curved features outside the prism are clipped away. Unsupported continuous domains keep sampled observations and null global extrema. A fixed directed material chord is not automatically a surface-normal or nearest-wall convention.
- **Unchanged dimensions:** source-relative axis extents or registered landmarks in the original fixed frame. No alignment optimization hides movement. S2 axis extents and whole-body measurements use `optimalBoundingBox(False, False)` on trimmed geometry; legacy S1 measurement defaults remain unchanged. Per-face atlas bounds retain their conservative native signature convention.
- **Preserved regions:** two-way material symmetric-volume change inside a fixed ROI, including lost/added material and numerical bounds. Equal overall bbox/volume does not establish preservation. This metric is not a maximum surface-distance certificate; it cannot replace such a requirement.
- **Face counts:** actual full or positive-area-clipped regional BREP counts against an explicit expected count/delta and fixed spatial correspondence. Fewer faces are not automatically better.
- **Solid/native roundtrip:** actual validity/single-solid checks, operative native restoration, and separate FCStd/STEP reopening. Compilation and verification use different owned headless processes, closed stdin, complete raw streams, PID/window evidence and cleanup checks.

Only reference-role STEP facts enter the S2 generator packet/approved selection. Checker-only facts and paths/cards are not exposed. Original-profile observations remain unchanged. S2 repair observations expose actual measurements/safe status, not private acceptance values or ROI/card data.

## Verification actually run

Working directory: `C:/dev/CAD-HARNESS-herdr`.

```text
python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration tools.test_verify_v4_s2
```

Native command, with `CAD_VERIFY_S1_NATIVE=1` and `CAD_VERIFY_S2_NATIVE=1` in its environment:

```text
C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe -B -m unittest tools.test_verify_v4_s1_native tools.test_verify_v4_s2_edit_native tools.test_verify_v4_s2_judges_native -v
```

| Final suite | Run | Passed | Skipped | Unittest elapsed |
| --- | ---: | ---: | ---: | ---: |
| Host, including all original 92 regression tests | 127 | 126 | 1 | 7.445 s |
| Pinned native-runtime suite, including existing 22 S1 native tests | 59 | 59 | 0 | 38.650 s |

The one skip is the existing Windows test-symlink creation case; reparse rejection controls remain exercised. The native-runtime suite includes host-safe admission controls as well as actual kernel, operative-document, supervised-process and independent STEP checks. No CAD process runs during ordinary host discovery.

Coverage includes signed curved offsets, genuinely tilted replacement, finite-patch and extension negatives, stale/ambiguous/reordered selections, immutable source/dependency checks, oblique coordinates, B-spline normal-offset points, local decoy feature movement with equal global bbox/volume, cavities/multiple ray hits, unsupported continuous domains, missing numerical acceptance, actual native parameter edits, and complete supervised native/reimport handovers.

## Actual CLI/native smoke evidence

Evidence root: **`reports/verify-v4-s2-dev-20261014T085548Z/`**. Current development inputs are **`inputs-v4/`**. Earlier input/output revisions and failed/UNVERIFIED development attempts are retained, not overwritten or relabelled as successes.

| Exercised surface | Current evidence |
| --- | --- |
| Source/replacement/smooth STEP preparation | `prepare-source-complete/`, `prepare-replacement-complete/`, `prepare-smooth-complete/` — PASS |
| Verified packet merge | `prepared-complete.json`; `merge-prepared-complete.command.json` |
| Signed planar edit | `offset-complete/summary.json` — PASS |
| Tilted finite-support replacement | `replacement-complete/summary.json` — PASS |
| Curved B-spline edit | `smooth-complete/summary.json` — PASS |
| Standalone independent verification | `judge-complete/summary.json` — PASS |
| Parse repair plus CAD repair replay | `request-complete/summary.json` — PASS, explicitly mocked |
| Development batch | `batch-run-complete/summary.json` — PASS, zero physical model attempts/live calls |
| Direct prepared intake | `bundle-complete/bundle.json` — integrity only, not eligibility or a pilot result |
| Original profile / archived S1 | `gate-smoke.json`, `s1-snapshot-preflight.json` — original and archived-S1 preflight succeeded |
| Live admission denials | `gate-smoke.json` — holdout and authorization-bearing freeze rejected before nonexistent authority files were opened |

All three final edited models are valid single solids; both independent FCStd and STEP judges PASS, with operative native restoration:

| Dev edit | Volume (mm³) | Maximum native/reimport bounds delta (mm) | Volume delta (mm³) |
| --- | ---: | ---: | ---: |
| Planar face offset | 1721.716814692821 | 0 | 0 |
| Tilted replacement | 1916.1168146928223 | 4.973799150320701e-14 | 1.8189894035458565e-12 |
| Cubic B-spline roof offset | 1783.1669628642242 | 4.126682995320152e-9 | 2.1056621335446835e-8 |

The planar card certifies 8 mm thickness over its entire declared rectangle. The curved card explicitly checks sampled scope only: its global minimum/maximum remain null. Independent source-polynomial/local-normal controls also check the reimported curved skin. These are synthetic dev values, not user tolerances or pilot requirements.

The final request replay uses malformed JSON, then an incorrect signed offset, then a correct R1. Real CAD verification catches the wrong geometry. It records **3 replay responses, 2 CAD attempts, 4 deterministic operations (3 PASS, 1 FAIL), 8/8 complete raw stream captures, 5.75199999997858 s deterministic work, and zero physical model attempts/live calls**. Existing episode/initial/repair limits remain 900/450/450 s with the original shared parse/repair slots and CAD2 limit. A repaired dev PASS is **not** a pilot first-handover PASS or model-quality result.

## Defects found and corrected during development

- **Serialized signed zero:** cylindrical BREP text changed a tiny midpoint-normal component's sign; quantization produced `+0.0` versus `-0.0` hashes. S2 alone now hashes numeric zero canonically. Physical normals and S1 signatures are unchanged; no acceptance tolerance was loosened.
- **Finite halfspace semantics:** using a finite trimmed replacement face could leave a floating/partial patch. Replacement now uses its unrestricted analytic support, then validates whole-face coverage against the original finite asset. Closed-shell checks and the undersized-patch negative remain.
- **Area construction bounds:** dimensionally inconsistent tolerance × area checks were replaced by construction-only mm² bounds using perimeter × tolerance, vertex disks and roundoff. These are not user acceptance values.
- **Empty Boolean results:** non-null empty compounds carried void `DBL_MAX` bbox sentinels into numerical error calculation. Geometrically empty results are excluded; invalid bounds on nonempty geometry still fail.
- **Local continuous coverage:** opposed patches are clipped to the complete declared prism before coverage analysis; remote holes/curves no longer falsely invalidate an otherwise certified local domain. Interior cavities still prevent a global certificate or produce decisive sampled failures.
- **Windows wire encoding:** actual supervised runs exposed a CP932 UnicodeEncodeError on valid report units. Worker JSON stdout is now explicitly UTF-8, not dependent on console locale. The actual supervised regression covers the complete compile/reimport path.
- **Trimmed geometry versus support bounds:** actual curved handover exposed default bbox spans from extended spline supports. Optimal non-triangulated bounds now measure S2 trimmed geometry. An independently authored oversized-support/trimmed-solid control and real curved CLI/reimport regression retain this behavior; S1 defaults are unchanged.
- Fixture source preparation now uses fresh output directories. Incidental generic coverage-key/API-method-name assertions were removed rather than repinned; behavior, uncertainty and geometry controls remain.

The initial synthetic numerical cards were also corrected before the current review lock: their roundtrip volume bound and ROI numerical budget did not cover the declared construction uncertainty. The dev generator documents independent source/envelope-area bounds; current **dev-only** roundtrip volume acceptance is 0.01 mm³ and ROI numerical uncertainty is 0.0003 mm³. ROI acceptance remains 0.001 mm³, analytic geometry truth is unchanged, and no user card or judge was weakened. These values are not adopted for U4 or any other user request.

## Verified implementation lock

Current review lock: **`implementation-lock/manifest.json`**, adjacent `SHA256.json`, under the evidence root. Verification receipt: **`implementation-lock-verification.json`**, with full raw stdout/stderr.

- Status: `verified_offline_implementation_lock`; schema `cad-harness.capability-manifest.v4c`; profile `c-s2`.
- Manifest SHA256: **`74c818b6b40409f5a707b541b53b374255f4f37544a0d5c44e6e6c23c20de10b`**.
- Rechecked **117 bound source/policy/skill/schema/control-generator files** and **5028 native-runtime files**, host identity, recipes/dev commitments and prior-stage archive identity.
- C-S2 skill SHA256: `4332a59f49cad4920ca91bc246ac613427d9e8c073b898ea0111a188502b6cc6`.
- C-S2 policy SHA256: `3f07a0f7480fae2cc5bf4b08beca9e7db90e0b3e9225a29b3097d7c906af64fd`.
- **Authorization null; final_v4_ready false.** No CLI/environment flag converts this review lock into trial authorization.
- Separate forged copies with correctly rebound checksum files were rejected for non-null authorization (`s2.capability.authorization:type`) and altered code bindings (`s1_implementation_file_binding_mismatch`). The original lock was not edited and no live command was invoked.

Pinned native runtime remains FreeCAD 1.1.4 / Python 3.11.14 / OCCT 7.8.1 with installed pythonocc 7.8.1.1. Future generator identities recorded in the manifest remain holdout **`openai-codex/gpt-6.1-sol` / xhigh**, pilot **`openai-codex/gpt-6-astra` / max**; judge **Astra / max**, authorization null. The pilot generator/judge coincidence is explicit and user visual judgment remains authoritative. No such model was called here.

## Remaining final-v4 gates and limits

- S1/S2 external review findings, including the pending relayed S1 review, still require disposition. Do not treat an unavailable review as READY. Further implementation changes require a new review lock; S3 is still outstanding.
- Before final freeze, obtain the applicable U4 thickness/dimension tolerances, measurement convention, opposed/target/preserved selections and numerical-uncertainty rules through the approved user/custodian process. Do not inherit the dev values above, substitute bbox span for wall thickness, or treat directed-chord sampling as a certified normal-wall result.
- Replacement currently supports planar source/replacement supports; arbitrary curved replacement, arbitrary healing/reconnection, recovered design history and extension-free portability are not guaranteed. Curved offsets are real but can be infeasible. Unsupported operations/certificates remain explicit non-successes, not reasons to drop a sealed case or reduce the user goal.
- Preserve C-R2: integrated S1–S3 code/skill/recipe/judge lock before independent family authoring, then custody/cards/cohorts/all-five input commitments and separately authorized counts/gates/call/model-judge budgets in the final execution freeze. Original 163-call holdout remains untouched, with no borrowing.
- Keep consensus section 5 and C-EXIT first-handover/critical-dimension/fabrication rules, complete U1–U5 cycle under one manifest, no pooling across revisions, and Astra judging followed by authoritative user visual judgment. No pilot/holdout, fresh-family success, token saving, quota saving or final-v4 exit is claimed.
- Separate processes and source-independent metric code are not independent numerical kernels: both use the pinned OCCT stack. This work does not certify physical manufacturing, CAM, six-DOF assembly, universal continuous curved-wall bounds, or a general hostile-document/OS sandbox.
