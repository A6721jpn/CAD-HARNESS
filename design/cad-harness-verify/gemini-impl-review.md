# CAD-HARNESS VERIFY Phase 2 Implementation Review (Gemini, 2026-10-12)

Review of the uncommitted working-tree implementation of `PLAN-CONSENSUS.md` (R3b).
Conducted strictly read-only: no code edits, no FreeCAD runs, and no Sol invocations.
All verified baseline test outcomes (offline 47/47 expected, legacy 4/4 passed, 73 unit tests discovered and 70 passed with 3 native skips) are recorded in `design/cad-harness-verify/impl-notes.md`.

---

## 1. Compliance Checklist Against PLAN-CONSENSUS.md

### Holdout and Freeze Discipline
- **Corpus Separation**: `design/cad-harness-verify/test/` (V1–V6, S1, Q1–Q3, F1–F3) and `dev/` (DV1–DV6, DS1, DQ1–DQ3) are strictly separated. Dev case dimensions and wording differ from test cases.
- **Description Cleanliness**: All `description.txt` files under `test/` match the signed consensus table character-for-character in UTF-8 without BOM, quotation marks, or trailing newlines.
- **Dev Pilot Constraint**: `tools/eval_verify.py:263-264` enforces a maximum of 4 dev Sol calls (`dev_calls`), stopping if exceeded. Dev entries in `run-order.json` (sequences 1–3) have planned calls summing to 4.
- **Freeze Immutability**: `tools/eval_verify.py:38, 55` writes `SHA256.json` using exclusive creation mode (`open("x")`). `verify_frozen` (`tools/eval_verify.py:59-68`) fails closed on any file mismatch, agent identity shift, or model configuration change.

### Gold Leak Prevention
- **Generation Isolation**: In `tools/cad_agent.py:476`, Codex execution receives only `input_text` as the prompt, which is validated to match `gold["description"]` (`tools/cad_agent.py:412-413`).
- **Prompt & Developer Context**: Initial turn context contains only the skill text and generic spec/source contracts (`tools/cad_agent.py:454-461`). No gold dimensions, target volumes, or test-case identities are present.
- **Generic Compiler**: `tools/cad_spec.py` is schema-driven with no case-name or description-hash lookups.
- **Repair Feedback**: Feedback keys in `tools/cad_agent.py:32-33, 602-603` provide only measured values, predicate diff names, and failure classes—never gold targets or source solutions.

### Eval-v1 Gold, Bar, and Eval_MVP Unchanged
- **Protected File Preservation**: All 27 baseline files remain byte-identical: `tools/eval_mvp.py`, `tools/cad_spec.py`, `tools/cad_spec_probe.py`, `design/cad-harness-mvp/eval-v1/*.json`, and `DECISION-01-acceptance-bar.md`.
- **Fresh Evaluator Runs**: `tools/eval_verify.py:259-269` runs fresh MVP cases (P1–P5 × 2) sequentially through `tools/cad_agent.py` using `probe_profile="mvp-v1"`.
- **Bar Enforcement**: `tools/eval_verify.py:328-330, 344` requires MVP ≥ 8/10 with each case ≥ 1/2, and legacy smokes 4/4.

### Probe Correctness (No False Passes)
- **Bounding Box Precision**: `tools/cad_verify_probe.py:22-25` exclusively uses `optimalBoundingBox(False, False)` with zero triangulation or padding, without fallback to conservative `BoundBox`.
- **Comprehensive Predicates**: Probes for all 6 profiles (`roller`, `taper`, `elbow`, `ribbed_box`, `flange`, `rect_prism`) enforce closed loop geometry, section cuts, wall positions, lumen occupancy, and extraneous face rejection.
- **S1 Gold Scope**: `test/S1/gold.json` and `tools/cad_verify_probe.py:409-417` evaluate target stock volume 29232 mm³ on the scoped bounding box `[-29,29,-21,21,0,12]`, avoiding fillet corner-patch ambiguity. Whole volume is measured and verified between FCStd and STEP reimports at 1e-4 relative tolerance.
- **Native Editability Gate**: `tools/cad_verify_probe.py:457-527` verifies a single Body, allowed Tip type, consumed Sketch links, clean recompute, and presence of driving dimensions (including Loft section placement and actually referenced construction axes).
- **Serialized OCC Sections**: `tools/cad_verify_probe.py:131-158` validates closed degree-1 B-spline representations from reimported FCStd pipe sections through pole radial distance, radial minimums, plane checks, and normal orientation, avoiding false reimport failures.

### Fault Injection Discipline
- **Contract-Valid Injection**: `tools/cad_verify_guard.py:83-126` injects faults only after a schema-valid initial candidate.
- **No Forced Failure**: `tools/cad_verify_guard.py:128-136` observes raw probe results; the injected flag never forces a probe failure.
- **Prescribed Defect Detection**: Defective candidates (F1 missing groove, F2 missing PCD hole, F3 diameter 4→6) must produce a settled run with valid native structure and target predicate failure. Undetected defects raise `fault_false_pass` or `fault_detection_mismatch` (`tools/cad_agent.py:584-585`), halting the suite.

### Quota Guard (55/60 + 5-Minute Staleness)
- **Strict Snapshot Validation**: `tools/cad_verify_guard.py:20-46` validates `snapshot_id`, `observed_at`, and `used_percent`. Future timestamps (`age < 0`) and stale snapshots (`age > 300` s) trigger stops.
- **Thresholds**: Soft stop at 55%, hard stop at 60%.
- **Pre-Call Enforcement**: `tools/cad_verify_guard.py:74-80` checks quota immediately before every real model invocation. `tools/eval_verify.py:158-161` re-validates snapshots across all recorded calls.

### 3-Hour Monotonic Deadline
- **Unified Clock**: `tools/cad_verify_guard.py:51-66` enforces a shared 10800 s deadline across dev, legacy, regression, test, and aggregation.
- **Timeout Clipping**: Individual runs are clipped to `min(900, remaining)` (`tools/cad_agent.py:386`). CAD executions are clipped to `min(300, remaining - 5)` (`tools/cad_agent.py:564`).
- **Post-Deadline Invalidation**: Any run with `ended_elapsed_s >= 10800` is marked failed (`tools/eval_verify.py:281, 369`). Aggregation checks `observed["wall_s"] < 10800` and deadline monotonicity (`tools/eval_verify.py:384`).

### No-Overwrite Aggregation
- **Path Protection**: `tools/eval_verify.py:236` rejects existing suite or run directories.
- **Exclusive Creation**: `tools/eval_verify.py:355-356, 396` forbids existing aggregate files or symlinks and writes JSON and CSV using exclusive mode (`open("x")`).

### Wilson Score Confidence Interval
- **Formulation**: `tools/eval_verify.py:293-298` implements standard two-sided 95% Wilson score intervals with $z = 1.96$.
- **Completeness Guard**: Returns `None` if the batch or part is incomplete (`not complete or not total`).
- **No Inferred Generalization**: Separate intervals are calculated per case and fault category; groups are not pooled into general language success rates (`tools/eval_verify.py:392`).

---

## 2. Findings

### MUST (Blockers)
*None.* The implementation satisfies all contractual gates and offline verification requirements. Any failure condition correctly fails closed.

### SHOULD (Recommended Improvements)
1. `tools/cad_verify_guard.py:99`:
   `Fault.inject` marks `self.record.update(reached=True, ...)` before inspecting `self.rule["path"]` and `self.rule["match"]`. If a candidate spec lacks the target element, execution reaches lines 110 or 115, setting `self.record["not_reached_reason"] = "candidate_target_missing"` and returning the unmutated candidate, while `reached` remains `True`. Moving `reached = True` to line 125 alongside `injected = True` ensures the reported `reached` metric accurately reflects successful injection.

2. `tools/eval_verify.py:24-30`:
   The `CODE` tuple does not include `"tools/test_verify_dv3_native.py"`. Consequently, running `python -B tools/eval_verify.py freeze` directly omits this test from `SHA256.json` unless monkey-patched via CLI as noted in `impl-notes.md:297`. Adding `"tools/test_verify_dv3_native.py"` to `CODE` in `tools/eval_verify.py:26` standardizes freeze generation.

### NIT (Observations & Non-Blocking Notes)
1. `design/cad-harness-verify/SHA256.json`:
   The manifest currently on disk represents the pre-fix snapshot (`local_commit: pending_supervisor`). As documented in `impl-notes.md:272-273`, the supervisor must archive the old manifest and generate a fresh freeze manifest before initiating Phase 3.
2. `tools/cad_agent.py:507-514`:
   Under `verify-v1`, any `needs_clarification` payload halts the run immediately (`clarification_stop`), which is correct for Q2/Q3 first-response rubrics and prevents wasteful CAD attempts on non-Q tasks. The legacy MVP path continues to raise `ValueError("needs_clarification")` and retry.
3. `tools/cad_agent.py:559, 564`:
   `Guard.remaining()` already deducts a 5-second reserve (`CLEANUP_RESERVE_S = 5`). Line 564 deducts an additional 5 seconds for the CAD timeout, and line 559 halts when remaining budget is $\le 6$ s. This conservative margin safely guarantees cleanup completion within the 10800 s window.
4. `tools/cad_agent.py:584-585`:
   If an injected fault fails to exhibit the expected predicate diff, the driver raises `fault_detection_mismatch` (or `fault_false_pass` if geometry passed). Both codes are correctly recognized as harness failures (`tools/eval_verify.py:114-115`), halting the suite as required by the consensus plan.
5. `tools/eval_verify.py:384`:
   The aggregation deadline check verifies monotonic clock progression within the same operating session. A host reboot between `run` and `aggregate` would invalidate monotonic comparison, which is appropriately noted in `impl-notes.md:337-339`.

---

## 3. Verdict

**verdict: READY**

REVIEW DONE
