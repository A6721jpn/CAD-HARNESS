# VERIFY v2 RESULTS

The practical bar is **unmet** (`bar_met=false`). Source and fault thresholds fail because W1 and K1 each finish 0/2. All other stored threshold flags are true. C2 and C3 each complete 3/3 and remain outside the bar.

Sources: [aggregate JSON](../../reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json), [suite-run.json](../../reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/suite-run.json), [plan.json](../../reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/plan.json), and [progress.jsonl](../../reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/progress.jsonl). Episode evidence below follows the run paths recorded in that suite. All numerical results are copied from those records or explicitly summed from their rows; this document does not re-score them.

## Measurement identity and completion

- Measurement: `verify-v2-reviewed-r1`, prefix `host-verify-v2-reviewed-r1`, implementation `1e93a1b`, plan `2159ce0`, original manifest digest `129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8`.
- Aggregation: `verify-v2-reviewed-r1-aggfix`, implementation `dd7225c`, manifest digest `b129072a9b1681795f6ec6339e6e6c808ec2a169c0b5acf2ac0708c058d8c999`; `aggregation_identity.run_manifest=design/cad-harness-verify-v2/SHA256.run-r1.json`. Top-level aggregate identity remains the original measurement.
- 60/60 episodes completed; `valid_suite`, `complete`, `core_complete`, `versions_consistent`, and `deadline_ok` are true; `stop_reason=null`.
- Suite-run wall: 4083.625 s. Real Sol calls: 92; recorded call budget: 163. Aggregate records 8 parse calls and 8 CAD repair calls. This documentation task made no new model/CAD calls or aggregate run.

Wilson intervals below are the aggregate's existing intervals, rounded to one decimal percent. Wall values are rounded to three decimals and include failures. Suite rows describe the stored cohorts; they do not establish a general CAD success probability. The part intervals show the uncertainty from the small fixed samples.

## Cohort results

| Cohort / part | Pass / N | Wilson 95% (%) | Wall median / p95 / max (s) | Sol calls | CAD attempts | Parse calls | CAD repair calls | Failure classes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| eval-v1 regression | 10/10 | 72.2–100.0 | 23.141 / 36.781 / 36.781 | 10 | 10 | 0 | 0 | — |
| legacy controls | 4/4 | 51.0–100.0 | 0.984 / 1.062 / 1.062 | 0 | 4 | 0 | 0 | — |
| geometry (W/S) | 16/18 | 67.2–96.9 | 87.414 / 234.719 / 234.719 | 34 | 20 | 4 | 2 | verification: 2 |
| defaults / ambiguity (A) | 13/13 | 77.2–100.0 | 21.907 / 30.500 / 30.500 | 13 | 3 | 0 | 0 | — |
| injected faults (K) | 4/6 | 30.0–90.3 | 254.359 / 355.500 / 355.500 | 20 | 12 | 4 | 6 | verification: 2 |
| C completion — outside bar | 6/6 | 61.0–100.0 | 47.907 / 53.422 / 53.422 | 12 | 6 | 0 | 0 | — |
| v1 dev previews — unscored | 2/3 | 20.8–93.9 | 33.703 / 33.891 / 33.891 | 3 | 0 | 0 | 0 | interpretation: 1 |

The dev row measures previews only: V1 fails interpretation, V6 passes the spec preview, and Q2 asks the required field. Its CAD attempt count is zero, and it contributes no score to the bar.

## Part results

| Cohort / part | Pass / N | Wilson 95% (%) | Wall median / p95 / max (s) | Sol calls | CAD attempts | Parse calls | CAD repair calls | Failure classes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| W1 | 0/2 | 0.0–65.8 | 234.523 / 234.719 / 234.719 | 8 | 4 | 2 | 2 | verification: 2 |
| W2 | 2/2 | 34.2–100.0 | 121.274 / 157.156 / 157.156 | 4 | 2 | 0 | 0 | — |
| W3 | 2/2 | 34.2–100.0 | 93.585 / 97.734 / 97.734 | 4 | 2 | 0 | 0 | — |
| W4 | 2/2 | 34.2–100.0 | 125.032 / 140.797 / 140.797 | 4 | 2 | 0 | 0 | — |
| W5 | 2/2 | 34.2–100.0 | 220.063 / 230.172 / 230.172 | 6 | 2 | 2 | 0 | — |
| W6 | 3/3 | 43.8–100.0 | 33.360 / 34.703 / 34.703 | 3 | 3 | 0 | 0 | — |
| S2 | 5/5 | 56.6–100.0 | 28.234 / 36.531 / 36.531 | 5 | 5 | 0 | 0 | — |
| A1 | 3/3 | 43.8–100.0 | 24.594 / 30.500 / 30.500 | 3 | 3 | 0 | 0 | — |
| A2 | 5/5 | 56.6–100.0 | 20.187 / 24.141 / 24.141 | 5 | 0 | 0 | 0 | — |
| A3 | 5/5 | 56.6–100.0 | 22.016 / 25.953 / 25.953 | 5 | 0 | 0 | 0 | — |
| K1 | 0/2 | 0.0–65.8 | 254.359 / 261.750 / 261.750 | 8 | 4 | 2 | 2 | verification: 2 |
| K2 | 2/2 | 34.2–100.0 | 348.399 / 355.500 / 355.500 | 8 | 4 | 2 | 2 | — |
| K3 | 2/2 | 34.2–100.0 | 66.813 / 67.766 / 67.766 | 4 | 4 | 0 | 2 | — |
| C2 — outside bar | 3/3 | 43.8–100.0 | 47.266 / 48.547 / 48.547 | 6 | 3 | 0 | 0 | — |
| C3 — outside bar | 3/3 | 43.8–100.0 | 50.890 / 53.422 / 53.422 | 6 | 3 | 0 | 0 | — |

The eval-v1 regression row above is 10/10, with P1–P5 each 2/2. Legacy 4/4 means both positive controls pass and both broken controls are correctly rejected.

## Provider usage

These are field sums already recorded per suite. Missing fields retain `null`; the legacy row is not converted to zero. Input, cached input, cache-write input, output, and reasoning output are kept as separate reported fields.

| Suite | Input tokens | Cached input | Cache-write input | Output tokens | Reasoning output |
| --- | --- | --- | --- | --- | --- |
| mvp | 349,147 | 192,768 | 0 | 6,460 | 3,297 |
| legacy | null | null | null | null | null |
| geometry | 1,147,607 | 588,800 | 0 | 56,403 | 37,694 |
| q | 455,914 | 285,568 | 0 | 6,052 | 4,225 |
| fault | 683,895 | 492,032 | 0 | 38,853 | 25,977 |
| completion | 403,251 | 319,616 | 0 | 6,214 | 4,062 |
| dev | 105,276 | 34,560 | 0 | 2,376 | 1,485 |

## Bar verdict

| Stored threshold | Verdict | Recorded evidence |
| --- | --- | --- |
| source | UNMET | W1–W5 sum to 8/10, but W1 is 0/2; W2–W5 are each 2/2. Source-route flags pass for W1–W5. |
| faults | UNMET | Final full gates 4/6; K1 0/2, K2 2/2, K3 2/2. Reach, establishment, and detection are each 6/6. |
| complex | MET | W6 3/3. |
| stock | MET | S2 5/5. |
| defaults | MET | A1 3/3. |
| ambiguity | MET | A2 5/5 and A3 5/5; critical-invention flags are false in all their episodes. |
| mvp | MET | eval-v1 regression 10/10, every part 2/2. |
| legacy | MET | Expected-control outcomes 4/4. |
| practical bar | UNMET | The source and fault flags are false despite complete, consistent, deadline-compliant records. |

C2 and C3 each have correct initial questions 3/3, completion 3/3, conditional completion after a correct question 3/3, and `not_reached=0`. Each completion Wilson interval is 43.8–100.0%. These results apply to the frozen-answer cohorts. Broader dialogue behavior remains unmeasured.

Natural repair is 0/2, eligible 2 and invoked 2, Wilson 0.0–65.8%; both eligible episodes are W1. Injected-fault repair reaches final full gates in 4/6, Wilson 30.0–90.3%; reach/establishment/detection each have Wilson 61.0–100.0%. K2 demonstrates successful source repair and K3 successful spec repair. All eligible W1/K episodes receive their repair call. The 8 parse calls are W1, W5, K1, and K2, one in each recorded round; they did not prevent the later W1/K repair calls.

The aggregate's scored failure distribution is `verification: 4`, split W1: 2 and K1: 2 (sum of the geometry and fault rows). Dev separately has `interpretation: 1`. The generic verification label needs the episode analysis below to identify the actual failed gate.

## W1 and K1 root cause

### What actually stopped verification

| Episode | Initial geometry | Repair geometry | Final failed check | Saved reimport outcome |
| --- | --- | --- | --- | --- |
| W1 r1 | pass | pass | `edit.driving_dimension.4`: expected 34, actual null | Not reached |
| W1 r2 | pass | pass | `edit.driving_dimension.4`: expected 34, actual null | Not reached |
| K1 r1 | fail: injected missing groove | pass | `edit.driving_dimension.4`: expected 34, actual null | Not reached |
| K1 r2 | fail: injected missing groove | pass | `edit.driving_dimension.4`: expected 34, actual null | Not reached |

Each final result has `failed_phase=probe`, `probe_status=predicate_fail`, `predicate_diff=["editability"]`, `geometry_ok=true`, `editability_ok=false`, and `verification_pass=false`. The worker events show every geometry predicate true and editability false. The model script completed, FreeCAD exited normally, the document closed, cleanup reports exited, and `native_valid=true`. A diagnostic FCStd was saved, but no STEP or independent verify-result artifact was produced, and `export_ms=null`. Thus these logs do not show a failed STEP/FCStd comparison: the pre-export editability gate blocked reaching it.

The final shape volume in every listed repair is 53758.93348822853 mm³ against logged gold 53758.93348822854 mm³. The final bounding box matches logged gold [-20,20,-20,20,0,48] mm. Section, shoulder, bore, and roller predicates also pass. The absence of the required direct driving value, rather than the shape geometry, is the terminal failure.

### Why the driving value is absent

The episode's copied gold asks for driving values [40,10,48,8,34]. The copied description specifies outer diameter 40, length 48, bore diameter 10, groove width 8, and **radial depth 3**. The 34 mm groove-bottom diameter is derived: outer radius 20 minus depth 3 gives radius 17, hence diameter 34. Its arithmetic is consistent with the logged shape.

The generated native histories instead drive the stated depth and outer radius. W1 r1/r2 repairs use a constrained rectangular groove section with outer-radius 20, radial-depth 3, and width 8. Their evidence lists those values on the used sketch, but no standalone 17 or 34 driving dimension. Renaming or restructuring native features during repair leaves this parameterization unchanged.

K1 r1 repairs with the same depth-driven groove representation. K1 r2 provides particularly clear evidence: its source ties the groove's outer radius to the stock radius using an expression, connects a construction depth line to the inner and outer circles, and drives that line to 3. The Probe's evidence actually reaches that construction line through `PointOnObject` and records the value 3. It nevertheless reports 34 missing, because deriving a dimension from other driving constraints is different from finding that dimension's direct value.

**Attribution:** the decisive task-level concern is representation sensitivity in the frozen editability gold/Probe contract. The logs support a correct native solid whose groove is controlled using the user-stated depth, rejected for lacking a direct derived diameter. They do not show a lost-link/reachability implementation exception or an arithmetic error in geometric gold. Under the literal frozen gate, the generated and repaired sources still miss a required value, so the recorded model-contract failures and scores stand. Broader parameter-change propagation has not been exercised here; `native_valid` and used driving constraints alone do not certify it.

### Model, prompt, and harness contributions

- **Model/schema:** all W1/K1 first responses invent a `stepped_shaft` build-spec representation and are recorded as invalid. The parse response then returns `unsupported`, and the source fallback runs. This is an observed model contract error and consumes parse budget; it is separate from the final editability failure.
- **Model repair:** each W1/K1 episode records one actual repair call and finishes `cad_repair_failed`. W1's geometry was already passing; K1's repairs restore the missing groove geometry in both episodes but retain the depth-driven representation rejected by the frozen gate.
- **Prompt attribution:** source/repair calls have context hashes, while the available driver log does not retain their complete context text. The records establish the returned representation and diagnostic target; they do not isolate inadequate prompt wording from failure to satisfy the literal target. Treat a prompt change as a candidate to test, rather than an established cause.
- **Harness:** no launch, cleanup, timeout, Probe exception, or uninvoked-repair stop explains these final misses. K1's initial failure is the intentional injection: both rounds record reached/injected/established/detected true and the candidate SHA as the executed source SHA. The missing groove produces volume 56548.667764616264 mm³ against 53758.93348822854, with section and shoulder failures. Its detection and repair launch worked. The broad final `verification` label obscures that the final failures occurred before export/reimport.
- **Scoring:** retain W1 0/2, K1 0/2, natural repair 0/2, and the unmet bar. Geometric restoration does not replace the frozen full-gate result.

### Episode evidence

- W1 r1: [driver](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/driver-run.json), [repair result](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/a2-mvp1/result.json), [repair source](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r1-mvp1/input-a2.py).
- W1 r2: [driver](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r2-mvp1/driver-run.json), [repair result](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r2-mvp1/a2-mvp1/result.json), [repair source](../../reports/cad-run/host-verify-v2-reviewed-r1-geometry-W1-r2-mvp1/input-a2.py).
- K1 r1: [driver/injection record](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r1-mvp1/driver-run.json), [injected result](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r1-mvp1/a1-mvp1/result.json), [repair result](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r1-mvp1/a2-mvp1/result.json), [repair source](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r1-mvp1/input-a2.py).
- K1 r2: [driver/injection record](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r2-mvp1/driver-run.json), [repair result](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r2-mvp1/a2-mvp1/result.json), [construction-depth source](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r2-mvp1/input-a2.py), [worker predicates](../../reports/cad-run/host-verify-v2-reviewed-r1-fault-K1-r2-mvp1/a2-mvp1/worker-events.jsonl).

## v3 fix candidates — each requires a fresh holdout

- **Editability semantics — fresh holdout required.** Author the next rubric around the dimensions actually requested, with feature-specific proof that driving constraints control the required geometry. Calibrate equivalent depth-driven and diameter-driven native representations, including expression and construction dependencies, against disconnected/reference/inactive decoys. Confirm behavior with deliberate parameter edits offline before freezing the new rubric and unseen items. Preserve v2 gold and results; avoid accepting arbitrary numerical combinations as dimension proof.
- **Supported-family routing and repair instructions — fresh holdout required.** Examine the exact contexts, strengthen early `unsupported` handling for unrepresentable shapes, and make repair instructions explain the failed native requirement using the returned evidence. Keep parse/repair accounting explicit and preserve actual repair opportunities. Evaluate on unseen shapes and dimensions so improvement is not measured on W1/K1 or other v2 items.
- **Failure diagnostics and prompt provenance — fresh holdout required.** Separate pre-export editability failure from export/reimport failure, record reimport as not reached when appropriate, and retain the exact source/repair context with its hash for future attribution. Freeze that reporting version and evaluate on a new holdout; retain original failure labels and aggregates as historical records.
