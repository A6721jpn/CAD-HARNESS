# CAD-HARNESS VERIFY v2 R1 — Gemini Proposal

## 1. Probe Driving & Construction Dimension Resolution
- **Problem**: v1 `cad_verify_probe.py` only collected construction dimensions referenced via `ReferenceAxis`, discarding valid construction pitch circles (e.g., V5 PCD60 constrained via `PointOnObject`).
- **Fix Design**: Treat construction geometry entity $G_c$ as consumed/active in sketch $S$ if and only if:
  1. It is directly referenced by feature `ReferenceAxis` (existing behavior), OR
  2. It has an active driving constraint connecting it to at least one non-construction (real) geometry entity in $S$ (e.g., `PointOnObject`, `Coincident`, `Tangent`).
- **Decoy Rejection**: Pure construction entities isolated from real geometries (or forming closed loops with zero constraint link to real shape boundaries) remain unconsumed and cannot supply driving dimensions.

## 2. Budget Split: Parse Repair vs. CAD Repair
- **Problem**: v1 shared a 3-call budget across interpretation, parse repair, source fallback, and CAD repair. Out-of-schema fallback exhausted all 3 calls, starving CAD diagnostic repair.
- **Fix Design**: Enforce a two-phase budget per run (retaining the 900s / run wallclock limit):
  - **Generation Budget** (Phase A): Max 3 Sol calls (1 interpretation + max 1 parse repair + 1 fallback source). If generation fails schema/syntax after 1 parse repair, terminate.
  - **CAD Repair Budget** (Phase B): Guaranteed 2 dedicated repair calls invoked *only* after a settled CAD attempt failure (`geometry_ok == False` or `native_valid == False`).
  - **Hard Cap**: Max 5 Sol calls per run. Clean runs use 1–2 calls; F1/F2 and broken runs are guaranteed $\ge 1$ diagnostic repair call with live feedback.

## 3. Clarify-Answer-to-Completion Measurement
- **Turn 1 (Ambiguity Gate)**: Identical to v1. Sol returns `needs_clarification` on Q2/Q3 without CAD (`cad_attempts=0`). Evaluated against frozen rubric (unchanged bar metric: $\ge 4/5$, 0 inventions).
- **Turn 2 (Completion Telemetry)**: Provide deterministic, frozen user response (e.g., Q2: `厚さ12mm`, Q3: `穴中心(±20,0)`). Sol invoked for follow-up build.
- **Reporting Separation**: Turn 2 runs full FreeCAD verify-v1 gates against companion gold. Reported as secondary metric `clarify_completion_pass`; does not alter the core v1 bar.

## 4. N per Class & Fresh Holdout Items
- **Sample Sizes (Unchanged Bar Cohort)**:
  - V1–V5: $N=2$ each (10 runs, bar $\ge 8/10$, each $\ge 1/2$) | V6: $N=3$ (bar $\ge 2/3$) | S1: $N=5$ (bar $\ge 4/5$).
  - Q1: $N=3$ (bar $\ge 2/3$) | Q2: $N=5$ (bar $\ge 4/5$) | Q3: $N=5$ (bar $\ge 4/5$).
  - Faults F1–F3: $N=2$ each (6 episodes, established/detected 6/6, final repair $\ge 4/6$, each $\ge 1/2$).
  - Regressions: eval-v1 fresh $N=10$ (bar $\ge 8/10$, each $\ge 1/2$) | legacy A/B $N=4$ (bar 4/4).
  - Optional follow-up completions: Q2/Q3 Turn 2 ($N=5$ each, reported separately).
- **Holdout Corpus (`v2/test/`)**:
  - **V1 (Roller)**: OD 36, ID 10, L 40, circumferential groove Z=16..22, W 6, radial depth 3.
  - **V2 (Taper)**: Rectangular solid taper, Z=0 is 48×32, Z=36 is 30×20, centered.
  - **V3 (Pipe)**: XY 90° pipe, R30 centerline, OD 14, ID 10, (0,0,0) +X to (30,30,0) +Y.
  - **V4 (Ribbed Box)**: Outer 70×50×24, wall/bottom 4, triangular rib along XZ, rib Y-width 4.
  - **V5 (Flange)**: OD 90, thickness 10, center dia 24, PCD 68 with 6× dia 6 holes, 2 key slots.
  - **V6 (Plate)**: 120×80×14, 2 pockets 30×20×6, 8× dia 5 holes, top outer chamfer C1.0.
  - **S1 (Filleted Block)**: 64×46×18, pocket 20×16×5, top 4 edges R2.5, sharp vertical edges.
  - **Q1**: 75×45×12 plate with center hole dia 10 (defaults XY center, bottom Z=0).
  - **Q2**: 90×45 plate with 4 corner holes dia 5, missing thickness (follow-up answer: 12 mm).
  - **Q3**: 65×45×12 plate with 2 holes dia 7, missing positions (follow-up answer: (±20,0)).
  - **F1**: V1 source with groove omitted | **F2**: V5 source with 1 PCD hole omitted | **F3**: V6 spec with 1 hole dia 5→7.
- **Authoring & Freeze**: Hand-authored positive/negative native sources and analytic gold. Frozen in `design/cad-harness-verify-v2/test/` before any Sol run. v1 items demoted to `v2/dev/`.

## 5. Execution Plan, Budgets & Risks
- **Run Order**: Dev pilot (3 runs) $\to$ Legacy A/B (4 runs) $\to$ Fresh eval-v1 (10 runs) $\to$ Clean geometry V1–V6, S1 (18 runs) $\to$ Clarification Q1–Q3 (13 runs) $\to$ Faults F1–F3 (6 runs) $\to$ Optional Q2/Q3 Turn 2 (10 runs) $\to$ Independent aggregate.
- **Sol Call Budget**:
  - Planned minimum: 4 (dev) + 0 (legacy) + 10 (eval-v1) + 23 (clean) + 13 (Q) + 14 (F) = 64 calls (+10 follow-up = 74 calls).
  - Maximum hard cap: 4 (dev) + 30 (eval-v1) + 54 (clean) + 21 (Q) + 30 (F) + 20 (follow-up) = 159 calls.
  - Quota impact: Expected ~75–95 real calls (~2.5–3.2M input tokens, ~10–13% weekly quota, safe below 55% soft stop).
  - Wallclock: ~45–60 min total, monotonic clock well within 10800s (3h).
- **Risks & Mitigations**:
  1. *Constraint Graph Leak*: Over-permissive construction detection could accept decoupled decoys. *Mitigation*: Require bipartite path connecting construction entity to a real geometric entity via driving constraints.
  2. *Phase B Call Bloat*: Runaway repair loops on unfixable syntax. *Mitigation*: Cap generation at 3 calls; allow Phase B repair only after successful CAD attempt generation with settled diagnostics.
  3. *Clarification State Bleed*: Follow-up answer contaminating initial ambiguity score. *Mitigation*: Evaluate and record Turn 1 first-response artifact to disk before injecting Turn 2 user response.

R1 DONE
