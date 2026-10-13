# Gemini Solfix Implementation Review: VERIFY v3

Verdict: **READY**

---

## 1. Scope & Verification Target

Review of uncommitted verify-v3 solfix diff across:
- `tools/cad_verify_v3_guard.py`
- `tools/cad_verify_v3_agent.py`
- `tools/eval_verify_v3.py`
- `tools/test_verify_v3.py`

Against:
- `design/cad-harness-verify-v3/SOLFIX-CONSENSUS.md` (including USER DECISION 16:39 JST and USER DECISION 17:08 JST update)
- `design/cad-harness-verify-v3/impl-notes.md` (Solfix section)

---

## 2. Findings & Verification Checklist

### A. Scoring, Gold, Thresholds, Order & Completed Records
- **Scoring**: **UNTOUCHED**. Evaluation gates in `eval_verify_v3.py` (`gates`, `result_pass`, `q_score`, `record`, `legacy_record`) are completely preserved. No scoring formulas or evaluator criteria were modified.
- **Gold**: **UNTOUCHED**. No gold files, schemas (`gold-schema.json`), rubrics, or descriptions were modified. Data checks pass cleanly (`smoke_verify_v3.py --data-only`: 18 cases, 60 episodes).
- **Thresholds**: **UNTOUCHED**. All threshold predicates in `eval_verify_v3.py` `summarize()` (`source` >= 8 and all >= 1, `complex` G6 >= 2, `stock` S3 >= 4, `defaults` A4 >= 2, `ambiguity` A5 >= 4 / A6 >= 4 with 0 critical inventions, `faults` fbar, `mvp` mbar, `legacy` lbar) remain byte-identical.
- **Order**: **UNTOUCHED**. Frozen order in `run-order.json` is verified by `validate_order()` against `expected_order()`. The resume segment executes strictly entries 46..59 in frozen sequence (sequences 47 through 60).
- **46 Records Preserved**: **CONFIRMED**. `original_binding()` verifies that all completed records 1–46 in `suite-run.json` are byte-identical. `original_artifacts()` validates directory and file hashes before and after execution. Sequences 1–46 are never re-executed. In `aggregate_resumed()`, segment 1 reports `completed_preserved: 46`.

### B. USER DECISION 16:39 JST (Retry & Call Accounting)
- **Retry Policy**: Uncapped retry on `codex_error_info == "server_overloaded"` (`PROVIDER_ALLOWLIST = frozenset(('server_overloaded',))`).
- **Wait Duration**: Fixed 600-second backoff (`PROVIDER_WAIT_S = 600`) tested and verified in `wait_provider()`.
- **Payload Identity**: Resent calls verify exact byte-identical context, prompt, argv, and target.
- **Budget Neutrality**: Provider-rejected attempts do not increment `budget.calls` or `guard.calls` (`guard.calls -= 1` restores the counter), and consume zero model P/R slots.
- **Observability**: Rejections, backoffs, session IDs, and stream hashes are recorded separately in `report['calls']` and transport artifacts without causing an abnormal harness stop.

### C. USER DECISION 17:08 JST Update (Deadline Removal)
- **Resume Deadline**: The inherited monotonic deadline is removed for segment 2 (`Guard.inherit(..., no_deadline=True)` sets `deadline = None`).
- **Segment 2 Reporting**: Segment 2 reports `deadline: 'none (user decision 17:08)'`, `deadline_monotonic: None`, and `deadline_ok: True`.
- **Segment 1 Intact**: Segment 1 strictly preserves its original recorded `deadline_ok` and monotonic bounds.
- **Remaining Bounds**: Quota stops (55% soft consult, 60% hard stop) and per-episode 900s stage budgets remain active and enforced.

### D. Consensus & Handoff Alignment
- **Historical G5-r1 and G1-r2**: Maintained as completed failures with separate `provider_rejected` annotations derived from historical session rollout logs.
- **A5-r5 Isolation**: The initial aborted A5-r5 attempt (sequence 47) is preserved in `original_partial` and scored strictly from segment 2 (`q-A5-r5-mvp1-resume1`).
- **Bounded Stream Capture**: Concurrent stdout/stderr draining retains at most 16,384 UTF-8 tail bytes (`CAPTURE_BYTES = 16384`) with full SHA-256 hashes and event length limits (`EVENT_CHARS = 1048576`).
- **Dual-Manifest Provenance**: Two-segment aggregation cleanly binds segment 1 to `SHA256.run-r1.json` and segment 2 to `SHA256.json`, gating changes strictly to `SOLFIX_CODE` allowlist via `transition()`.

---

## 3. Test & Verification Evidence

- `python -B -m unittest tools.test_verify_v3`: **23 tests passed, 0 failures, 1.030s**.
- Full test command (`115 tests` across 11 test suites): **115 passed, 6 skipped (native FreeCAD only), 41.233s, exit 0**.
- `python -B tools/smoke_verify_v3.py --data-only`: **pass** (`cases: 18, episodes: 60, planned_calls: 83, max_calls: 163, sol_calls: 0, cad_attempts: 0`).
- Working tree integrity: Only the designated 4 code files, 2 documentation files, and this review file are touched.

Verdict is **READY** to proceed with freeze and suite resumption.
