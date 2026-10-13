# VERIFY v3 BRIEF (2026-10-13). Bar unchanged from PLAN-CONSENSUS.md.

v2 result: design\cad-harness-verify-v2\RESULTS.md and RESULTS-CONSENSUS.md. The bar is unmet only on source (W1 0/2) and faults (K1 0/2).
Root cause: the editability gate requires a direct driving value of 34, which is a derived diameter. The model drives the user-stated depth of 3 instead. Geometry passes. Secondary: the first response invents a stepped_shaft spec, which burns parse budget. Diagnostics: the final "verification" label hides that the failure was pre-export.

## Constraints
- Fresh holdout only. Author and freeze it before any Sol call. Do not use v1 or v2 test items for scoring, and do not tune on them.
- FreeCAD 1.1.4 headless only. No CAE. No invented numbers. New output files only.
- The quota guard is unchanged: 55% soft stop, 60% hard stop. The call cap is set explicitly.

## Ask (r1)
Propose a minimal v3 fix set: (1) editability semantics that accept equivalent driving representations of the requested dimensions; calibrate offline on dev/decoys only. (2) Unsupported-family routing and repair instructions. (3) Failure-phase diagnostics. Also give the fresh holdout design: items, reps, and which bar cohorts it covers.
State what you would NOT change. Write to design\cad-harness-verify-v3\<you>-r1.md only.
