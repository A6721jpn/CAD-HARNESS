# VERIFY v3 implementation review

Read-only pass, 2026-10-13, against signed `PLAN-V3-CONSENSUS.md`. Uncommitted tree, read from the v3 modules and the `verify-v3` branches in `tools/cad_run.py`, `tools/cad_run_freecad.py`, and `tools/cad_verify_freecad.py`. No code edits. No FreeCAD, Sol, unittest, freeze, or git.

## Verdict

READY

MUST: none.

Analytic gold matches the frozen descriptions. Roller driving proof asks for the stated depth and width. The capability bypass is the single code `unsupported_shaft_operation`. Freeze and any holdout measurement stay stopped until the Gemini control files listed below are present and the new-dev calibration has passed. `require_controls` already raises `independent_native_controls_pending` for that handoff.

## Gold, re-derived from the descriptions

Tolerances in every geometry gold file are ±0.01 mm, axis 1e-6, and volume relative 1e-4. Stored `target_mm3` values match these closed forms in double precision. Suffixes follow the signed payload rule. 「寸法列はX×Y（3つ目はZ）。」 is absent. G3 and A4 omit 「XY中心、下面Z=0。」. F4/F5/F6 description bytes are the finished G1/G5/G6 bytes. C4/C5 gold descriptions are description + one LF + answer, and the binding block splits those hashes.

| ID | Re-derived volume | Stored target |
| --- | --- | --- |
| G1, F4 | `24432.5π` = `[(23²−7²)54−(23²−19.5²)10]π` | 76756.96250883261 |
| G2 | `44∫₀¹(56−28t)(36−18t)dt` = `44·56·36·(1−1/2+1/12)` | 51744 |
| G3 | `π(9²−6²)·38π/2` = `855π²` | 8438.5117629314 |
| G4 | `84·58·28−74·48·23+74·15·5/2` | 57495 |
| G5, F5 | `π(54²−13²−6·3.5²)·11−288` | 92101.52755309542 |
| G6, F6 | `112391.744−864π` | 109677.40794729843 |
| S3 | stock `74·54·14` on `[-37,37]×[-27,27]×[0,14]` | 55944 |
| A4 | `98·56·13−π·6²·13` | 69873.73463811997 |
| C4 | `88·52·12−4π·3.5²·12` | 53064.743519689204 |
| C5 | `84·50·10−2π·4²·10` | 40994.69035085127 |
| D1 | `7117.875π`, OD29 / bore7 / H37 / Z13..19 / depth1.25 | 22361.463809170447 |
| D2 | `62·44·11−π·3.75²·11` | 29522.03488639783 |
| depth_edit | `7039.875π` at depth 1.75, width 6, Z13..19 | 22116.419582190443 |
| width_edit | `7083.1875π` at depth 1.25, width 7, Z13..20 | 22252.48981399905 |

Sections and boxes match the same descriptions. G1 planes are Z11.5 / 28 / 43.5, with outer radius 23 outside the groove and 19.5 inside, bore radius 7. Bottom OD 39 is that geometric radius doubled. G2 sections are 56×36, 42×27, and 28×18, box half-extents 28×18×44. G3 box is `[0,47,−9,38,−9,9]`. G5 pockets are x −26..−14 and 14..26, y −25..−21, floor Z8; PCD centers are `(41 cos(kπ/3), 41 sin(kπ/3))`. G6 pockets are x −37..−13 and 13..37, y −8..8, floor Z11; six D6 holes sit at x ∈ {−34,0,34}, y ∈ {−25,25}. S3 fillet centers are (±34, 17) and (±24, 17); the Z18.5 outer offset is `1.5√3`. C4 centers are (±33, ±16). C5 centers are (±23, 0). D3, A5, and A6 have rubric only.

Fault solids, checked against the clean gold rather than stored as pass targets: F4 omits the groove and is larger by `1487.5π` (`25920π`). F5 omits the (41, 0) hole and is larger by `134.75π` (`29543.25π−288`). F6 changes only the (−34, −25) hole from D6 to D9 and is smaller by `180π` (`112391.744−1044π`). `test/F6/candidate.json` is that one-hole mutation of the G6 spec. F4 and F5 `candidate.py` files are absent.

Call sums in `run-order.json` and `expected_order()` are baseline 83, maximum 163, 60 episodes, and 51 scored rows. Order is dev3, legacy4, eval-v1 P1×2, P2×2, P4×2, P5×2, P3×2, then clean G/S, A, C, F.

## Requested roles and capability

Roller gold keys are outer diameter, bore, and length. Groove width and radial depth are separate roles (`axial_control`, `radial_control`). `load_gold` rejects a roller key list that includes the derived bottom diameter. `editability` clears that flat list and requires a proof for each of the five roles (`tools/cad_verify_v3_probe.py:392–402`).

Depth proof is a direct radial span between the outer and bottom boundaries, a radius difference, or half a diameter difference. Width proof is an operative pocket length, an axial boundary difference, or a centered half-width whose `Symmetric` constraint proves both boundaries and a driven center. Origin-only coordinates stay operands. Inoperative `Length2` is outside the roller proof. Expressions resolve one native constraint reference; other expression text yields no proof.

`interpretation` schema-checks first. The allowlist is exactly `unsupported_shaft_operation`, and only on a source route before the first CAD attempt (`tools/cad_verify_v3_agent.py:40–55`). The recorded origin is `model` or `validator`. G1–G5 and F4/F5 are source routes. G6, S3, A4, completion, and F6 are supported routes.

## Aligned

`cad_run.py` adds probe choice `verify-v3` and loads `cad_verify_v3_probe` for that profile. `cad_run_freecad.py` and `cad_verify_freecad.py` do the same. mvp-v1, verify-v1, and verify-v2 keep their own loaders. MVP episodes still call `cad_agent.run_mvp_driver`.

v3 geometry predicates are the existing roller, taper, elbow, ribbed-box, flange, and rect-prism checks, including S3 `volume_scope` and the local R3 section cuts. Reimport compares full FCStd and STEP volumes with each other. The S3 pass/fail volume remains the stock scope.

A probe miss sets `next_actor=sol` for verify-v3, including an in-schema editability miss (`cad_run_freecad.py:82–85`). `repair_reason` then allows one R. `repair_time_reservation_lost` becomes `episode_stop_reason` and leaves `stop_reason` empty, so later episodes can continue on the same clock (`eval_verify_v3.py:402–403`, `553`).

Stage labels are `geometry_pre_export`, `editability_pre_export`, `export_failure`, and `reimport_verification_fail`. Geometry wins when both geometry and editability fail. Unexecuted stages stay `not_reached` with null measurements. Export runs only after a probe pass.

Budgets are P1, R1, CAD2, source 4, spec 3, ask 1, completion 4, 450+450 inside 900, shared 10800, and call budget 1..163. Repair reserves R180 + unused P60 + build/export 90 + reimport 90 + cleanup 30. Initial cleanup reserve is 30 and FreeCAD is clipped at 300. Quota stops remain missing, invalid, future, age > 300, 55% soft, and 60% hard. An `-aggfix` version cannot start a live run. Aggregates use new `aggregate-verify-v3-<suffix>` names and exclusive create. `bar_met` requires 51 complete core rows and the unchanged thresholds. C and dev stay outside that flag. Wilson 95% uses z=1.96 on completed fixed cohorts.

Repair text names the equivalent driving forms and states that an unstated derived dimension is not an independent requirement. Initial context is the skill plus the generic contract. Source and repair calls archive prompt and context bytes beside the run, with paths and hashes in `driver-run.json`.

## NIT

1. `tools/cad_run.py:145`. The branch `probe_profile in ("verify-v2", "verify-v3")` loads the v2 probe. verify-v3 is already returned at lines 139–142, so this arm is the non-package verify-v2 loader.

2. `design/cad-harness-verify-v3/test/G5/gold.json`. Two PCD coordinates carry binary residuals near `1e-14` mm, inside the ±0.01 mm tolerance. The centers are `41·(cos(kπ/3), sin(kπ/3))`.

3. Non-roller editability still uses the v2 flat search, including a half-value match and `Length2` (`tools/cad_verify_v2_probe.py:144–163`). G6 therefore treats thickness 16 and pocket width 16 as the same flat value. Roller width and depth use the role proofs above. Plate, flange, pocket, and fillet geometry predicates still gate the solid.

## Gate before freeze

These required paths are absent: `tools/fixtures/verify_v3_native.py`, `test/F4/candidate.py`, `test/F5/candidate.py`, and `positive.py`, `negative.py`, and `offline.json` for G1–G6, S3, A4, C4, C5, F4, F5, and F6. `dev/native-matrix.json` and `dev/sources/` are present and use the D1 roller. This review did not execute those sources. `impl-notes.md` records the Sol-free unit and data-only checks; those counts were not re-run here.
