# SOLFIX addendum A1: no-deadline CAD timeout cap (draft for 3-party consensus)

## Evidence
- Resume #2 (detached, PID 30464, started about 18:53 JST): q-A5-r5 passed, then q-A6-r5 passed, then the process crashed at the start of completion-C4-r1 (dir mtime 18:55:48 JST).
- `.tmp\v3resume.err.log`: `cad_verify_v3_agent.py:474 timeout=min(timeout,math.floor(guard.remaining()))` raised `OverflowError: cannot convert float infinity to integer`.
- Cause: the `no_deadline=True` guard (user decision 17:08) makes `cad_verify_v3_guard.Guard.remaining()` return `math.inf`, and `math.floor(inf)` raises. The other uses of `remaining()` (lines 184, 289, 314 and 482) only use `min()` or `str()` on it, so they are finite-safe. Provider, Sol and quota are not involved (quota was at 3.0%).
- Why this was not caught earlier: segment 1 ran with a finite deadline, and at A5-r5/A6-r5 the CAD path was either skipped or took another branch. *(To confirm: the reviewers check the route.)*

## Fix (minimal)
- New helper `cap_timeout(timeout, remaining)`: if `remaining` is finite it returns `min(timeout, floor(remaining))`, otherwise `timeout` (the per-stage `budget.cad_timeout()`).
- It replaces line 474 only.
- Regression test: `test_solfix_a1_cad_timeout_cap_with_no_deadline_guard`. 24 tests OK.
- Untouched: scoring, gold, thresholds, order, rubric, budgets and the 46 segment-1 records.

## Re-run
- `resume()` always runs `entries[46:]` and refuses existing `-resume1` dirs.
- So the four resume #2 dirs (`suite`, `q-A5-r5`, `q-A6-r5` and the partial `completion-C4-r1`, all `-resume1`) are renamed with the suffix `-aborted-inf-overflow-20261013T1856`. Nothing is deleted.
- Their logs are archived the same way.
- The whole segment 2 (A5-r5 then sequences 48–60) is re-executed under the refreeze `verify-v3-reviewed-r1-solfix-a1`.
- The A5-r5 and A6-r5 passes from resume #2 are not scored. They are reported in RESULTS as informational only.

## Refreeze
- `SHA256.json` is regenerated, and the previous solfix manifest is archived as `SHA256.solfix.json`.
- The aggregate still binds the original run with `--run-manifest SHA256.run-r1.json`.
- A FROZEN.md section is appended.

## Revision 2 (after BLOCKs from codex and grok, 19:12 JST)
- **Version:** the manifest version stays `verify-v3-reviewed-r1-solfix`. `SOLFIX_VERSION`, the transition gates and the cold-run exclusion are unchanged. "solfix-a1" is used only as the FROZEN.md section label.
- **Manifests:** the previous solfix manifest is archived as `SHA256.solfix.json`, and a new `SHA256.json` is generated. The aggregate still uses `--run-manifest SHA256.run-r1.json`.
- **Log name:** the archived log is `.tmp\v3resume.err-aborted-inf-overflow-20261013T1856.log`.
- **Call charge carried forward:** the aborted resume #2 spent 4 accepted calls (A5-r5 1, A6-r5 1, C4-r1 2; 0 CAD attempts). They are charged, not refunded. The total spent before re-execution is therefore 54 + 4 = 58, leaving 105 of 163.
  - The worst case of the 14 segment-2 entries is a sum of `max_calls` = 48, giving 58 + 48 = 106 ≤ 163. The 163 ceiling cannot be breached, so no budget code change is needed.
  - RESULTS reports the total as 54 + 4 (archived, informational, unscored) + segment-2 calls, with the 4 listed separately.
  - The aggregate's own call field covers only the scored segments, and RESULTS states this explicitly.
- No other change.
