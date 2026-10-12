# CAD-HARNESS VERIFY — grok R1 validation plan

2026-10-12. Independent plan for BRIEF (a)–(i). No code, FreeCAD, or Sol was run. MVP baseline stays `reports/aggregate-mvp-eval-v1-r2.json`: 10/10, one Sol call each, wall 19.594–32.281 s, commit `f454e6c`. That file's usage totals are input 349105, cached input 216064, output 6574, reasoning output 3504. eval-v1 gold, the 8/10 and per-part 1/2 bar, legacy A/B probes, and `judge_stub` stay as signed. Verify numbers below are a plan, not a new measurement.

Schema today is `rect_prism` (one region), `rect_stack`, `stepped_shaft`, rectangular pockets, Z through-holes, and one `top_outer` fillet or chamfer. `mvp-v1` merges same-radius Z cylinders, treats every inward Z cylinder as a through hole, and fails on non-plane, non-Z-cylinder faces when no finish is requested. A groove, loft, sweep, shell, or blind hole cannot pass that probe even when the solid is right. Those parts get a new `verify-v1` profile. P1–P5 keep `mvp-v1`.

Sketches below are not the frozen strings. Freeze writes the verbatim text, display formulas, and SHA manifest before any Sol call. A typed fixture must match each formula first. A mismatch stops the suite. Gold is not edited to fit the solid.

## (a)(d) Suites and gold checks

Out of schema, so a valid `build_spec` cannot be the gold solid. A compiler-only pass is a fallback miss. N=2 because each run is an interpretation call plus a `build(doc)` call, and agent wall time is unmeasured.

| Id | Sketch | Gold checks |
| --- | --- | --- |
| V1 | Z pin, D24×40, bottom Z=0. Annular rectangular groove, floor D16, width 6, centered at Z=20. | bbox, volume `5280π`, unmerged outer cylinders, groove cylinder and its two annular shoulders. Display formula, not yet measured. |
| V2 | Loft along Z from a 30×20 rectangle at Z=0 to a 16×10 rectangle at Z=28, centered. | bbox, end sections, volume. Mid section recorded. Extra surfaces recorded, not failed as an unwanted fillet. |
| V3 | Sweep a 8×6 rectangle along a 90° arc, radius 25, in the XZ plane. | bbox, volume, end sections, arc-path sample points. Same surface policy as V2. |
| V4 | Open-top box, outer 60×40×30, wall and floor 3. | bbox, volume `60×40×30−54×34×27`, outer section, cavity points outside the solid, floor at Z=3. |
| V5 | Plate 80×50×12. Six blind D5 holes, depth 8, 2×3 grid, centers stated. | bbox, volume `48000−300π`, six blind holes (open at the top, closed at the floor, solid below). Zero through-holes. |

In schema, every dimension stated. Same one-run gates as DECISION-01: geometry, thin editability, FCStd and STEP reimport, close, cleanup, ≤3 Sol calls, ≤3 CAD attempts, ≤900 s. Volume relative 1e-4. Face and edge counts stay recorded only.

| Id | N | Sketch | Gold checks |
| --- | --- | --- | --- |
| C1 | 3 | Three stacked rectangular regions, two rectangular pockets, four through holes. No finish. | sections, pockets, holes, volume |
| C2 | 3 | One prism, one pocket, eight through holes, top-outer fillet. | pocket, holes, fillet, volume |
| S1 | 5 | One new prism, one pocket, top-outer fillet. Dimensions differ from P1–P5 and `H_LIVE_PROBE.txt`. | existing `mvp-v1` checks |

## (c) Ambiguity

The driver has no human reply channel. The user payload stays byte-identical, and `needs_clarification` currently consumes a call and retries. Q runs use a new flag `--stop-on-clarification`, default off. `eval_mvp.py` does not set it.

- Q1, N=3. "70×40×10 plate, one centered through hole, diameter 8." Origin omitted. Binding default is center XY and bottom Z=0. Pass is that default plus the geometry gates. A first-response clarification is `default_miss` even if a later call builds the solid.
- Q2, N=5. Plate 80×40, four corner holes, diameter and edge offsets stated, thickness omitted. No geometry gold.
- Q3, N=5. Plate 60×40×10, two D6 holes, positions omitted. No geometry gold.

Q2 and Q3 score the first response only. `ambiguity_ok` means `needs_clarification` naming the frozen missing slot, and no compiled number for that slot. A built solid is `invented_dimension`. Unsupported is not credit for a missing in-schema number.

## (b) Fault injection

Natural first-try repairs on C/V are tallied when they happen. If none happen, the natural repair rate is unobserved.

`--inject-fault`, default off, runs after the clean batches. It waits for the first schema-valid spec or contract-valid source, compiles one mutated copy, and returns the real probe's expected/actual on the normal repair path. Mutations are frozen: F1 multiplies one pocket depth by 2 (N=3, in-schema text that is not S1); F2 adds 1 mm to one hole diameter on a blind-hole text that is not V5 (N=2). The mutated attempt is `injected: true` and cannot pass. User-payload SHA is unchanged. Gold stays out of the first context.

`repair_success` = later attempt passes the full run gates, calls ≥ 2, and attempt 1 was a settled probe fail. `injection_not_reached` (invalid first output, or human/compiler/export/cleanup) is reported aside and is neither success nor model failure. A typed confirmed spec still does not call Sol.

## (e)(g) N, intervals, metrics

N=5 is only S1, Q2, and Q3. Fallback and injection stay at N=2 or 3 so the Sol bill stays inside a few hours. The aggregator reports a Wilson 95% interval (z=1.96) from that batch's passed and completed counts, per part and per suite. An incomplete batch has no interval. The interval is descriptive. It is not a claim about other JA/EN requests.

Each new aggregate records, per run: pass, geometry, editability, reimport, wall_s, Sol calls, CAD attempts, repair attempts, injected flag, first-response class, failure class, and provider `turn.completed` tokens. A missing usage field stays null. Failure classes stay the driver's: timeout, budget, compiler_native, launch, dialog, cleanup, verification, export, save, plus verify labels `fallback_miss`, `invented_dimension`, `default_miss`, `injection_not_reached`.

## (f)(h) Regression and holdout

`design/cad-harness-verify/dev/` holds typed fixtures and injector scratches. Dev Sol runs are capped at 4 and stay out of the rate. `test/` holds V, C, S, Q, and F text plus gold. Commit the SHA manifest before any test Sol. Compiler tests do not read `test/`. No skill, schema, gold, or description edit after that commit. A fix is a new directory version and a new aggregate. Old aggregates stay.

Before test Sol, compare skill, schema, `cad_agent.py`, `cad_spec.py`, and `cad_spec_probe.py` hashes with `aggregate-mvp-eval-v1-r2.json`. If they match, that aggregate is the regression record. If they differ, one new eval-v1 prefix, same gold and bar, is a separate aggregate. Legacy A/B stay on the existing unittests and fixtures, 0 Sol. Verify failures do not change eval-v1 tolerances.

## Budget, (i) stopping, practical

Planned test calls, expected path: V 5×2×2 = 20, C 6, S 5, Q 3+5+5 = 13 with the stop flag, F about 10. Dev cap 4. Total about 58, or about 68 if eval-v1 is repeated. Scale the r2 10-run usage totals by `planned_calls/10` only as a lower bound for short JSON calls. Source and repair calls are unmeasured and can be larger. Token-to-percent is not in the repo. BRIEF says weekly use is about 6% with a hard stop at 60%. The supervisor checks that host figure before every batch and does not start a batch at or above 60%.

Host wall cap for the whole verify execution is 3 hours, at a batch boundary. One run still dies at the existing 900 s cap and counts as a miss. No warm-up drop and no replacement. Two harness failures in a row (launch, export, reimport, cleanup) stop the version. The remaining batches are unmet.

After validation, "practical" means all of the following, and nothing more:

1. eval-v1 still meets the signed bar on unchanged gold.
2. Each V part has at least one full pass whose call log contains `kind=source` after `unsupported`.
3. The frozen injection set shows at least one `repair_success`. The rate is reported.
4. Q2 and Q3 report `ambiguity_ok` with Wilson intervals. Invention is visible.
5. C1, C2, and S1 report the DECISION-01 run gates on their own aggregates.

A miss on (2) or (3) means the path beyond the MVP schema is not yet practical. That result stands. It does not move the 8/10 bar, add an LLM judge, or make N=5 a general success rate.
