# C-R8 — v4grok

Verdict: **SIGN**

Reviewed `PLAN-V4-ADDENDUM-C.md:145-149`. No other edit, no commit, no live call. No new user value. This sign authorizes no live run, no pilot, no operative lock, and no retirement of the cycle-2 cohort. It does not decide whether stress cases 02 and 10 were intended feasible; that confirmation belongs to the suite author.

## Fact

SIGN. `impl-notes-c2-cycle3.md:13` matches the locked inspection. `reports/verify-v4-c2-cycle3-20261014T202701Z/inspect-locked-source.stdout:2` and `:10` record `case02_sharp_corners` and `case10_mixed_crescent_stars` with error `contour_nonmanifold_pixel_contact` and no loops. The same two ids fail again in `source-fit-preflight.stdout:2` and `:10`, each in about 0.031 s, with that same error. The exact-cell tracer raises `contour_nonmanifold_pixel_contact` when a boundary vertex already has a successor (`tools/cad_verify_v4_contours.py:32-33`, `:381-387`). Its extraction text calls those diagonal contacts (`tools/cad_verify_v4_contours.py:889`). That raise is in the mask tracer, before any curve fit. `design/cad-harness-verify-v4/dev-c2-stress/manifest.json` has `cases_count` 14 and, for case 02 (`:17-26`) and case 10 (`:97-106`), only id, filename, category, description, size, and hash. It states no expected outcome for corner contacts.

The same preflight also records later fit failures on other cases. `PLAN-V4-ADDENDUM-C.md:146` does not claim those are cleared.

## Connectivity

SIGN. `PLAN-V4-ADDENDUM-C.md:147` declares 4-connected foreground in the cycle-3 recipe, applied to every image that recipe traces. A corner-only contact becomes separate boundary vertices and separate loops or pieces. An 8-connected join stays forbidden. That matches C-R6 (`PLAN-V4-ADDENDUM-C.md:134`) and C-R7 (`PLAN-V4-ADDENDUM-C.md:141`). The current tracer refuses the contact; this clause replaces that refusal with the split. It is one recipe rule, not a per-case waiver and not a U5-pixel tune.

## Pinch opening

SIGN, with this reading. `PLAN-V4-ADDENDUM-C.md:148` allows the certified fit to open the split pinch by removing material, inside the existing C-D(a) mask-to-contour bound, Hausdorff <= 1.5 mm and IoU >= 0.90 (`PLAN-V4-ADDENDUM-C.md:98`). R >= 0.25 mm remains the check on the final part. Contour-to-CAD stays IoU >= 0.92 and Hausdorff <= 1.0 mm (`PLAN-V4-ADDENDUM-C.md:98`). Topology is the declared 4-connected topology. If the bound cannot be met, the case is a stress FAIL under a specific refusal code. The case stays in the suite. This is the C-R7 certified fallback (`PLAN-V4-ADDENDUM-C.md:141-142`), declared in the recipe. It is not a fillet or buffer added after scoring, and it is not a silent deletion (`PLAN-V4-ADDENDUM-C.md:52`, `:126`).

## Gate

SIGN, with this reading. The suite stays 14 cases (`dev-c2-stress/manifest.json:4`). `PLAN-V4-ADDENDUM-C.md:149` keeps the C-R7 rule that every stress case passes before the custodian U5 run (`PLAN-V4-ADDENDUM-C.md:140`). The default expected outcome is a geometric pass. If the suite author marks a case deliberately infeasible, the expected outcome becomes refusal only through a manifest amendment that is committed and hash-locked again before sol finalizes the recipe (`PLAN-V4-ADDENDUM-C.md:140`, `:143`) and before sol's final run. That amendment is not a deletion and not a change after the final run.

No live calls, CAD, or commit.
