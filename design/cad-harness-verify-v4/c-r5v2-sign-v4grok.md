# C-R5v2 — v4grok

Verdict: **SIGN**

Reviewed `PLAN-V4-ADDENDUM-C.md:123-129`. No other edit, no commit, no live call. No new user value. This signs the revised procedure. It does not sign recipe feasibility, a pilot outcome, or live authorization.

## Fact

SIGN. `PLAN-V4-ADDENDUM-C.md:123` voids C-R5. `:124` names `rounding-recipe` in intact bytes. The abbreviated SHA-256 `d0551190...300b` matches `reports/verify-v4-s1-dev-20261014T063456Z/fixtures/rounding-recipe.json`, whose full SHA-256 is `d0551190868dad359fe0d7ad9c0a1b883563488a7fbe0a735771ced8a8c2300b`. The disclosed substitution is `scale.mm_per_pixel` 0.25 to 0.05. Foreground luminance/dark/127, alpha `require-opaque`, and `radius_mm` 3 stayed unchanged. `pilot-bundle-commitment.md:14-28` records worker status `FAIL`, error `contour_nonopaque_image`, no mask, and no contour. History is that commitment plus `C:\dev\v4-holdout-private\pilot-v1\`. The attempt stays history and is not retried as-is. No C2 production recipe was registered.

## Recipe and scale

SIGN. `:126` authorizes one production recipe on independent dev fixtures, including transparent-background RGBA. The foreground choice is declared in that recipe. No fillet or buffer is added to satisfy minimum R. R >= 0.25 mm stays a check on the actual output with the existing tool-access checks (`PLAN-V4-ADDENDUM-C.md:98`, `c-d-proposal-sol.md:24`). Boundary approximation is only what the frozen recipe specifies, and both fidelity legs and topology still pass. No silent radius change (`PLAN-V4-ADDENDUM-C.md:52`).

`:127` sets nominal logo height at 50 mm as the final canonical contour's Y extent, aspect preserved (`PLAN-V4-ADDENDUM-C.md:76`, `:111`). The scale and approximation order is specified and tested on dev fixtures. One mask-to-world registration is committed for both fidelity legs. There is no renormalization after scoring.

## Revision, lock, and the one U5 run

SIGN. `:125` places this revision before the final freeze. No pilot, holdout, or benchmark run is authorized here. It is a pre-freeze implementation revision, not a C-R2-3 post-failure roster cycle (`PLAN-V4-ADDENDUM-C.md:53-56`). The final integrated lock binds the revised code, skill, recipe, and judges, plus a fresh independent neutral proof. The pre-authoring integrated lock at `:113` still has to bind that revised HEAD before fresh C2 authoring. C-R4 at `:116` does not replace that prerequisite.

`:129` gives the custodian one run of the frozen production recipe. Sol does not see U5 pixels or results. A failure keeps the worker status and error. U5 cannot pass in this cycle, so v4 cannot exit (`PLAN-V4-ADDENDUM-C.md:16`). There is no retuning. `INCOMPLETE` stays reserved for `budget_exhausted` and `quota_stop` (`PLAN-V4-ADDENDUM-C.md:30`).

## C2 replacement

SIGN, with this reading. `:128` retires the already authored C2 generative items and the C2 benchmark pairs, and keeps them as history. The fresh blind authoring replaces both sets. Signed counts stay in force: C2 generative 10 across the strata in `c-d-proposal-sol.md:55`, and 4 C2 benchmark pairs inside the 20-pair corpus (`PLAN-V4-ADDENDUM-C.md:112`). Family budgets stay 129 + 43. The benchmark envelope stays at most 160. The original 163-call holdout stays untouched (`PLAN-V4-ADDENDUM-C.md:45`). Other families stay in place. The four admission controls are outside this retirement.

No live calls, CAD, or commit.
