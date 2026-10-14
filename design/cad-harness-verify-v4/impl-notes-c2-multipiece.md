# C-R6 — multi-piece C2 implementation

## Progress log (chronological)

- Scope mapped; shared interfaces and disjoint ownership recorded. Authority: `PLAN-V4-ADDENDUM-C.md:132-138` and `.tmp-sol-multi.md`.
- Required behavior: preserve disconnected foreground components, placement, nesting and holes; separate native solids in one document/STEP compound; no bridges/backing/joins. One registration and final all-component canonical Y extent 50 mm. Both fidelity legs, actual min-R and tool access cover every piece. Other families and single-piece C2 remain single-solid.
- Implementation milestone: canonical alternating nesting forest, all-piece uniform registration, C2-only source-derived solid counts, compound compiler path, neutral/native pipeline integration, current schemas/contracts, new production registry and independent multi-piece RGBA fixtures/tests are implemented. Combined execution is pending; no pass claim yet. Previous C-R5v2 evidence remains historical.
- Independent dev material only. No pilot-user/ or private-holdout access, live/model/provider calls or commit. Reported custodian failure is accepted as supplied; it will not be rerun or inspected by the implementer.
- Default separate-piece behavior is authorized by C-R6. The unanswered bridge/backing alternative is not used and does not block this implementation.
- Construction smoke: `reports/verify-v4-c2-multipiece-20261014T184709Z/generate-multi-dev.event.json` records exit 0, 8.344 s, closed stdin and complete stdout/stderr. Actual production preparation has three components, one hole and parent forest outer -> hole -> island plus a separate root. Canonical global Y extent is 50.000000000000014 mm; one scale/origin maps every source piece. Both native constructions were written successfully. This is construction evidence, not yet neutral acceptance.
- All-piece checker matching, per-piece requested tool-center connectivity and collective native edit coverage have been integrated. Complete suites are next; failures, if any, will be retained and corrected on these dev cases only.
- First complete regressions ran and retained their failure evidence: host 191 tests (one error, one existing Windows skip); native 125 tests (six failures/four errors including subtests). Root causes were a dev manifest's invalid image role, overly strict admission of an existing analytic implicit-hole-parent form, a missing-contour metrology plan default, a new caller omitting its authenticated count, and STEP import exposing compound solids as separate objects.
- Fixes applied without changing recipe geometry or acceptance numbers: correct the dev role/caller; preserve the existing analytic single-piece form and conservative one-solid default; read the COMPLETE multi-piece STEP topology into one compound feature without fusing or dropping pieces. Single-piece/other-family STEP object guards stay unchanged. Incidental error-wording assertions were removed; substantive count and failure behavior checks remain. Targeted and complete reruns are pending.
- Targeted confirmation cleared the host defect and the existing C1/analytic regressions. Remaining harness UNVERIFIED results identified a checker representation defect: a closed native wire evaluated its shared endpoint 7.105427357601002e-15 mm apart, creating an artificial microscopic closing edge in the polygon approximation. The checker now represents an already accepted closed loop with one shared endpoint and adds the measured displacement to its approximation-error enclosure. The existing open-chain rejection bound is unchanged; no candidate geometry, recipe or acceptance tolerance is altered. Both bare/harness real native roundtrip/full-card cases now pass in the targeted confirmation (exit 0, 42.047 s). Full reruns and fresh CLI proof remain pending.
- Final complete suites passed: host 191 run / 190 pass / one existing Windows symlink-permission skip (101.272 s); native 125/125 pass (590.155 s). Original suites remain included; source-count/STEP/partial-edit/closure regressions are retained and green. Fresh final dev artifacts were regenerated after source fixes (exit 0, 10.907 s). The actual CLI neutral proof for both arms is the remaining verification step.
- Fresh actual CLI verification passed: production image-to-contour exit 0 (6.078 s), neutral bare exit 0 (37.579 s), neutral harness exit 0 (65.734 s). Each arm passed all ten criteria on BOTH FCStd and STEP; each representation has exactly three valid solids, and operative native probes cover every solid. CLI preparation exactly matches the proof packet. Final proof index and conservative measurements are recorded below.

## Verification

**COMPLETE for this C-R6 independent-dev task.** Complete host/native suites and both actual CLI neutral arms pass. No pilot/holdout/benchmark run, worktree commit, final integrated lock or live authorization was performed.

## Active recipe and retirement

| Resource | SHA-256 |
| --- | --- |
| `design/cad-harness-verify-v4/c2-production-recipe-cycle2.json` — active file, 847 bytes | `0b6d09b67c67a050de5247e9c28f95abc454ee33b2c8cef604f5839ea7dc7e04` |
| Active recipe, sorted-key compact canonical JSON | `e061fa8618dbd22bfa810999f3d6b5ab5f33d2c07d7cdd7734566486f5224231` |
| `design/cad-harness-verify-v4/c2-production-registration.json` | `5b97fc37d4d3cf6ae751258f84fee001b4c4156e1bb7fdc3b1e5fe9e82568146` |
| Retired, unchanged `c2-production-recipe.json` | `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00` |

There is ONE active registration; the old recipe is hash-bound retired metadata, never a production fallback. Runtime registration does not open the historical recipe. Only recipe `topology` changed, from `{components:1, holes:"preserve", islands:"reject"}` to `{components:"preserve", holes:"preserve", islands:"preserve"}`. An actual semantic equality check confirms every other recipe control is unchanged; see `recipe-cutover-check.json` under the evidence root.

Alpha-derived foreground, no simplification/rounding, pixel-space approximation controls, bounded source-error fitting, final global height and both C-D fidelity limits are unchanged. No new source-specific geometry or acceptance tolerance was chosen.

## Implemented contract

- **Topology:** raster boundaries form a canonical preorder forest. Root outers have no parent; each nested loop has its immediate enclosing loop index, with alternating outer/hole roles. Material islands inside holes remain separate pieces. Native spatial containment, boundary separation and source/output hash regeneration verify the declared hierarchy. Old strict raster and analytic single-piece branches remain single-piece; the existing optional implicit analytic counter-parent form remains admissible.
- **Registration:** approximate in pixel units, compute extrema over ALL final curves, then apply ONE uniform scale and translation to source mask boundaries and canonical curves. No per-piece normalization or candidate registration fitting. Actual dev canonical Y extent is 50.000000000000014 mm; the floating-point residual is not corrected after scoring.
- **Count authority:** `inputs.contour_solid_count` derives expected cardinality only from authenticated, declared C2 raster source topology. No plan, context or judge-card count override was added. Other families and single-piece C2 still require exactly one solid.
- **Native output:** declared multi-piece C2 uses a document-level frozen `Part::FeaturePython` compound with operative whole-output Width, Thickness and Origin. Single-piece C2 retains the existing PartDesign Body path. Every piece is extruded; no bridges, backing, fusing or deletion. The existing engraving dependency chain preserves the bound contour-derived count. Invalid edits clear the output instead of preserving stale solids.
- **Independent checking:** native/STEP validity, solid count, native editability, original-image fidelity, contour/output fidelity, actual minimum radius and disk-center coverage include every piece. Fixed-frame piece/hole correspondence and nesting are checked in addition to aggregate counts. Collective edit evidence must cover every solid, so one operative piece cannot certify unrelated cached pieces.
- **STEP:** for declared multi-piece C2 only, read the complete file topology into one compound feature. FreeCAD's one-object-per-transferred-solid presentation is not mistaken for multiple submitted output files, and no imported solid is dropped or joined. The old strict single-output object checks remain for single-piece/other families.
- **Tool connectivity:** total uncovered-area bounds cover the complete output. If connected tool-center regions are requested, certify each material piece separately; disconnected physical parts do not require an impossible cross-piece tool path. Missing per-piece certificates remain UNVERIFIED. The proof annulus makes no global connectedness claim (`require_connected=False`); the separate two-convex-piece regression verifies the requested-connectivity behavior.
- **Numerics:** already accepted native loop closure is represented exactly during chord tessellation, with the measured endpoint displacement added to the symmetric error bound. Open-loop rejection is unchanged. This fixes checker representation, not candidate geometry, and uses no buffer repair or tolerance widening.

Main changed files: `tools/cad_verify_v4_contours.py`, `cad_verify_v4_compile.py`, `cad_verify_v4_judges.py`, `cad_verify_v4_inputs.py`, `cad_verify_v4_plans.py`, `cad_verify_v4_artifacts.py`, `cad_verify_v4_artifact_judges.py`, `cad_verify_v4_worker.py`, `cad_verify_v4_integrated.py`, `cad_verify_v4_s1.py`, `cad_verify_v4_c2_recipe.py`, the current recipe/registration and supporting contour schemas. Current `skills/cad-harness-v4/c-s1.md` and `contracts-c-s1.md` describe the new declared case. Original profile archives, model file-read boundaries and other-family one-solid requirements were not expanded.

## Independent fixtures and regression coverage

`design/cad-harness-verify-v4/dev-c2-multipiece/generate.py` authors new RGBA sources: an annulus, a material island within its hole, a separate disk, invisible-RGB and transparent-padding variants, and an additional small sharp piece. Supersampled source geometry is independent of any user attachment.

The bare arm uses three independently specified C++ Sketcher/Pad bodies and a native `Part::Compound`; it does not consume a harness plan, fitted contour or proxy. Its actual Pad edits collectively exercise all pieces. The harness arm uses the registered production preparation and compound extrusion; global Width/Thickness edits are operative over all pieces. Both share the same immutable source/prepared/card/context.

New tests are `tools/test_verify_v4_c2_multipiece.py`, `test_verify_v4_c2_multipiece_native.py` and `test_verify_v4_c2_multipiece_artifacts.py`. Necessary existing production-island tests now verify preservation plus explicit strict-mode rejection, rather than retaining an obsolete rejection expectation. Existing integrated fixture resources were migrated to the new active registration.

Coverage includes nested islands/holes, source-derived count and forged declarations, common scale/padding/alpha semantics, actual compound roundtrip and all-piece edits, dropped/extra/moved/merged pieces, hole corruption, a small sharp component that aggregate area could hide, partial cached-piece editability, scoped one-solid rejection, native compile/reopen and fixed-registration fidelity. The originally failing native and STEP scenarios remain tests; no criterion was weakened to obtain green results.

| Final complete suite | Run | Passed | Skipped | Failures/errors | Unittest elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing 183 host tests plus 8 new host controls | 191 | 190 | 1 | 0 | 101.272 s |
| Existing 111 native tests plus 14 new native controls | 125 | 125 | 0 | 0 | 590.155 s |

The host skip is the existing OS restriction on test symlinks. Both suite processes exited 0. Native execution used pinned Python 3.11.14 / FreeCAD 1.1.4. Exact argv, native guard flags and independent fixture environment are in `suite-commands.json`; full final streams and process metadata are bound in `host-final.event.json` and `native-final.event.json`. No live/model/provider calls occurred.

## Fresh actual CLI proof

Evidence root: `reports/verify-v4-c2-multipiece-20261014T184709Z/`.

Fresh source and artifacts are in `fixtures-final/`. The original production CLI was run explicitly with `--profile c-s1`, this manifest, asset `ring`, the new active `--recipe` and fresh `production-image-cli-final/`; its complete prepared packet equals `fixtures-final/prepared.json`. Each neutral `judge-artifacts` call used the same manifest, prepared packet, card and fixed context, with its own bound bare/harness bundle and fresh output directory. Exact expanded commands and full stdout/stderr are retained in the corresponding `.event.json` and stream files.

Both neutral processes ran headless with closed stdin, owned native execution, runtime/code integrity checks and closed documents. FCStd and independently reopened STEP are valid with exactly three solids. The three operative solid indices are covered in each arm. Both arms use identical implementation bindings, original registration and acceptance card.

| Conservative metric — worst across FCStd/STEP | Gate | Bare | Harness |
| --- | ---: | ---: | ---: |
| Image -> contour IoU lower | >=0.90 | 0.9767242808270201 | 0.9767242808270201 |
| Image -> contour Hausdorff upper, mm | <=1.5 | 0.3057929373002147 | 0.3057929373002147 |
| Contour -> output IoU lower | >=0.92 | 0.9848464200180769 | 0.9999514714337244 |
| Contour -> output Hausdorff upper, mm | <=1.0 | 0.2522937652041832 | 0.01018552884264215 |
| Actual native minimum radius lower, mm | >=0.25 | 4.166656666666665 | 1.067415390612656 |
| Total disk-center uncovered area upper, mm2 | <=0.1, independent DEV control | 0.05270304496721361 | 0.053119713377580195 |

Both image and output topology are three components, one hole, Euler characteristic two. Nesting is outer -> hole -> island plus a separate root, with a fixed piece/hole correspondence. The single registration is 0.5201373318945678 mm/pixel and image bottom-left origin (-14.509270021047607,-20.77912132166397) mm; the checker top-left mapping derives from that same transform.

Explicit DEV numerical controls are in `fixtures-final/expected.json`, not invented user tolerances. Tool coverage is only a planar disk-center model, not a CAM, collision-dynamics or physical manufacturing guarantee.

Proof index: `neutral-proof-c2-multipiece.json`, SHA-256 **`a6acefb4d904adc4890b4741e98938b7b27c017d6afd8031474afa7da7013139`**. It hash-binds the current and retired recipe records, active registry, source generator, input/prepared/card/context, both artifact bundles, both native result/summary/ledger/runtime files, final suite/CLI events and historical failed events.

Final results: `neutral-bare-final/native/result.json` and `neutral-harness-final/native/result.json`; each has all ten criteria PASS on both FCStd and STEP. Historical failed runs remain in the evidence root and are not promoted as final proof.

## Limits and handoff

This is a C2-only independent-dev proof index, not a complete C1-C5 neutral proof or an operative integrated lock. Fresh blind C2 authoring, custodian-only user preparation, the required combined commit and final lock/budgets remain the relay/custodian process under C-R6/C-R4. Earlier C2 cohorts and the old recipe stay retired; unchanged, unrun other-family cohorts are not scored or inspected here.

Unseen image feasibility is not guaranteed. Invalid contacts, lost topology, uncertified numerical geometry, inadequate real tool radius/access, failed edits or missing criteria do not become PASS. No bridges/backing/joins, hidden radius changes or retuning on a user attachment were introduced. No pilot-user/ or private-holdout path was opened, and no worktree commit or live call was made. `authorization: null`; `final_v4_ready: false`.
