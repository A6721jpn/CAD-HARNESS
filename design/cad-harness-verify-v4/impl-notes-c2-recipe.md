# C-R5v2 — ONE C2 production recipe

Implemented and verified on DPC-019 using independent development fixtures only. No pilot-user or private-holdout assets, metadata or derived geometry were accessed. No live/model/provider calls; no pilot, holdout or benchmark run; no worktree commit. This is pre-final-freeze implementation evidence, not live authorization or a final integrated lock.

## Registered production recipe

| Resource | SHA-256 |
| --- | --- |
| `design/cad-harness-verify-v4/c2-production-recipe.json` — exact file bytes, 836 bytes | `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00` |
| Same recipe — sorted-key compact UTF-8 canonical JSON | `361235a66c015765b65fbd1041c031a84b1b369c671a205dc1b4363d63eb8c06` |
| `design/cad-harness-verify-v4/c2-production-registration.json` | `e3c5a585550856c5bb144066c83c0b0d711ce0fd7e9fbb3e61069b71c1310d34` |

`tools/cad_verify_v4_c2_recipe.py` admits exactly this one C2/c-s1 registration and checks the registration bytes, recipe file hash, canonical hash and strict recipe schema. Unknown/missing/modified resources fail closed; the loader never edits or substitutes a recipe. Every C-profile preflight validates it, and implementation bindings include both JSON files and the independent dev generator source. A future integrated implementation freeze therefore binds these resources along with the code, schemas and skill. Existing explicit `--recipe PATH` remains the CLI; no production alias, automatic fallback or second production recipe was added. Fixed-mm-per-pixel development recipes remain legitimate dev inputs, not production replacements.

## Deterministic derivation and boundary

Production settings are explicit recipe data:

- PNG decoded to RGBA8; foreground is **alpha >= 128**, independent of RGB. `alpha.policy: ignore` means no additional opacity gate; it does not ignore the selected alpha foreground channel. Hidden RGB under fully transparent pixels cannot change the mask or geometry.
- `simplify.allowed: false`; `rounding.allowed: false`. No candidate fillet, buffer, dilation, hole deletion or cutter-radius-driven correction.
- `periodic_cubic_biarc_v1`: source-local, uniform arclength samples at 1 pixel; periodic cubic FITPACK fit with initial RMS 0.35 pixel; shared-tangent equal-distance G1 biarcs with 0.05-pixel intermediate polyline error control. Source hard-corner detection uses a 2-pixel arclength window and 60-degree threshold. A hard-corner loop bypasses periodic smoothing and retains distinct incoming/outgoing tangents.
- At most four fit passes: halve RMS per pass and select the **first** final line/arc boundary whose conservative two-sided enclosure against the original cell boundary is <= 1 pixel. Continuous spline evaluation permits subdivision below the initial sampling interval. Failure to converge/certify, resource exhaustion or incompatible geometry fails; no radius or fidelity score is consulted to select a fit.
- Final source-deviation budget is 1.5 mm, using the existing conservative native contour certificate and 0.005-mm flattening tolerance. These are distinct from the independently scored fidelity legs. Pixel sampling/smoothing/error settings are dev-authored algorithm controls, not new user tolerances.

Order:

1. Decode and threshold the unchanged source; trace its exact closed unit-cell union in pixel coordinates.
2. Perform the declared boundary approximation **in pixel units**. Preserve one outer loop, hole nesting and topology; reject disconnected islands and diagonal/nonmanifold contacts.
3. Compute exact line/arc extrema of the final fitted canonical boundary.
4. Uniformly scale by `50 / fitted_Y_extent` and translate its lower-left to the declared canonical origin. Aspect is preserved by one scalar, not independent X/Y fitting.
5. Apply the **same affine registration** to both original pixel-mask cell boundaries and canonical curves. Persist its derived scale/origin in `pixel_to_mm`; validate by deterministic re-derivation from mask and recipe.
6. Both fidelity legs use this committed registration and the fixed output placement. There is no candidate-bbox alignment or normalization after scoring.

The new fitting module accepts no min-R/cutter-radius argument. Actual native R >= 0.25 mm and existing disk-center access checks remain independent gates. A genuinely sharp dev notch stays R=0 and fails the actual native radius judge; it is not silently rounded. Existing checker buffers are measurement operations, not modifications to candidate geometry.

## Implementation files

- `tools/cad_verify_v4_biarcs.py`: source-local periodic cubic fitting, bounded source-error refinement, shared-tangent biarc construction and conservative two-sided enclosure. Lazy native numerical dependencies; no provider access.
- `tools/cad_verify_v4_contours.py`: strict fit/scale admission, canonical-final-height derivation, one source/contour registration, exact regeneration/hash closure and processing provenance including SciPy version.
- `schemas/contour-recipe.schema.json`: mutually exclusive fixed-pixel and canonical-final-height scale modes and closed approximation controls. `schemas/contour.schema.json` references that shared recipe schema instead of maintaining a divergent embedded copy; admits the explicit fit/order provenance.
- `tools/cad_verify_v4_c2_recipe.py`, the two registered JSON files, and `tools/cad_verify_v4_s1.py`: host-safe registered-resource validation and implementation inventory integration.
- `skills/cad-harness-v4/contracts-c-s1.md`: production registration, alpha semantics, approximation/scale order, solver boundary and C2 cohort retirement. Generator construction and no-file-read permissions are unchanged.
- `design/cad-harness-verify-v4/dev-c2-production/generate.py`: independent sources and genuine bare/harness native artifacts. No analytic-prepared substitute for production raster preparation.
- `tools/test_verify_v4_c2_recipe.py`, `tools/test_verify_v4_c2_recipe_native.py`: six host and eight native behavior tests. `tools/test_verify_v4_integrated.py` now supplies the real public production policy resources in its otherwise synthetic isolated lock repository.

## Independent fixtures and tests

RGBA sources are authored from independent analytic pixel geometry using deterministic 8x8 area supersampling: annulus, ellipse, rounded rectangle, sharp concave/convex notch, alpha 127/128/129 boundary, empty mask, disconnected island, diagonal contact, invisible-RGB variant and transparently padded annulus. No attachment or private outcome informed these sources or settings.

Native tests cover deterministic derivation/hash closure and self-consistently rehashed tampering; alpha threshold/invisible-RGB semantics; fitting before final-height scaling; uniform aspect/source mapping; padding invariance; preserved sharp corners and actual R failure; holes/islands/empty/nonmanifold boundaries; valid single-solid native/STEP output and operative editable parameters; and rejection of translated/scaled candidates under the fixed registration. Smooth proof outputs must pass actual native radius and tool-access checks, not merely avoid exceptions.

The first complete run exposed a padding-conditioning defect and a rounded-rectangle approximation failure in the new tests; all original 103 native tests passed. Fixes were source-local fitting, bounded original-boundary-error refinement and continuous subinterval evaluation, not weaker criteria. The failing-before/passing-after tests remain. Historical failed runs and full streams are retained, not reused as proof.

Final complete baseline-plus-new suites:

| Suite | Run | Passed | Skipped | Failures/errors | Exit | Unittest elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Existing 177 host tests + 6 new C2 host tests | 183 | 182 | 1 | 0 | 0 | 93.706 s |
| Existing 103 native tests + 8 new C2 native tests | 111 | 111 | 0 | 0 | 0 | 278.660 s |

The host skip is the existing Windows symlink-permission case. Native suite uses the pinned Python 3.11.14 / FreeCAD 1.1.4 interpreter. All original suite modules remain included. Exact complete argv and native fixture/guard environment are in `reports/verify-v4-c2-production-20261014T171741Z/suite-commands.json`; `host-final.event.json` and `native-final.event.json` bind full stdout/stderr and process metadata. Native flags include `CAD_VERIFY_C2_RECIPE_NATIVE=1` plus all original S1/S2/S3/artifact guards. Final logs are `host-final.stderr.log` and `native-final.stderr.log` in the same directory.

## Actual CLI and neutral C2 proof

Evidence root: `reports/verify-v4-c2-production-20261014T171741Z/`.

Fresh `fixtures-final/` contains production-prepared RGBA annulus, source manifest, fixed checker card/context and both artifact bundles. Bare construction is an independently authored ordinary Sketcher circle-pair plus C++ Pad: center (25,25), radii 25 and 25*20/48 mm, thickness 3 mm. It consumes neither a harness plan nor the fitted contour. Harness construction extrudes the actual production-derived contour at scale 1/origin (0,0,0), thickness 3 mm. Both are saved/reopened native documents and independent STEP files; real parameter edits must alter the output and restore it.

The existing CLI was exercised, not just unit helpers:

```text
python -B -m tools.eval_verify_v4 image-to-contour --profile c-s1 --input-manifest <fixtures-final/manifest.json> --asset-id ring --recipe design/cad-harness-verify-v4/c2-production-recipe.json --run-dir <evidence/production-image-cli-final>
python -B -m tools.eval_verify_v4 judge-artifacts --profile c-s1 --input-manifest <fixtures-final/manifest.json> --prepared <fixtures-final/prepared.json> --card <fixtures-final/card.json> --context <fixtures-final/context.json> --artifact-bundle <fixtures-final/{bare,harness}/artifacts.json> --run-dir <evidence/neutral-{bare,harness}-final>
```

The brace notation denotes the two actual separate calls; exact expanded argv are retained in their event JSONs. The production CLI returned PASS/exit 0, and its entire prepared packet exactly equals the proof's declared prepared packet. Both neutral calls returned PASS/exit 0, with **all 10 criteria passing on each of FCStd and STEP**. Owned native processes ran headless, stdin closed; documents closed; implementation/runtime checks and full native streams/ledger retained.

The table uses the **worst conservative bound across native and STEP**, not nominal values:

| Actual metric | Fixed gate | Bare | Harness |
| --- | ---: | ---: | ---: |
| Image -> contour IoU lower | >= 0.90 | 0.9865965573633074 | 0.9865965573633074 |
| Image -> contour Hausdorff upper, mm | <= 1.5 | 0.32872179094523224 | 0.32872179094523224 |
| Contour -> output IoU lower | >= 0.92 | 0.990351346151347 | 0.9999725936692896 |
| Contour -> output Hausdorff upper, mm | <= 1.0 | 0.20977110632697557 | 0.01019302577953781 |
| Actual minimum radius lower, mm | >= 0.25 | 10.416656666666663 | 1.645392554007554 |
| Disk-center uncovered area upper, mm2 | <= 0.1, independent DEV control | 0.04829564894114607 | 0.04821819774522534 |

Source/output topology both have one component and one hole. Final canonical Y extent is 50.000000000000014 mm (floating-point residual only); there is no subsequent normalization. The single source transform is scale 0.5197246358400207 mm/pixel, bottom-left image origin (-8.263462264610608,-8.262378011915581) mm; checker top-left registration is derived from that same transform, not refitted to either candidate.

Dev uncertainty controls are explicitly recorded in `fixtures-final/expected.json`: linear 1e-5 mm, curve 1e-4 mm, sampling 0.02 mm, angular 1e-6 rad, area 1e-5 mm2, disk-buffer segments 128, native bounds difference 1e-5 mm and volume difference 0.01 mm3. They are not newly chosen user tolerances. `require_connected=False` makes **no disk-center connectedness claim**: the current global convex-erosion certificate does not cover an annulus. Output topology and both fidelity-leg topology checks still apply. This is planar disk-center coverage, not a CAM/physical machining guarantee.

The first pair of CLI checks correctly stopped on implementation drift when `PLAN-V4-ADDENDUM-C.md` changed during execution. Fresh-process inventory comparison identified only that authoritative document delta; no guard was weakened. Those directories are historical failures. The final pair used fresh output directories and identical implementation bindings. See `intervening-implementation-change.json`.

Durable C2-only proof index: `reports/verify-v4-c2-production-20261014T171741Z/neutral-proof-c2.json`, SHA-256 `044cfe432aec21c1a05e8baab048f56cdbe74ce746596efff3c78131580a28f9`. It binds both result/summary/ledger/runtime files, input/card/context, artifact bundles, registered recipe and final command events. Final result locations are `neutral-bare-final/native/result.json` and `neutral-harness-final/native/result.json`. This index is explicitly **not** the complete C1-C5 integrated proof or a live manifest.

## Limits and freeze handoff

No guarantee that an unseen image is one connected manufacturable part, has sufficient actual R/tool access, preserves topology under this approximation or passes either fidelity gate. Uncertifiable geometry, missing controls and exhausted resources do not become PASS. Genuine hard corners, thin features, ambiguous contacts or unsupported tool-center connectedness can fail or remain UNVERIFIED; no input-specific repair is added.

Prior integrated locks do not cover these source/resource changes. The relay must bind the final committed implementation/skill/recipe/judges and current neutral evidence in the operative integrated lock before any live call. C2 holdout items and benchmark pairs from the previous lock remain retired; fresh blind C2 authoring follows the recipe freeze. Other families' definitions are unchanged. This task did not author or inspect holdout cases.

Custodian-only U5 execution remains outside this task; sol does not see its pixels or results. Under current C-R5v2/C-EXIT, U5 failure cannot pass this cycle or permit v4 exit; a next cycle requires fresh dev fixes, a new lock/manifest and fresh blind changed-family holdouts. Cycle results are retained and never combined. No retuning on the custodian outcome. `authorization: null`; `final_v4_ready: false`.
