# C-R7 — v4grok

Verdict: **SIGN**

Reviewed `PLAN-V4-ADDENDUM-C.md:138-144`. No other edit, no commit, no live call. No new user value. This sign authorizes no live run, no pilot, no operative lock, and no retirement of the cycle-2 cohort.

## Closure

SIGN. `PLAN-V4-ADDENDUM-C.md:139` says the cycle-2 C2 cohort stays active until v4grok retires it when authoring the cycle-3 cohort. `holdout-families-commitment.md:121` names that cohort the active cohort, on the same ids and the same signed strata. The retired cohort at `retired-c2-cycle1/` is the cycle-1 fresh cohort (`holdout-families-commitment.md:119`). The fresh C2 cohort in `PLAN-V4-ADDENDUM-C.md:144` is that later retirement.

Cycle 2 is closed before the freeze. Spend is 0 generation calls and 0 judge calls. `holdout-families-commitment.md:3` and `:7` record `live_calls` 0. The one custodian run records `live_calls` 0 and `live_cad_runs` 0 (`pilot-bundle-commitment.md:124`). Commit `2e64c2bb6344b91342a7f142e72b41020f0c429f` holds the public cycle-2 commitment and pilot v3. Sealed holdout bytes stay private and are outside that commit. C-R4 (`PLAN-V4-ADDENDUM-C.md:116`) still requires the operative lock to be re-issued at the final freeze. The sentence "Fix per v4grok C-R7 BLOCK" cites the prior verdict on the retired-cohort wording.

## U5 fact

SIGN. `PLAN-V4-ADDENDUM-C.md:139` matches the one cycle-2 run. The abbreviation `0b6d09b6...7e04` is `c2-production-recipe-cycle2.json`, SHA-256 `0b6d09b67c67a050de5247e9c28f95abc454ee33b2c8cef604f5839ea7dc7e04`, 847 bytes (`pilot-bundle-commitment.md:110-112`). `pilot-bundle-commitment.md:120-122` records one invocation, exit code 1, worker status `FAIL`, error `contour_curve_fit_error_budget_unattainable`. No contour, mask, registration, piece count, fidelity leg, or min-R report was produced (`pilot-bundle-commitment.md:125-131`). This cycle's result is that worker failure. `INCOMPLETE` stays reserved for `budget_exhausted` or `quota_stop` (`PLAN-V4-ADDENDUM-C.md:30`, `:129`).

## Stress suite

SIGN. `PLAN-V4-ADDENDUM-C.md:140` pre-registers a generic agent-made raster suite and hash-locks it before the cycle-3 recipe is finalized. Nothing is taken from U5. The recipe must pass every case on both C-D(a) fidelity legs, min-R and tool access on the actual output, valid solids, and both neutral-checker arms (bare and harness) before the custodian U5 run. Those gates are the existing ones (`PLAN-V4-ADDENDUM-C.md:98`; `impl-notes-c2-multipiece.md:16`). `PLAN-V4-ADDENDUM-C.md:143` assigns authorship: gemini authors and hash-locks that suite before sol finalizes the recipe, and sol may use the locked suite as a dev gate. This adds no user dimension.

## Fit budget

SIGN, with this reading. `DECISIONS.md:61` says the logo only needs to match roughly and that model correctness matters more. `PLAN-V4-ADDENDUM-C.md:141` uses that decision. The cycle-2 recipe's source limit is `maximum_error_pixels` 1.0, and it also has `biarc_error_pixels` 0.05 (`c2-production-recipe-cycle2.json:18`, `:21`). The worker raises `contour_curve_fit_error_budget_unattainable` when the active fit limit cannot be met (`tools/cad_verify_v4_biarcs.py:179`). The pilot record leaves which of those two pixel limits fired unstated. The certified fallback is accepted or refused by the C-D(a) mask-to-contour bound, Hausdorff <= 1.5 mm and IoU >= 0.90 (`PLAN-V4-ADDENDUM-C.md:98`, `:141`). Contour-to-CAD stays IoU >= 0.92 and Hausdorff <= 1.0 mm (`PLAN-V4-ADDENDUM-C.md:98`). The stress suite still requires both legs (`PLAN-V4-ADDENDUM-C.md:140`).

Kept, and unchanged here: final canonical height 50 mm (`PLAN-V4-ADDENDUM-C.md:111`), one registration for both legs (`PLAN-V4-ADDENDUM-C.md:127`), no rounding, filling, bridging, or buffering (`PLAN-V4-ADDENDUM-C.md:126`; `c2-production-recipe-cycle2.json:29-30`), topology preserved, valid solids, and R >= 0.25 mm plus tool access on the actual output (`PLAN-V4-ADDENDUM-C.md:98`).

## Corner tension

SIGN. `PLAN-V4-ADDENDUM-C.md:142` matches the checker: a non-tangent corner has radius 0 (`tools/cad_verify_v4_contours.py:341-342`), so a raw pixel polyline fails R >= 0.25 mm on the actual part. The fallback has to pass that check inside the fidelity bound, or the case fails. Silent radius change after scoring stays forbidden (`PLAN-V4-ADDENDUM-C.md:52`, `:126`). The 0.25 mm figure is the existing check.

## Process

SIGN, with this reading. `PLAN-V4-ADDENDUM-C.md:144` has sol implement on generic fixtures only. Gemini reviews. The new recipe and the lock before v4grok's fresh blind C2 cohort are the pre-authoring lock (`PLAN-V4-ADDENDUM-C.md:54`). That lock binds authoring. Live authorization stays with the final operative lock (`PLAN-V4-ADDENDUM-C.md:116`). One custodian U5 run follows. The C-R4 combined commit and the final operative lock come before the quota check, live runs, and the pilot (`PLAN-V4-ADDENDUM-C.md:30`, `:116`). Other families' unrun cohorts stay carried forward and unscored (`PLAN-V4-ADDENDUM-C.md:55-56`, `:136`). Exit still requires all of U1-U5 on the new manifest (`PLAN-V4-ADDENDUM-C.md:17`, `:130`).

No live calls, CAD, or commit.
