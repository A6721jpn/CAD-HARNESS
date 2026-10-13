# CAD-HARNESS VERIFY v2 Aggfix Implementation Review (Gemini, 2026-10-13 11:25 JST)

Reference:
- Consensus: [`design/cad-harness-verify-v2/AGGFIX-CONSENSUS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/AGGFIX-CONSENSUS.md)
- Notes: [`design/cad-harness-verify-v2/aggfix-impl-notes.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/aggfix-impl-notes.md)
- Diff: `git diff tools/eval_verify_v2.py tools/test_verify_v2.py`

## Verdict: READY

The uncommitted implementation in `tools/eval_verify_v2.py` and `tools/test_verify_v2.py` conforms strictly and completely to `AGGFIX-CONSENSUS.md` and `aggfix-impl-notes.md`. All unit tests pass cleanly (15/15 PASS in 31.865 s).

---

## Detailed Audit

### 1. Duration Term Float Rounding Fix ([`tools/eval_verify_v2.py:565`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L565))
- Replaces exact duration equality `!= 10800` with absolute error tolerance:
  ```python
  or abs((observed["deadline_monotonic"]-observed["started_monotonic"])-10800)>1e-6): raise ValueError("suite_record_binding")
  ```
- Correctly accommodates IEEE 754 64-bit float subtraction error ($|10799.999999999942 - 10800| \approx 5.82 \times 10^{-11} \le 10^{-6}$).
- All other duration and monotonic comparisons remain exact:
  - `observed["started_monotonic"] != plan["started_monotonic"]` (exact)
  - `observed["deadline_monotonic"] != plan["deadline_monotonic"]` (exact)
  - `(run_manifest is not None and plan["version"] != manifest["version"])` (exact)
  - `row["ended_elapsed_s"] >= 10800` marks `row["passed"] = False` (exact, line 576)
  - `deadline_ok = (clock or time.monotonic)() < observed["deadline_monotonic"] and observed["wall_s"] < 10800` (exact, line 596)

### 2. Dual-Manifest Binding Architecture ([`tools/eval_verify_v2.py:538-560, 604, 623`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L538-L560))
- **Safe Reading**: When `--run-manifest` is provided, reads via `safe_file(root, run_manifest)` preventing directory traversal or symlink escapes.
- **Strict Compatibility Checks** (lines 547–555):
  - Requires identical metadata key sets (`set(original) == set(manifest)`).
  - Only metadata keys `{"version", "created_at", "local_commit", "files"}` may differ; all other metadata fields (`schema`, `profile`, `plan_commit`, `cli`, `agents_sha256`, `settings`) must match identically.
  - Requires `manifest["version"] == original["version"] + "-aggfix"`.
  - Requires identical file key sets (`set(original["files"]) == set(manifest["files"])`).
  - **Strict Scope Gate**: Requires differing file hashes to be **strictly and exactly** `{"tools/eval_verify_v2.py", "tools/test_verify_v2.py"}`. Any third-file change raises `Stop("aggfix_manifest_binding")`.
- **Identity Preservation**:
  - Rebinds `manifest` to `original` and `digest` to `sha(raw)`, so `observed.version`, `observed.sha_manifest`, `observed.frozen_sha256`, and per-episode driver identities check against the original run measurement identity.
  - Adds `aggregation_identity = dict(version=manifest["version"], local_commit=manifest["local_commit"], sha_manifest=digest, run_manifest=run_manifest)` to output document (line 604).
  - Top-level `version`, `local_commit`, `plan_commit`, `sha_manifest`, `frozen_sha256` remain the original measurement's identity.
  - When `run_manifest is None`, single-manifest behavior is completely preserved.

### 3. Live Run Lockout for Aggfix Versions ([`tools/eval_verify_v2.py:410`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L410))
- Enforces Grok addition (a):
  ```python
  if manifest["version"].endswith("-aggfix"): raise Stop("aggfix_no_live_run")
  ```
  Halts immediately before directory creation, plan writing, or subprocess launch.

### 4. Comprehensive Unit Test Coverage ([`tools/test_verify_v2.py:216, 279-289, 416-510`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2.py#L216))
- **Live Run Refusal**: `test_aggfix_version_cannot_start_a_live_suite` verifies `Stop("aggfix_no_live_run")` and asserts zero subprocesses or directory writes.
- **Stored Pair & Tolerance**: Exercises stored host pair `525342.3589999999 - 514542.359 == 10799.999999999942` (accepted, produces identical summary to unpatched aggregation), while rejecting `10799.9` and `10801` with `ValueError("suite_record_binding")`.
- **Exact Limits Verified**: Rejects run/plan timestamp mismatch (`+1e-7`), rejects expired monotonic deadline (`clock = deadline`), rejects `wall_s = 10800`, and rejects episode `ended_elapsed_s = 10800`.
- **Archive Simulation**: Verifies valid aggregation with `--run-manifest`, matching top-level identity, `aggregation_identity` structure, rejection of missing `--run-manifest` on modified manifest, rejection of corrupted archive bytes, rejection of third modified file (`Stop("aggfix_manifest_binding")`), and rejection of uncommitted code edits (`Stop("sha_mismatch:tools/eval_verify_v2.py")`).
- **Process Launch**: Asserts `launch.assert_not_called()` across all aggregation tests.

### 5. Integrity & Non-Regression
- **No Scope Creep**: Zero changes to scoring, analytic gold formulas, bar thresholds, prompt payloads, run order, runner logic, or FreeCAD/Sol execution.
- **Zero Live Execution**: No live Sol or CAD calls were made.
- **Test Results**: All 15 tests in `tools/test_verify_v2.py` pass cleanly.
