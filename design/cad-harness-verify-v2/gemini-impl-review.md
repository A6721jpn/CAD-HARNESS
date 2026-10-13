# CAD-HARNESS VERIFY v2 Phase 2 Implementation Review (Gemini, 2026-10-13)

Review of the uncommitted working-tree implementation of `PLAN-V2-CONSENSUS.md` (R3 consensus draft).
Conducted strictly read-only: no code edits, no FreeCAD runs, and no Sol invocations.
All verified baseline test outcomes (84 unit tests PASS with 6 native skips, 3 native v2 unit PASS, 3 native DV3 unit PASS, 41/41 fresh native/rubric smokes r3 PASS, legacy 4/4 PASS, 60-episode mock integration PASS) are recorded in `design/cad-harness-verify-v2/impl-notes.md`.

---

## 1. Compliance Checklist Against PLAN-V2-CONSENSUS.md

### Probe Reachability and Artifact Gates
- **Relational Graph Traversal**: [`tools/cad_verify_v2_probe.py:65-85`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_probe.py#L65-L85) implements BFS graph traversal over active, driving constraints in `RELATIONS`. Seeds are extracted strictly from non-construction geometries of consumed native features ([`tools/cad_verify_v2_probe.py:37-57, 123-125`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_probe.py#L37-L57)) and resolved `ReferenceAxis` construction axes ([`tools/cad_verify_v2_probe.py:126-137`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_probe.py#L126-L137)).
- **Negative ID Exclusion**: [`tools/cad_verify_v2_probe.py:60-63`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_probe.py#L60-L63) strictly filters constraint references to `0 <= i < count`, explicitly preventing origin, coordinate axes, and external geometries (which carry negative IDs in FreeCAD) from becoming seeds or transit hubs.
- **PCD Capture**: For bolt circle flanges (W5 and saved V5), driving diameter/radius dimensions on construction PCD circles linked via active coincident/point-on-object constraints are captured in `driving_dimensions_mm` with full feature/link/sketch/constraint evidence paths ([`tools/cad_verify_v2_probe.py:152-160`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_probe.py#L152-L160)). Tested and verified offline on saved v1 V5 r1/r2 models (PCD 60 mm reachable, [`tools/test_verify_v2_native.py:13-30`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2_native.py#L13-L30)).
- **Decoy Rejection**: Unconnected construction circles, isolated loops, ray-only or origin-mediated connections, and reference or inactive dimensions are cleanly rejected ([`tools/test_verify_v2_native.py:31-59`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2_native.py#L31-L59), [`tools/test_verify_v2.py:192-205`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2.py#L192-L205)).
- **Artifact Gates Preserved**: Optimal bounding box (`optimalBoundingBox(False, False)`), relative volume tolerance ($10^{-4}$), stock scope bounding for S2, clean recompute, native editability checks, and independent FCStd/STEP reimport verification via separate headless `freecadcmd` process with PID tracking and clean document closure are retained identically to v1.

### Parse vs. CAD Repair Budget Split & Guaranteed Repair Call
- **Budget Partitioning ($P \le 1, R \le 1$)**: [`tools/cad_verify_v2_guard.py:26-91`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L26-L91) enforces episode-level caps: at most 1 `parse_repair`, at most 1 `repair`, and at most 2 CAD attempts. Once a CAD attempt executes, `generation_closed = True` locks initial generation calls ([`tools/cad_verify_v2_guard.py:54-55, 68`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L54-L55)). Route call caps ([`tools/cad_verify_v2_agent.py:42-45`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L42-L45)) enforce `source` $\le 4$, `spec` $\le 3$, `ask` $\le 1$, `completion` $\le 4$.
- **Timer and Reservation Enforcement**: 1 episode = 900 s fixed. Initial stage $\le 450$ s ([`tools/cad_verify_v2_guard.py:33`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L33)). Entering repair requires $\ge 450$ s remaining in the episode ([`tools/cad_verify_v2_guard.py:74-75`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L74-L75)), reserving 450 s for repair (R Sol 180 s, unused P 60 s, build/export 90 s, reimport 90 s, cleanup 30 s; [`tools/cad_verify_v2_guard.py:79-90`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L79-L90)).
- **Settled Failure Diagnostic & Repair Guarantee**: If attempt 1 results in settled CAD failure (`cad_agent.repair_reason(result) is None`), [`tools/cad_verify_v2_agent.py:253-260`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L253-L260) sets `report["repair_eligible"] = True`, calls `budget.begin_repair()`, prepares compact feedback ([`tools/cad_verify_v2_agent.py:22-31`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L22-L31)), and transitions purpose to `repair`.
- **Harness Stop on Missed Eligible Repair**: If `report["repair_eligible"]` is true but no repair call is invoked for any reason other than a valid guard stop (quota, sha, deadline, budget), [`tools/cad_verify_v2_agent.py:272-273`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L272-L273) marks `harness_repair_not_invoked:<reason>`, which triggers a fatal harness stop ([`tools/eval_verify_v2.py:173-177`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L173-L177)).
- **Repair Hygiene**: The repair call retains the original candidate target (`source` or `spec`) and never falls back to `unsupported` ([`tools/cad_verify_v2_agent.py:179`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L179)). Injected faults are never re-injected during repair ([`tools/cad_verify_guard.py:95`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_guard.py#L95)).

### Clarify-to-Completion Cohort (C2/C3) Outside `bar_met`
- **Cohort Isolation**: C2 and C3 (3 episodes each, 6 total) have `scored: false` and `bar_class: null` in [`design/cad-harness-verify-v2/run-order.json:579-661`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/run-order.json#L579-L661). [`tools/eval_verify_v2.py:490-528`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L490-L528) calculates `bar_met` strictly over the 51 core episodes (`core = [r for r in rows if r["scored"]]`), entirely excluding C cohort outcomes.
- **Two-Payload Linkage Protocol**: Call 1 outputs a clarification response evaluated by rubric and saved to `first-response.json` ([`tools/cad_verify_v2_agent.py:168`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L168)). Incorrect questions, hallucinations, or unneeded fields stop immediately with `completion_reached = False`, counting as misses in the fixed denominator of 3 without receiving the answer.
- **Clean Second Turn**: If the initial question is correct, call 2 receives user payload `description + "\n" + answer` (single LF, no BOM, no trailing LF). No conversation history or field hints are passed (`previous = None`, [`tools/cad_verify_v2_agent.py:173`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L173)). Prompt SHA is bound to `completion_input_sha256` ([`tools/cad_verify_v2_agent.py:68`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L68)).
- **Independent Wilson Reporting**: Metrics for completion pass rate, initial correct question rate, and conditional completion rate (given correct question) are reported independently under `summary["completion"]` ([`tools/eval_verify_v2.py:508-515`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L508-L515)). Incomplete cohorts set Wilson CI to `None` ([`tools/eval_verify_v2.py:513`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L513)).

### Fresh Holdout Freeze and Gold Isolation
- **15 Fresh Holdout Items**: Hand-authored cases under [`design/cad-harness-verify-v2/test/`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/test/) (W1–W6, S2, A1–A3, C2–C3, K1–K3). All analytic volume, bounding box, and fault delta formulas match `PLAN-V2-CONSENSUS.md` and are verified in [`tools/test_verify_v2.py:206-231`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2.py#L206-L231).
- **Text & Suffix Hygiene**: Adopts grok's COUNTER (omitting the common dimension convention clause "寸法列はX×Y（3つ目はZ）。"). Placement text ("XY中心、下面Z=0。") is correctly omitted for W3 and A1 exceptions.
- **Zero Gold Leakage**: Generation context never contains gold targets, tolerances, or case names ([`tools/cad_verify_v2_agent.py:73-84`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L73-L84)). Compiler [`tools/cad_spec.py`](file:///C:/dev/CAD-HARNESS/tools/cad_spec.py) is byte-identical to baseline with no case-name or description-SHA lookups.
- **Freeze Manifest**: [`design/cad-harness-verify-v2/SHA256.json`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/SHA256.json) binds 187 files. Initial state `version = "verify-v2-phase2-uncommitted"` correctly fails closed on any live run attempt until reviewed freeze commit is generated ([`tools/eval_verify_v2.py:132-135`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L132-L135)).

### Baseline Preservation
- **Unmodified Core Components**: `tools/cad_agent.py`, `tools/cad_spec.py`, `tools/cad_spec_probe.py`, `tools/cad_verify_probe.py`, `tools/cad_verify_guard.py`, `tools/eval_mvp.py`, `tools/eval_verify.py`, `design/cad-harness-mvp/eval-v1/*.json`, and `design/cad-harness-verify/*` remain completely untouched and byte-identical to baseline.
- **Surgical Runner Dispatch**: Only 3 files modified in `tools/` ([`cad_run.py`](file:///C:/dev/CAD-HARNESS/tools/cad_run.py), [`cad_run_freecad.py`](file:///C:/dev/CAD-HARNESS/tools/cad_run_freecad.py), [`cad_verify_freecad.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_freecad.py)), strictly gating v2 functionality behind explicit `--probe-profile verify-v2`. Legacy, mvp-v1, and verify-v1 behaviors are 100% preserved.

### No-Overwrite Aggregates
- **Path and File Protection**: [`tools/eval_verify_v2.py:533-534`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L533-L534) pre-checks `reports/aggregate-verify-v2-<suffix>.{json,csv}` for existence or symlinks.
- **Exclusive Creation**: Both `.json` and `.csv` files are written using exclusive creation mode (`open("x")`, [`tools/eval_verify_v2.py:581, 585`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L581-L585)). Suite progress logs and run directories similarly enforce non-existence before execution ([`tools/eval_verify_v2.py:415, 423`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L415-L423)).

### Quota Guard (55% Soft / 60% Hard Stop, 5-Minute Staleness)
- **Snapshot Validation**: [`tools/cad_verify_guard.py:20-46`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_guard.py#L20-L46) enforces age $< 0$ (future stop), age $> 300$ s (stale stop), $\ge 55\%$ soft stop, $\ge 60\%$ hard stop.
- **Pre-Invocation Verification**: Checked immediately before every real LLM call ([`tools/cad_verify_v2_guard.py:20-23`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L20-L23), [`tools/cad_verify_v2_agent.py:95`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L95)). Pre-call stops prevent launching unverified calls without faking invocation records.

### Monotonic 3-Hour Deadline across Suite
- **Single Monotonic Clock**: Shared 10800 s monotonic deadline spans the entire suite from run start through independent aggregation ([`tools/cad_verify_guard.py:51-66`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_guard.py#L51-L66), [`tools/eval_verify_v2.py:572`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L572)).
- **Episode Reserve Guard**: [`tools/cad_verify_v2_guard.py:20-23`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_guard.py#L20-L23) ensures $\ge 960$ s (900 s episode + 60 s aggregate reserve) remain before starting any episode, halting immediately with `shared_deadline_insufficient_episode_reserve` if insufficient.

---

## 2. Findings

### MUST (Blockers)
*None.* The implementation satisfies all requirements, contracts, and safety mechanisms established in `PLAN-V2-CONSENSUS.md`.

### SHOULD (Recommended Improvements)
1. [`tools/cad_verify_v2_agent.py:102-106`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L102-L106):
   If `runner` raises `subprocess.TimeoutExpired`, execution jumps directly to the enclosing `except` block in `run_driver` without setting `row["exit"]`. In `row`, `exit` remains unset. While `row.get("exit")` handles missing keys safely, explicitly populating `row["exit"] = -1` or `row["timed_out"] = True` in an inner `except subprocess.TimeoutExpired` handler before re-raising would aid post-run triage.
2. [`tools/eval_verify_v2.py:428`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L428):
   `guard.before_episode(max(e["max_calls"], sum(x["min_calls"] for x in order["entries"][e["sequence"]-1:])))` checks that remaining calls cover the remaining planned minimums. If earlier episodes consume extra repair or parse calls, this guard correctly halts early with `insufficient_call_budget`. Ensure this fail-fast behavior is understood during host monitoring.

### NIT (Observations & Non-Blocking Notes)
1. [`design/cad-harness-verify-v2/SHA256.json`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/SHA256.json):
   The manifest on disk is currently the Phase 2 uncommitted snapshot (`version: "verify-v2-phase2-uncommitted"`, `cli: null`). As documented in `impl-notes.md:79-92`, the supervisor must archive this file and run `eval_verify_v2.py freeze` to produce the reviewed freeze manifest binding the committed implementation and plan commit SHAs before Phase 3 live execution.
2. [`tools/cad_run.py:333`](file:///C:/dev/CAD-HARNESS/tools/cad_run.py#L333):
   In `verify_artifacts`, `deadline = min(run_deadline, time.monotonic() + request.get("verification_timeout_s", 300))` cleanly receives 90 s during v2 repair stage, aligning artifact verification with the 90 s repair stage reservation.
3. [`tools/cad_verify_v2_agent.py:26`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v2_agent.py#L26):
   `measured["editability"].pop("dimension_evidence", None)` inside `feedback()` keeps the repair prompt compact and avoids context blowout from large constraint reachability graphs while leaving full evidence in the artifact report.

---

## 3. Verdict

**verdict: READY**

REVIEW DONE
