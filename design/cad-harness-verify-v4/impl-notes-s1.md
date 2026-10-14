# S1 implementation notes — sol

S1 is implemented and exercised offline on DPC-019. This is an implementation-review result, **not** final v4 authorization, a pilot result, or a holdout result. S2/S3 are not claimed complete.

## Boundaries

- Used independently authored synthetic development fixtures only. No `pilot-user/` attachment or `v4-holdout-private` content was opened or used for this implementation.
- Made zero live harness generator/judge calls. Model-path smoke used recorded development responses or mocked callbacks; actual CAD compilation and verification ran locally.
- Ran no pilot or holdout, authored no fresh holdout family material, and made no commit.
- Installed or changed no runtime packages. Existing resource limits and the original 163-call holdout allocation remain unchanged.
- Original `policy.json`, `SKILL.md`, `modeling.md`, and `contracts.md` bytes remain unchanged. C capabilities use an explicit separate `c-s1` profile and `.v4c` contracts.

## Implemented paths

| Capability | Implementation | Observable boundary |
| --- | --- | --- |
| C1 STEP | `tools/cad_verify_v4_inputs.py`, `cad_verify_v4_worker.py` | Immutable input admission, original axes, normalized mm, bbox/volume/face atlas, source-unit attestation, explicit selection provenance. Bbox is not treated as thickness; unknown thickness is null. |
| C2 raster/contour | `tools/cad_verify_v4_contours.py` | Explicit PNG interpretation and scale, topology-preserving preparation, approved simplification/real tangent fillets, exact native contour segments. Infeasible or unsupported geometry is refused rather than silently repaired. |
| C3 engraving | `tools/cad_verify_v4_text.py`, `cad_verify_v4_compile.py` | Registered-font outlines and native operative text/height/depth/placement; recessed geometry and counter preservation checked on actual output. No model file access or ambient font selection. |
| Typed native construction | `tools/cad_verify_v4_plans.py`, `cad_verify_v4_compile.py` | Data-only plans for contour extrusion, reference fixtures and engraving; native recompute and reopening remain operative. References are not exported as extra solids. |
| Independent judges | `tools/cad_verify_v4_judges.py` | Reopens FCStd and STEP independently; checks dimensions, native/export roundtrip, solid count, reference relationships, engraving, two-leg fidelity and actual-output radius/tool access. |
| Supervision/integration | `tools/cad_verify_v4_s1.py`, existing `eval_verify_v4.py`, `cad_verify_v4_agent.py`, `cad_verify_v4_live.py`, `cad_verify_v4_ledger.py`, `cad_verify_v4_pilot.py`, `cad_verify_v4_freeze.py` | Explicit profile routing, trusted headless worker, owned-PID/cleanup checks, immutable per-case bindings, repair privacy, complete raw streams, development replay and separate zero-live implementation lock. |

New contracts: `capability-manifest`, `input-manifest`, `prepared-inputs`, `contour`, `capability-plan`, `judge-card`, `judge-result`, `step-facts`, `step-recipe`, `contour-recipe`, `contour-source`, and `text-outline` schemas under this directory. `ledger.schema.json` includes deterministic work events and bindings. New policy/skill files are `capability-policy.json`, `skills/cad-harness-v4/c-s1.md`, and `skills/cad-harness-v4/contracts-c-s1.md`.

The registered font and its license are `skills/cad-harness-v4/fonts/DejaVuSansMono.ttf` and `LICENSE_DEJAVU`, copied from inspected installed resources. SHA256:

- Font: `602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3`
- License: `d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e`

Independent fixture sources: `dev-c-s1/generate.py` and `dev-c-s1/expected.json`. Tests: `tools/test_verify_v4_s1.py`, `tools/test_verify_v4_s1_integration.py`, and `tools/test_verify_v4_s1_native.py`.

## Contract and isolation details

Input admission binds kind, role, size and SHA256. Traversal, absolute/drive-relative paths, alternate data streams, links/reparse points and special files are rejected. Forbidden lexical components are rejected before content lookup; canonical paths are checked too. Source hashes are checked before and after preparation. Face references include ordered atlas entries and geometric signatures; ambiguous correspondence is not auto-selected.

The model receives request text plus authenticated typed runtime facts. It does not receive attachment file access. Font runtime facts expose approved IDs, glyph coverage and hashes, not font contents or filesystem paths. Facts and selection digests are rechecked at each model phase. Request, input manifest, prepared bundle and checker card bindings are pinned before admission and rechecked before native/model work and acceptance. Mid-case card drift stops INCOMPLETE rather than changing the target or using R1.

The pinned native Python is launched with `-I -B`, a trusted bootstrap and closed stdin (`DEVNULL`). Ready metadata must identify the owned PID and FreeCAD runtime; GUI/window, capture and cleanup checks remain mandatory. Native documents are closed. Compilation and independent reopening occur in different processes. Native custom proxies are trusted data-only persistence, not model-generated executable code.

Repair observations expose measured values, uncertainty and safe status/error codes, not private checker thresholds, targets, card paths, masks or recipes. The original profile retains its original observation contract. Completed geometric FAIL may use the existing R1. Timeout, capture/ownership/cleanup failure, missing dependencies and binding drift stop INCOMPLETE instead of becoming model-repairable geometry failures. Shared P1/R1/CAD-attempt and active-time budgets are retained. Deterministic work is recorded separately from physical model attempts.

## Judge semantics and limits

- Image→contour and contour→actual-output fidelity each report IoU and bounded symmetric Hausdorff distance. The independent checker verifies decoded RGBA and row-run mask hashes and pixel registration. Integer Rec.601 is explicitly `(299R + 587G + 114B + 500) // 1000`.
- Minimum radius and tool accessibility inspect the **actual output section**, including parameter edits, not just preprocessing declarations. Uncertainty is explicit. Accessibility is a planar disk-center geometric result, not a CAM/manufacturability guarantee.
- `reference_gap` is a signed parallel-planar gap/spread/projected-overlap check. `reference_clearance` measures complete selected original faces, including curved faces. `reference_contact` measures common face area with explicit uncertainty; it does not invent an inflated contact band.
- `translation_clearance` certifies only the declared overlap-free interval; it is **not** maximum play. `reference_play` bounds the connected collision-free translation component using actual collision stops, explicit total/positive/negative convention, search interval/resolution and volume uncertainty. Missing barriers give UNKNOWN; disconnected free samples are not a connectivity proof.
- Native/export/reimport checks verify one valid solid, expected bounds/volume and operative parameters. Rejected native edits clear stale Shape rather than retaining a misleading previous result.
- Unsupported PNG/sample/topology cases, disconnected islands or infeasible fillets are refused; no carrier, bridge or base is invented. The reference-fixture family retains the existing build-spec operations/count limits and is not arbitrary conformal/freeform design.
- These are bounded geometric checks, not six-DOF assembly, friction, compliance, universal typography/readability, physical fabrication or hostile-document/OS sandbox guarantees. Missing required bounds or unsupported geometry remains UNVERIFIED. Astra/user visual judging was not run.

## Exercised verification

All commands below ran from `C:/dev/CAD-HARNESS-herdr`.

```powershell
python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration
```

Observed: **119 tests run, OK, 1 skipped** in 7.182 s. All existing **92** tests remain passing. The additional host tests contribute 26 passes and one Windows symlink-creation skip; mocked reparse rejection is exercised.

```powershell
cmd /c "set CAD_VERIFY_S1_NATIVE=1&& C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\python.exe -B -m unittest tools.test_verify_v4_s1_native -v"
```

Observed: **22 native tests run, OK** in 23.511 s. These use actual FreeCAD, not a mocked CAD kernel. Coverage includes STEP measurements/ambiguity, curved reference faces, collision-bounded play, operative native reference pockets, raster topology/fillets/refusals, both fidelity legs, scale/topology/radius/tool-access negatives, Rec.601/mask mismatch, native roundtrip and parameter edits, engraving counters/depth/frame/wrong-text/unsupported-glyph negatives, and a fake model callback driving real supervised compilation and independent reopening.

Runtime observed: FreeCAD **1.1.4**, GuiUp **0**, native Python **3.11.14**, OCCT **7.8.1**, NumPy **1.26.4**, SciPy **1.16.3**, Pillow **12.0.0**, Shapely **2.1.2**, ContourPy **1.3.3**, FontTools **4.61.1**, pythonocc **7.8.1.1**. Native executable: `C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`.

### Actual facade/native smoke

Evidence root: **`reports/verify-v4-s1-dev-20261014T063456Z/`**. These are independent development artifacts, not trial results.

| Exercised path | Evidence |
| --- | --- |
| STEP preparation | `step-cli/summary.json`, `step-cli/native/prepared.json` |
| Raster preparation | `contour-cli/summary.json`, `contour-cli/native/contour.json` |
| Text outline preparation | `text-cli/summary.json`, `text-cli/native/text-outline.json` |
| Prepared-data merge | `merged-prepared.json` |
| Analytic/native compilation | `compile-cli/summary.json` |
| Raster→contour→native→STEP chain | `raster-chain-cli/summary.json` — PASS |
| Engraving/native reimport | `engraved-cli/summary.json` — PASS |
| Reference fixture/native reimport | `reference-cli/summary.json` — PASS |
| Standalone judge | `judge-cli/summary.json` — PASS |
| Prepared bundle intake | `prepared-bundle-cli/bundle.json` — integrity only, not eligibility |
| Development batch | `batch-cli-v2/summary.json` — PASS; physical model attempts 0, live calls 0; pilot/holdout not_run |
| Parse repair + CAD repair replay | `request-cli-v3/summary.json` — PASS; 3 replay responses, 0 physical model attempts, 0 live calls |

The replay deliberately supplies malformed JSON, then a parsed development width of 35 instead of the independently requested 34, then a correct R1. Actual native verification catches the first geometry FAIL before the repaired PASS. It records two CAD attempts, four deterministic operations (three PASS, one FAIL), 8/8 complete stdout/stderr captures and 5.515999999945052 s of deterministic work. Failed artifacts remain available. This repaired dev result is not a pilot first-handover PASS or model-quality measurement.

The raster-chain ledger records distinct compile/verify PIDs, closed stdin, GuiUp 0, zero owned windows, complete SHA-bound streams, exited cleanup and `document_closed: true`. Its independently measured development solid has volume 2961.0973355292326 mm³ and bounds approximately `[4,38,4,26,0,4]` mm. Native/STEP bounds delta is 4.440892098500626e-16 mm and volume delta is zero. Its actual-output radius interval is `[2.9999899999999893,3.0000099999999894]` mm. These are **dev fixture measurements, not user/pilot tolerances**.

Failure regressions were exercised for sharp-output radius and narrow tool access, technical-failure retry, checker-card drift, decoding/mask mismatch and immutable bindings. Invalid early dev batch/lock attempts were retained rather than rewritten as successes. An incidental text-counter assumption was removed; the retained counter invariant uses an independent Pillow/FreeType check, not values copied from the compiler.

## Original-profile preservation

`original-profile-snapshot.zip` preserves the observed pre-S1 executable/public commitment set: **68 files, 316045 bytes**, SHA256 **`763fb69bdef88cb3ba62c7fb646ebcc3bd16e80585356bd732eefeddf506447d`**. Its `snapshot.json` binds the copied files. ZIP timestamps are canonical serialization metadata, not evidence of source modification times.

The extracted original executable completed its own preflight: offline_ready, zero live calls and zero CAD attempts. Observed original skill SHA256 is `df6a2ff9df096e7be5815957318f00684810fd79422d203d6fcdf42c9de25109`; original policy SHA256 is `c5a301e3944dae3211fbffed3f7456c6712bd7558ebfc9fa8bea29d1ac69b5aa`. The owned throwaway extraction was removed after that smoke; the archive remains.

This is an **observed pre-S1 baseline**, not an assertion that it matches an unseen earlier manifest. Old manifests were not rewritten. An original trial must use its own matching immutable implementation/manifest, not silently run changed root code under old hashes.

## Verified S1 implementation lock

Current review lock: **`reports/verify-v4-s1-dev-20261014T063456Z/implementation-lock-v4/manifest.json`**, adjacent `SHA256.json`. Verification receipt: **`implementation-lock-verification.json`** at the evidence root, with full `.stdout.txt` and `.stderr.txt`.

Observed verification:

- `status: verified_offline_implementation_lock`
- Manifest SHA256: **`75a6a374a66e3ad7c53f4647bac90c45d92ecabe89a9d260e810fe94bc782337`**
- Schema `cad-harness.capability-manifest.v4c`, profile `c-s1`, **authorization null**, **final_v4_ready false**
- Rechecked 98 bound files and 5028 native-runtime files, recipe/dev-input bindings and the original snapshot.
- C skill SHA256: `05f9949cd1d5b29dd79fe2bf451990027ae3ce0d72d8f5badd53fb6cd2e7ca6f`
- C policy SHA256: `715bc5dc6d739ab9500c28dee565b2573172b489692abc072e50184079a699f0`
- A temporary forged copy with a rebound checksum file but non-null authorization was rejected with `capability.authorization:type`; no live command was invoked. The original lock was not edited.

Recorded future generator identities are **holdout: `openai-codex/gpt-6.1-sol`, xhigh** and **pilot: `openai-codex/gpt-6-astra`, max**. Recorded model judge: **`openai-codex/gpt-6-astra`, max**, authorization null; pilot generator/judge model coincidence is explicit and user visual judgment remains authoritative. None was called for this work.

Earlier `implementation-lock`, `-v2` and `-v3` directories are retained development history, **not the current lock**. Later S2/S3 source changes invalidate this S1 snapshot and require a new integrated lock. There is no CLI/environment override that turns this zero-live review manifest into trial authorization.

## Remaining final-v4 gates

S1 offline implementation is complete. Final integrated release and trials remain subject to C-EXIT/C-R1/C-R2/C-Q and consensus section 5:

1. Complete and review S2 direct edit and S3 reconstruction. C-A already fixes U3 at G2 with the existing 0.005 mm requirement; U2 has no maximum envelope. Do not reopen these as unanswered questions.
2. Resolve/fix the applicable C-Q4–Q8 critical-tolerance, measurement, ROI/fidelity and engraving conventions in approved cards; complete delegated C-U5 consensus choices. No pilot-specific numbers were invented here.
3. C-Q9 fresh-family counts, denominators/pass gates and accepted-call/model-judge budgets still need user authorization. Resource changes under C-Q10 require evidence; existing active limits were retained.
4. Lock the integrated S1–S3 code/skill/recipes/judges **before independent family authoring**, then bind custodian bundles/cards/cohorts/budgets and all five input commitments in the final execution freeze.
5. Only then perform authorized fresh holds and the complete U1–U5 cycle. Preserve the original 163 allocation and custody, no cross-allocation borrowing, no pooling across manifests, fatal critical/fabrication first-handover rules, and user-authoritative visual judgment.

No token-saving, quota-saving, general manufacturing, fresh-holdout success or v4 exit claim follows from this development smoke.
