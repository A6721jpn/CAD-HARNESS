# VERIFY v2 Results Review & Sign (Gemini, 2026-10-13 11:47 JST)

Reference:
- Document: [`design/cad-harness-verify-v2/RESULTS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/RESULTS.md)
- Report: [`reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json`](file:///C:/dev/CAD-HARNESS/reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json)
- W1/K1 Runs: [`reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r{1,2}-mvp1/`](file:///C:/dev/CAD-HARNESS/reports/cad-run/), [`reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r{1,2}-mvp1/`](file:///C:/dev/CAD-HARNESS/reports/cad-run/)

## Verdict: AGREE

Gemini agrees with `RESULTS.md` without reservation.

---

## Verification Rationale

### 1. Complete Numerical Verification Against Aggregate
Every figure, rate, Wilson 95% confidence interval, wall time triple (median / p95 / max), call count, token sum, and threshold flag in [`RESULTS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/RESULTS.md) matches [`reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json`](file:///C:/dev/CAD-HARNESS/reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json) exactly:
- **Suite & Core Totals**: 60/60 completed, `bar_met = false`, real Sol calls: 92 (budget 163), parse calls: 8, repair calls: 8, suite wall: 4083.625 s.
- **Cohort Table**: eval-v1 10/10 (72.2–100.0%), legacy 4/4 (51.0–100.0%), geometry 16/18 (67.2–96.9%), defaults/ambiguity 13/13 (77.2–100.0%), faults 4/6 (30.0–90.3%), completion 6/6 (61.0–100.0%, outside bar), dev 2/3 (20.8–93.9%, unscored).
- **Part Table**: W1 0/2 (0.0–65.8%), W2–W5 2/2 (34.2–100.0%), W6 3/3 (43.8–100.0%), S2 5/5 (56.6–100.0%), A1 3/3 (43.8–100.0%), A2–A3 5/5 (56.6–100.0%), K1 0/2 (0.0–65.8%), K2–K3 2/2 (34.2–100.0%), C2–C3 3/3 (43.8–100.0%).
- **Provider Usage**: Token counts per suite are identical to the report sums; legacy preserves `null` across all fields.
- **Bar Verdicts**: `source = UNMET` (due to W1 0/2), `faults = UNMET` (due to K1 0/2), all other 6 component thresholds `MET`. Scored failure distribution correctly totals `verification: 4`.

### 2. W1 and K1 Root Cause Verification
Inspection of the underlying episode artifacts ([`driver-run.json`](file:///C:/dev/CAD-HARNESS/reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/driver-run.json), [`a2-mvp1/result.json`](file:///C:/dev/CAD-HARNESS/reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/a2-mvp1/result.json), [`input-a2.py`](file:///C:/dev/CAD-HARNESS/reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/input-a2.py)) fully confirms the root-cause analysis:
- **Geometry Restored & Correct**: In all four repair attempts (W1 r1/r2, K1 r1/r2), final solid volume is $53758.93348822853 \text{ mm}^3$ (gold target: $53758.93348822854 \text{ mm}^3$, relative error $< 2 \times 10^{-16}$). Bounding box $[-20, 20, -20, 20, 0, 48]$, bore, shoulder, and section predicates all pass (`geometry_ok = true`).
- **Terminal Predicate**: The singular failure blocking `editability_ok` across all 4 episodes is `edit.driving_dimension.4` (expected key dimension 34 mm, actual None).
- **Representation vs. Target**:
  - The user prompt specified "半径深さ3" (radial depth 3).
  - The model generated native parametric sketches driving outer radius 20, width 8, and radial depth 3. In K1 r2, it explicitly connected a construction line of length 3 via `PointOnObject` between outer and inner groove circles, which the probe successfully traversed.
  - The groove inner diameter (34 mm) was therefore derived geometrically rather than directly dimensioned as 34 or 17.
  - Because the probe requires a direct driving dimension matching the gold entry (`[40, 10, 48, 8, 34]`), the check failed closed.
- **Attribution**: The conclusion that this failure represents sensitivity to parametric representation in the frozen editability gold contract—rather than a geometry arithmetic error, probe traversal bug, or harness crash—is rigorously substantiated by the evidence.
