# Gemini Consensus: SOLFIX Addendum A2

Verdict: **AGREE**

---

## 1. Root Cause Confirmation

The evidence in [`reports/cad-run/host-verify-v3-reviewed-r1-fault-F4-r1-mvp1-resume1-aborted-fault-binding-20261013T1930/driver-run.json`](file:///C:/dev/CAD-HARNESS/reports/cad-run/host-verify-v3-reviewed-r1-fault-F4-r1-mvp1-resume1-aborted-fault-binding-20261013T1930/driver-run.json) and [`tools/eval_verify_v3.py`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v3.py) confirms the diagnosis:
- **Driver execution**: In F4-r1, the driver completed normally with `status: "ok"` and all fault gates verified (`injected: true`, `reached: true`, `established: true`, `detected: true`, `observed: true`).
- **CRLF vs LF discrepancy**:
  - The working-copy candidate fixture (`test/F4/candidate.py`) was checked out with Windows CRLF line endings under `core.autocrlf=true`.
  - The driver in [`tools/cad_verify_v3_agent.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_agent.py) re-extracts the injected candidate via `agent.source_from_final(candidate)`, which strips fences and trailing carriage returns (`\r`), writing an LF-terminated `input-a1.py` with hash `4b43ad8b...`.
  - The checker in [`tools/eval_verify_v3.py:429`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v3.py#L429) hashed raw `injected.encode("utf-8")` containing `\r\n`, producing hash `118f1c94...`.
  - Because `4b43ad8b... != 118f1c94...`, `check_fault` raised `ValueError("fault_source_binding")`, causing the harness stop.
- Provider, Sol, quota (3.0%), CAD execution, and scoring were not involved.

---

## 2. Minimal Fix Verification

- **Implementation**:
  - Adds helper `fault_source_sha(injected)`:
    ```python
    def fault_source_sha(injected):
        return sha(cad_agent.source_from_final(injected).encode("utf-8"))
    ```
  - Updates line 435 in `check_fault`:
    ```python
    if kind == "source":
        if first["source_sha256"] != fault_source_sha(injected): raise ValueError("fault_source_binding")
    ```
  - Exactly mirrors the driver's pre-CAD normalization pass on source candidates.
  - The spec branch (`kind == "spec"`, case F6) is unchanged.
- **Empirical validation**:
  - Verified directly against the archived F4-r1 run: `check_fault` now validates cleanly (`True`).
  - New test `test_solfix_a2_fault_source_sha_mirrors_driver_reextraction_for_crlf_fixture` passes.
  - All 25 unit tests in [`tools/test_verify_v3.py`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v3.py) pass in 0.922s.
- **Invariants intact**:
  - Scoring: Untouched.
  - Gold & rubrics: Untouched.
  - Thresholds: Untouched.
  - Order: Untouched.
  - 46 segment-1 records: Untouched and byte-identical.
  - Data smoke checks pass (`smoke_verify_v3.py --data-only`: 18 cases, 60 episodes, planned 83, max 163).

---

## 3. Call Charge & Re-run Plan Confirmation

- **Call Accounting**:
  - Attempt #3 spent 17 accepted calls (71 total minus 54 inherited).
  - Cumulative calls spent across segments/attempts: 54 + 4 + 17 = 75.
  - Worst case for remaining 14 episodes of segment 2: 75 + 48 = 123 ≤ 163 ceiling. The inherited harness counter (54) stays well below the 163 cap.
  - Transparent attribution: RESULTS will document 54 (segment 1) + 4 (attempt #2) + 17 (attempt #3) as archived, unscored calls, alongside completed segment-2 calls.
- **Archive & Re-execution**:
  - All attempt #3 directories (`suite`, `A5-r5`, `A6-r5`, `C4/C5 r1..r3`, `F4-r1`) and logs are archived with suffix `-aborted-fault-binding-20261013T1930`. Zero forensic data is deleted.
  - Namespace `-resume1` is freed to permit clean execution of segment 2 (`entries[46:]`).
  - Version remains `verify-v3-reviewed-r1-solfix`, preserving transition gate consistency. Previous manifest is archived as `SHA256.solfix-a1.json`, and FROZEN.md receives section "solfix-a2".

Gemini confirms consensus: **AGREE 19:35 JST**.
