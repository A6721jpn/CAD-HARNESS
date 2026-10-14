# S3 implementation notes — sol

**S3 is implemented and verified offline under the separate `c-s3` profile.** This is development evidence, not blind reproduction, pilot adoption, live authorization or final v4 exit. `c-a2-sign-sol.md` records the requested two-line **AGREE** on C-A2's USER 17:28 recording.

No `pilot-user/` attachments or private holdout material were opened or used. No live generator/judge calls, pilot runs or commits were made. U3's 0.005 mm pilot value is not a development target; all source shapes and numerical cards below were independently authored.

## Implementation and integration

| Surface | Files / behavior |
| --- | --- |
| C5 construction | `tools/cad_verify_v4_s3_rebuild.py`: actual finite freeform patch joining, C2 knot reconstruction, source-boundary preservation, solid reconnection and operative native persistence |
| Independent C6 | `tools/cad_verify_v4_s3_judges.py`: bounded bidirectional surface deviation, geometric G1/G2, complete unselected-source preservation, actual solid/face-count and native-reopen evidence; no rebuild/editor/compiler oracle import |
| Host admission | `tools/cad_verify_v4_s3_contracts.py`; eight `schemas/s3-*.schema.json` documents for inputs, prepared data, STEP facts/recipe, plan, judge card/result and capability manifest |
| Policy / skill | `policy-c-s3.json`, `skills/cad-harness-v4/c-s3.md`, `contracts-c-s3.md`; offline-only, fixed G2 plan family, no generated-source import/I/O expansion |
| Shared entry points | Explicit S3 dispatch in `eval_verify_v4.py`, `cad_verify_v4_s1.py`, `cad_verify_v4_inputs.py`, `cad_verify_v4_plans.py`, `cad_verify_v4_worker.py`, `cad_verify_v4_agent.py`, `cad_verify_v4_pilot.py`; existing supervisor/accounting, generic native-document helpers and freeze binding are reused |
| Independent controls | `dev-c-s3/generate.py`; `tools/test_verify_v4_s3.py`, `test_verify_v4_s3_rebuild_native.py`, `test_verify_v4_s3_judges_native.py` |

The deterministic CLI owns actual input import, geometry, reconstruction and measurement. The skill chooses the intended patch grid/orientation and explicit work settings; it cannot read files, probe the host, emit arbitrary reconstruction code, invent missing acceptance values or override an UNVERIFIED check.

S3 input facts add measured parameter domains, global-frame corner points and spline degrees. The original reference bytes/frame remain immutable. Corner facts are not treated as a trim or continuity certificate. Selectors are revalidated against actual geometry, signatures and complete shared-edge adjacency, not merely `FaceN` labels.

### C5: real reconstruction, not a copied reference

- `surface_rebuild` admits a finite oriented rectangular tensor grid. Swap/reverse flags define an explicit affine patch correspondence. Native source data is used directly for B-splines/Bezier surfaces; planes have an exact bilinear representation. There is no generic approximate surface-conversion fallback.
- The CLI aligns degrees/knot partitions, constructs the common C0 spline net, then uses actual OCCT knot removal to enforce parametric C2 in both directions within the declared fitting setting. Boundary compatibility, positive weights, degree/pole limits and tensor allocation limits are checked. A failed fit does not return the unchanged source as success.
- The preserved outer boundary is checked before sewing the replacement into the original unselected faces. A valid closed single solid is required. Holes/notches and unsupported trim/chart/periodic cases are not silently filled, bridged or reinterpreted.
- `SurfaceRebuildProxy` persists data plus a fixed version token. An actual interior `PoleOffsets` vector changes the native surface/solid; boundary poles are locked. Recompute failure clears stale geometry. Native restoration does not require the original source file, and verification binds the embedded original/plan/facts to admitted inputs.
- This creates new operative history; it does not recover lost STEP history. Opening without the frozen installed extension/Python path is not promised to preserve recomputation.

Parametric C2 is not alone a blanket geometric-success claim: C6 independently checks actual native data, regularity, continuity, full-region deviation and the unchanged complement.

### C6: full-domain evidence

**Maximum deviation:** bidirectional Hausdorff `[L,U]` over the registered full finite regions in the original frame. Outward-rounded Boehm/Bernstein enclosures provide corresponding-point upper bounds only after complete chart/trim coverage; actual native closest-point distances provide lower witnesses. Sample maxima, minimum shape distance and fitter-reported error do not certify the maximum. PASS requires the supported upper bound within the card; FAIL requires a valid lower witness above it; unresolved evidence is UNVERIFIED.

**G1/G2:** full positional/oriented-normal seam checks, with G2 comparing the invariant physical shape operator, not raw UV derivatives or principal-curvature numbers alone. Actual native knot seams are automatically checked at their native coordinates in addition to registered seams. A same-face exact Ck certificate requires actual sufficient knot multiplicities, correct correspondence/orientation and a full-seam interval Jacobian proof; it is not a trusted `Continuity` enum or compiler flag.

**Complete preservation:** every unselected original face and every unmapped output face must have a bijective continuous support/full-trim certificate. Equal face count or excluding a moved bottom from an ROI is insufficient. Preserved faces may cross the ROI; their global identity is still checked. Decisive outside closest-point witnesses can fail the result; unsupported preservation prevents PASS.

**Native parameter roundoff:** cards can preregister `domain_uv: native_full`. The checker measures the actual full `Face.ParameterRange`, records it, and rigorously includes endpoint strips through polynomial extrapolation. Jets are differentiated on real native knot spans before affine composition. UV trim roundoff is bounded physically, not ignored with a fixed crop epsilon. This handles the observed STEP domain starting at approximately −1.08e-16 / −4.53e-17 without post-generation card editing or acceptance widening.

The full generation worker requires `solid_valid`, `face_count`, `surface_deviation`, `g2_continuity` and `native_roundtrip`; G2 contains G1 preconditions. Focused library cards cannot certify a complete handover merely by checking validity or reopening.

## Verification actually run

Working directory: `C:/dev/CAD-HARNESS-herdr`. Complete evidence root:

`reports/verify-v4-s3-dev-20261014T105649Z/`

Final registered development assets/cards are in **`inputs-v3/`**. Earlier input versions, API investigations and unsuccessful new host-fixture checks remain separately recorded; nothing is relabelled as a blind or successful pilot trial.

| Final suite | Run | Passed | Skipped | Unittest elapsed |
| --- | ---: | ---: | ---: | ---: |
| Complete host suite, including all original 92 regressions and all prior S1/S2 host coverage | 140 | 139 | 1 | 7.515 s |
| Pinned native-runtime suite, including all existing 59 runtime tests | 92 | 92 | 0 | 43.210 s |

The skip is the existing Windows test-symlink permission case; reparse-point rejection remains tested. The runtime suite includes 86 kernel/native cases and six host-safe admission controls. The two S3 card-admission controls also run in the host suite; do not add the suite counts as independent observations.

Host command:

```text
python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration tools.test_verify_v4_s2 tools.test_verify_v4_s3 tools.test_verify_v4_s3_judges_native.S3CardAdmission -v
```

Native command, with `CAD_VERIFY_S1_NATIVE=1`, `CAD_VERIFY_S2_NATIVE=1`, `CAD_VERIFY_S3_NATIVE=1` and `CAD_VERIFY_S3_FIXTURES` pointing to `inputs-v3/`:

```text
C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe -B -m unittest tools.test_verify_v4_s1_native tools.test_verify_v4_s2_edit_native tools.test_verify_v4_s2_judges_native tools.test_verify_v4_s3_rebuild_native tools.test_verify_v4_s3_judges_native -v
```

Logs/metadata: `host-complete-tests-v1.{stdout.bin,stderr.bin,json}` and `native-tests-v1.{stdout.bin,stderr.bin,json}`. The initial subset host run exposed exclusive-create collisions in newly written fixtures. Unique new card files fixed the policy-boundary test; an incomplete/malformed lock test was removed in favor of the genuine lock/copy/tamper smoke below. All pre-existing tests remain included.

New coverage includes actual G1→G2 deformation, both tensor directions, swapped/reversed UV and oblique global frames, lower-body preservation, operative edits/restoration, stale-atlas rejection, failed-fit rollback, tiny notches, cached-shape invalidation, unequal-speed geometric G2, rotated-curvature decoys, off-grid localized deviations, exact numeric boundaries, rational/periodic refusal, singular/resource exhaustion, Bezier extraction, full STEP preservation, hidden actual knot seams and complete source/candidate complement checks.

### Real native CLI smoke, no generated model responses

| Independently authored case | Source → output faces | Native / STEP verdict | Certified STEP deviation upper | Registered dev maximum |
| --- | --- | --- | ---: | ---: |
| G1-only roof pair | 10 → 9 | PASS / PASS | 0.006686726487 mm | 0.08 mm |
| Two-direction four-patch grid | 16 → 13 | PASS / PASS | 0.040020009996 mm | 0.6 mm |
| Swapped/reversed source chart | 10 → 9 | PASS / PASS | 0.006686726487 mm | 0.08 mm |

Both representations passed solid, face-count, deviation, G1/G2 and native-roundtrip criteria. Their same-face G1/G2 structural residual bounds were exactly zero after full regularity/coverage checks. On the pair, all eight unselected original/output faces were certified with an outside-preservation upper of approximately 2.1651e-6 mm against the independent 1e-5 mm numerical identity budget. These numbers describe these dev fixtures, not U3 or a manufacturing guarantee.

Exercised facade paths and retained evidence:

- `preflight --profile c-s3`: offline-ready only; also re-executed inside the final lock.
- `prepare-step`: `prepare-complete-v1/`; owned native process, complete measured facts and source provenance. `merge-prepared` produced `merged-prepared.json` for the same immutable manifest.
- `compile-plan`: `merge-complete-v1/`, `tensor-complete-v1/`, `reparameterized-complete-v1/`. Actual C5 geometry, operative edits, saved FCStd/STEP, separate verification process and independent reimport.
- `judge`: `judge-complete-v1/`; verified the retained pair candidate independently without regenerating it.
- `request` with explicitly mocked response replay: `request-complete-v1/`. Malformed initial JSON → shared P1 → intentionally incompatible fitting tolerance → one actual failed native attempt → R1 → valid reconstruction/reverification. Exactly three replayed responses, two CAD attempts, zero physical model attempts. All three deterministic operations completed; six of six raw CAD streams were complete. The failure remains in the ledger. Deterministic-work wall sum was 5.656 s; this is not a manual/time-saving baseline.
- `run --phase development`: `batch-complete-v1/`; one declared mocked-response episode passed through actual native construction/checking, with zero live calls.
- `prepared-bundle`: `bundle-complete-v1/`; preserved the authored dev request bytes and committed inputs. This is integrity-only independent-dev evidence, not real-user provenance or pilot enrollment.

`s3-smoke-summary.json` indexes actual certificate results. Operation ledgers record owned PIDs, closed stdin, monotonic intervals, input/code hashes, complete binary stdout/stderr, exit/cleanup and document-closure evidence. Native and STEP reopening both reported zero bounds/volume discrepancy on these cases. No pricing, provider-token consumption, quota capacity or productivity saving is inferred from mocked responses.

## Implementation review lock and preservation

Current review lock: `implementation-lock/manifest.json` under the evidence root.

- Manifest SHA-256: **`d57f0f39ebd34b23075c1c6d6152d4b2afa3b833c6bf2744ee2a467a79af482c`**.
- Reverified **134 bound implementation/policy/skill/schema/generator files** and **5028 pinned native-runtime files** on DPC-019.
- Skill SHA-256: `90995b8aaa29d73b02f0d818f2923bf0936423c3547e654b0733d1aa775190b1`.
- Policy SHA-256: `2051fc41a06606bfa5a3d0b04f90f7ebaeb695f75bfaf5f8f30fe667d9c3d74f`.
- FreeCAD **1.1.4**, bundled Python **3.11.14**, OCCT **7.8.1**; host tests used Python **3.12.10**.
- **Authorization null; final_v4_ready false.** This is not a live execution manifest.

`lock-smoke-capture.json` records successful verification of the real lock and an unchanged relocated control. Separate full copies with correctly rebound checksum files rejected non-null authorization, changed code bindings and a downgraded prior-stage identity. The original lock was never modified. This is stronger than expecting a malformed incomplete manifest to fail.

Before any S3 root mutation, the complete pre-S3 S2 implementation was archived and verified at `design/cad-harness-verify-v4/s2-profile-snapshot.zip`: **117 files, 1,910,809 bytes**, SHA-256 **`9548163e733c159893549eec025d312eb5fceace615f9fd41f10ae7212af184d`**. It includes the authority documents current at that snapshot; it is not claimed byte-identical to an earlier S2 review lock. Existing S1/original archives and the unchanged-scope 163-call holdout were not repurposed.

Recorded future identities remain holdout **`openai-codex/gpt-6.1-sol` / xhigh**, pilot **`openai-codex/gpt-6-astra` / max**, judge **Astra / max**. The same-model pilot generator/judge limitation is explicit; the user's visual/adoption decision remains authoritative. None of these model paths was called.

## Limits and unchanged gates

- Reconstruction requires compatible finite rectangular patch charts and boundary correspondence. It is not an arbitrary-network, arbitrary-trim, periodic or universally convergent freeform solver. Incompatible constraints/fitting failures remain outcomes, not permission to lower G2 or invent another surface.
- Selected-domain C6 certificates currently cover nonrational nonperiodic rectangular polynomial B-spline/Bezier faces, degree at most 12 and at most 4096 poles/spans per face. Rational selected surfaces, selected planes, unsupported trims/outside supports, uncertain correspondence, singularity or exhausted bounds return UNVERIFIED where no supported certificate exists. Native positive-weight construction alone does not waive those limits. Do not screen away scored failures to improve a family denominator.
- G2/deviation, full source preservation, solid validity, editability and semantic intent are distinct. No G3, general Class-A, CAM, physical strength or universal manufacturing-accuracy guarantee is made.
- Current active limits remain episode 900 s, initial/repair 450 s, existing subcaps, one shared P1, one R1 and at most two CAD attempts. The generic four-call ceiling does not add a fourth typed-plan response. The unagreed C-D extension proposal was not applied.
- Verified no-output overload still requires the full 600 s wait and identical uncapped resend, excluding only the verified unavailable cycle from active clocks. Full wall/capture remains recorded. Quota consultation at 55%, hard stop at 60%, and stale/missing-quota stops remain intact. No live overload recovery is claimed by development mocks.
- Final code/skill/recipe/judge agreement, independent fresh family authoring/control review/custody, agreed cards/counts/gates/budgets and final execution authorization remain prerequisites. All five original requests must pass under the agreed final trial; no development case substitutes for them.
- Preserve consensus §5 and C-EXIT: user adoption, no edit or verified correction within 300 elapsed seconds from first edit, and irreversible failure for a critical-dimension error/fabrication at the first or any later handover. Later repair does not erase that history.

S3 is ready for independent offline review within these demonstrated domains. Fresh holdouts and the five-request pilot remain **not_run**. No commit was made.
