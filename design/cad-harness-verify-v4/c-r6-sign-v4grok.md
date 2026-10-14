# C-R6 — v4grok

Verdict: **SIGN**

Reviewed `PLAN-V4-ADDENDUM-C.md:132-137`. No other edit, no commit, no live call. No new user value. This signs the cycle-1 closure and the cycle-2 C2 rule. It does not authorize live runs, a pilot, or an operative lock.

## Closure

SIGN. `PLAN-V4-ADDENDUM-C.md:133` closes cycle 1 before the freeze. Spend is 0 generation calls and 0 judge calls. `holdout-families-commitment.md:7` and `:83` record `live_calls` 0, with authorization null and `final_v4_ready` false on the interim lock (`impl-notes-integrated-lock-head.md:13`). Both preparation runs record `live_calls` 0 and `live_cad_runs` 0 (`pilot-bundle-commitment.md:26`, `:80`).

The named records are the closed-cycle commit `8562af5f917677872a786a4c617a14630b8955a0`: the family holdout commitment, the C2 recipe, C-R4/C-R5/C-R5v2, both U5 preparation records, and the rubric work. That commit is not an operative lock. C-R4 (`PLAN-V4-ADDENDUM-C.md:116`) still requires the final lock to be re-issued against the later combined commit. Sealed holdout bytes stay private; they are not in that commit.

## Cause

SIGN. `PLAN-V4-ADDENDUM-C.md:134` matches the one production-recipe run. The abbreviation `ae1db1b4...af00` is `c2-production-recipe.json`, SHA-256 `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00`, 836 bytes. `pilot-bundle-commitment.md:77-78` records one invocation, exit code 1, worker status `FAIL`, error `contour_multiple_islands_one_solid_refused`. The recipe that ran has `topology.components` 1 and `islands` `reject` (`c2-production-recipe.json:36-39`; `pilot-bundle-commitment.md:71`). No contour, mask, registration, fidelity leg, or min-R report was produced (`pilot-bundle-commitment.md:81-86`). The earlier fixture failure stays the other preparation record: `FAIL` / `contour_nonopaque_image` (`pilot-bundle-commitment.md:24`). This cycle's result is that worker failure. It is not `INCOMPLETE` (`PLAN-V4-ADDENDUM-C.md:30`, `:129`).

## Cycle 2 geometry

SIGN, with this reading. `PLAN-V4-ADDENDUM-C.md:135` keeps a multi-piece foreground as separate pieces, each traced and extruded, all in one FCStd and STEP compound. Placement, nesting, and holes stay. No bridges, backing, or joins are added. Piece count is checked, and no count is set here. Both fidelity legs and min-R apply to every piece together. The existing thresholds stay: mask to contour IoU >= 0.90 and Hausdorff <= 1.5 mm; contour to CAD IoU >= 0.92 and Hausdorff <= 1.0 mm; R >= 0.25 mm on the actual output (`PLAN-V4-ADDENDUM-C.md:98`). Final canonical height, one mask-to-world registration, no fillet or buffer, and no renormalization after scoring stay (`PLAN-V4-ADDENDUM-C.md:111`, `:126-127`). The single-solid rule is relaxed only for this declared multi-piece C2 case. Every other family stays one solid.

## Process

SIGN, with this reading. `PLAN-V4-ADDENDUM-C.md:136` has sol implement on independent dev fixtures only, including multi-piece RGBA. Then a new C2 production recipe, a fresh neutral proof, a fresh blind C2 cohort from v4grok, and one custodian U5 run. Cycle-1 C2 cohorts stay retired. The C-R4 combined commit and the final lock come before live runs and the pilot (`PLAN-V4-ADDENDUM-C.md:116`). Changed-family fresh blind holdouts follow `PLAN-V4-ADDENDUM-C.md:130`. Other families' cycle-1 cohorts carry forward unrun and unscored; `live_calls` 0 means they were not scored and their successes are not combined (`PLAN-V4-ADDENDUM-C.md:55-56`). Exit still requires all of U1-U5 on the new manifest (`PLAN-V4-ADDENDUM-C.md:17`, `:130`). The custodian U5 step is preparation, not a generator, judge, or pilot call (`PLAN-V4-ADDENDUM-C.md:31`). A new cycle still needs its own budget and quota check before any live call (`PLAN-V4-ADDENDUM-C.md:30`).

## Open question

SIGN. `PLAN-V4-ADDENDUM-C.md:137` leaves bridges or a backing plate as a non-blocking question. `user-questions-morning.md:5` asks it and says the default proceeds. The default remains the separate-piece compound at `:135`.

No live calls, CAD, or commit.
