# Gemini Review: VERIFY v3 RERUN2 (User Decision 2026-10-14 08:58 JST)

Verdict: **READY**

---

## 1. Scope & Verification

Review of uncommitted rerun2 diff across:
- [`tools/eval_verify_v3.py`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v3.py)
- [`tools/test_verify_v3.py`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v3.py)

Against:
- [`design/cad-harness-verify-v3/RERUN2-BRIEF.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/RERUN2-BRIEF.md)
- [`design/cad-harness-verify-v3/rerun2-impl-notes.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/rerun2-impl-notes.md)

---

## 2. Findings & Invariant Checklist

1. **Allowlist Restricted Strictly to G5-r1 and G1-r2**:
   - `RERUN2_IDS` is fixed as `frozenset(('geometry-G5-r1', 'geometry-G1-r2'))`.
   - `rerun2_ids` enforces exact set equality and length 2, raising `Stop('rerun2_id_allowlist')` on any other ID, duplicate, or subset before loading state or launching.
   - `rerun2_source` verifies that the base aggregate's historical provider-rejected failures match `RERUN2_IDS`.

2. **Driver, Scoring, Gold, Thresholds & Order Untouched**:
   - **Driver**: [`tools/cad_verify_v3_agent.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_agent.py) is completely untouched. `rerun2_driver` runs `agent.run_driver` under a temporary `-mvp1` execution name accepted by the driver, then relocates the resulting directory to `-rerun2` and patches path references in `driver-run.json`.
   - **Scoring**: Untouched. Re-uses existing `record()` without altering any pass/fail evaluation logic.
   - **Gold & Rubrics**: Untouched. No data or schemas were edited.
   - **Thresholds**: Untouched. Existing `summarize()` function is invoked without modification to re-evaluate suite thresholds.
   - **Order**: Untouched. `run-order.json` is preserved. `selected` preserves the frozen order (`geometry-G5-r1`, then `geometry-G1-r2`), each with `route='source'` and `max_calls=4`.

3. **Original Artifacts Preserved**:
   - `rerun2_source` records SHA-256 digests for all files in segment 1 (`paths(root, prefix)`), segment 2 (`...-resume1`), driver directories, and the base aggregate JSON/CSV.
   - `verify_rerun2_artifacts` verifies that none of these preserved files were altered before writing the rerun2 aggregate.
   - `substituted_rows` preserves both the `original` and `replacement` rows for complete forensic traceability.

4. **Nothing Overwritten**:
   - `rerun()` checks for existing target directories (`-rerun2` suite, episode dirs, staging dirs) and immediately raises `Stop('rerun2_prefix_exists')` if any are present.
   - `aggregate_rerun2()` requires the `-rerun2` suffix and checks that output JSON/CSV do not already exist, raising `Stop('aggregate_exists_or_linked')`. Exclusive file creation is enforced throughout.

5. **Call Charge & Quota Stops**:
   - Initial call spend is seeded from `RERUN2_SPENT = 105` against the 163 ceiling.
   - Maximum budget for the two episodes is 4 + 4 = 8 calls, bounding total potential spend to at most 105 + 8 = 113 ≤ 163.
   - The Guard inherits `no_deadline=True` (per 17:08 decision) and enforces quota checks (55% soft consult, 60% hard stop) on every invocation. Overload retries (600 s) follow the existing unbudgeted provider-retry policy.
   - Aggregate correctly reports `real_calls` as 84 + new calls, `total_charged_calls` as 105 + new calls, and `archived_charged_calls` as 21.

6. **Substitution Strictly Limited to 2 Rows**:
   - `replacements` dictionary contains only keys from `RERUN2_IDS`.
   - In `aggregate_rerun2()`, exactly 2 rows are replaced. The remaining 58 rows (including segment-2 A5/A6) are copied verbatim from the base aggregate without re-scoring or re-execution.

---

## 3. Test Evidence

- `python -B -m unittest tools.test_verify_v3`: **29 tests OK in 1.447s** (includes 4 new mocked regression tests for allowlist, target refusal, driver compatibility, and row substitution).
- Full regression suite: **121 tests OK (6 skipped native-only) in 42.475s**.
- `python -B tools/smoke_verify_v3.py --data-only`: **pass** (18 cases, 60 episodes, 83 planned, 163 max calls).

Verdict is **READY** to proceed with freeze and rerun execution.
