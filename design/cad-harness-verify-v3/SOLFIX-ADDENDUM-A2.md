# SOLFIX addendum A2: fault source binding vs CRLF fixture (draft for 3-party consensus)

## Evidence (resume attempt #3, PID 42540, 19:18–19:28 JST)
- Commit b483cc9, freeze f5b4aafc. Results: q-A5-r5, q-A6-r5 and C4/C5 r1–r3 all completed and PASS (8 of 8).
- fault-F4-r1 was then recorded with `stop_reason=harness:report_binding`, error `fault_source_binding` (eval_verify_v3.check_fault). The F5-r1 to F6-r2 entries were not started (stopped). Segment summary: real_calls 71.
- The F4-r1 driver itself completed normally, status ok: fault injected, reached, established, detected and observed are all True, and `injected_sha256` matches the fault record (118f1c94…).
- The mismatch: attempt-1 `source_sha256` is 4b43ad8b…, but the checker computes sha(injected) = 118f1c94…. The byte diff is exactly one byte: the injected text ends in `\r\n`, while input-a1.py ends in `\n`.
- Cause:
  - core.autocrlf=true checks the v3 fixtures out as CRLF (`git ls-files --eol`: `i/lf w/crlf`), and the frozen SHA hashed those working-copy bytes.
  - The driver (cad_verify_v3_agent.py:443–446) runs `fault.inject` and then `agent.source_from_final(candidate)`, whose fence strip drops the final CR.
  - check_fault hashes the raw injection and does not mirror that second pass.
  - Segment 1 had no F4–F6 entries, and the unit tests use LF fixtures, so this was never exercised before.
- Not involved: Sol, provider, quota (3.0%), CAD, scoring.

## Fix (minimal; checker only)
- New `fault_source_sha(injected)` = sha(cad_agent.source_from_final(injected)), which is exactly what the driver sends to CAD. check_fault uses it for the source-kind comparison only.
- The spec kind (F6) is unchanged.
- The driver, fixtures (bytes unchanged), scoring, gold, thresholds, order and rubric are all unchanged.
- Verified: the archived F4-r1 now binds (True).
- Test: `test_solfix_a2_fault_source_sha_mirrors_driver_reextraction_for_crlf_fixture`. 25 tests OK.

## Re-run
- All attempt #3 `-resume1` dirs (suite, A5-r5, A6-r5, C4/C5 r1–r3, F4-r1) and their logs are renamed with the suffix `-aborted-fault-binding-20261013T1930`. Nothing is deleted.
- Segment 2 (entries[46:]) is re-executed in full. The attempt #3 results are informational and unscored.
- The manifest version stays `verify-v3-reviewed-r1-solfix`. The previous manifest is archived as SHA256.solfix-a1.json, and FROZEN.md gets a section labelled "solfix-a2".

## Call charge
- Attempt #3 spent 71 − 54 = 17 accepted calls. These are charged.
- Spent before re-execution: 54 + 4 + 17 = 75. Worst case: 75 + 48 = 123 ≤ 163. The harness counter inherits 54, so it stays well under the ceiling.
- RESULTS will report 54 + 4 + 17 (archived, unscored) + segment-2 calls.
