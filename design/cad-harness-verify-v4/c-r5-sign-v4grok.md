# C-R5 — v4grok

Verdict: **BLOCK**

Reviewed `PLAN-V4-ADDENDUM-C.md:119-121` (LF line breaks). No other edit, no commit, no live call. No new user value.

## Fact line

BLOCK. `PLAN-V4-ADDENDUM-C.md:120` contains a bare CR (`0x0D`) where the recipe name must read `rounding-recipe`. The bytes are `dev ` + CR + `ounding-recipe`. A `splitlines()` reader breaks the sentence there. The identifier to sign is `rounding-recipe`.

The failure citation is right. `pilot-bundle-commitment.md:22-24` records one invocation, exit code 1, status `FAIL`, error `contour_nonopaque_image`, and no contour. `pilot-user-requests.md:75` already records the attachment as RGBA. The dev file `reports/verify-v4-s1-dev-20261014T063456Z/fixtures/rounding-recipe.json` is a fixture recipe (SHA-256 `d0551190868dad359fe0d7ad9c0a1b883563488a7fbe0a735771ced8a8c2300b`). No separate C2 production recipe is registered.

The same fact must record the disclosed substitution. `pilot-bundle-commitment.md:14-16`: the run used that fixture with only `scale.mm_per_pixel` changed from `0.25` to `0.05`. Foreground stayed luminance/dark/127, alpha stayed `require-opaque`, rounding stayed allowed at `radius_mm` 3. `require-opaque` stopped the run before a mask or a contour. History is `pilot-bundle-commitment.md` plus `C:\dev\v4-holdout-private\pilot-v1\`. Keeping that attempt, and not retrying it as-is, is right.

## Production recipe

BLOCK on two clauses in `PLAN-V4-ADDENDUM-C.md:121`.

Scale. C-R3-1 (`PLAN-V4-ADDENDUM-C.md:111`) and C-U5 (`PLAN-V4-ADDENDUM-C.md:76`) define logo height as the committed contour's Y extent. `:121` sets scale from the foreground-mask Y extent. Those extents diverge as soon as a fillet is allowed. The 50 mm target stays the contour Y extent, aspect preserved.

Fillet. `:121` allows a fillet up to whatever minimum tool R 0.25 mm "requires". C-D(a) (`PLAN-V4-ADDENDUM-C.md:98`) and `c-d-proposal-sol.md:24` make R >= 0.25 mm a check on the actual output, with the existing tool-access checks. `c-d-proposal-sol.md:25` allows a boundary approximation only when the frozen recipe specifies it and both fidelity legs and topology still pass. C-R2-2 (`PLAN-V4-ADDENDUM-C.md:52`) does not allow a radius change. `u5-defaults-sol.md:22` blocks treating a buffer or fillet as proof of tool access. The production recipe does not gain a fillet in order to satisfy minimum R.

The rest of the rule can be signed once those clauses are corrected. One C2 production recipe, authored on independent dev fixtures that include transparent RGBA, then hash-frozen, then run once by the custodian. Sol does not open U5 pixels or fit thresholds to the U5 result. The public failure mode may motivate the recipe class; it does not supply parameters.

## Cycle outcome

BLOCK the C-R1-2 citation. `PLAN-V4-ADDENDUM-C.md:30` uses `INCOMPLETE` only for `budget_exhausted` or `quota_stop`. A contour CLI failure is the worker status and its error code, as in the first run (`FAIL` / `contour_nonopaque_image`). Stopping this cycle and not retuning matches C-R1-3 (`PLAN-V4-ADDENDUM-C.md:31`) and `c-d-proposal-sol.md:26`. It does not borrow the budget reason.

No live calls, CAD, or commit.
