# VERIFY v3 RERUN2 results (2026-10-14 JST)

User decision 2026-10-14 08:58 JST (option 1). Only geometry-G5-r1 and geometry-G1-r2 were re-run. These were the two segment-1 interpretation failures caused by provider `server_overloaded` (see SOL-FAILURE.md).

- Implementation: c345617 (codex). Reviews: grok and gemini READY. Refreeze: c6cc8d8 (SHA256.json 024ecb52c38194d12f7fa7b89217a96e64d6853893fc4dfced7ccd430ab09714; manifest version verify-v3-reviewed-r1-solfix).
- Run: detached on DPC-019. Suite `reports/cad-run/host-verify-v3-reviewed-r1-verify-v3-suite-mvp1-rerun2`. Quota snapshot 9% used.
- Results:
  - geometry-G5-r1: completed, PASS.
  - geometry-G1-r2: completed, PASS.
- Provider: rejected attempts 0, provider wait 0 s. rerun2_calls 4.
- New aggregate: `reports/aggregate-verify-v3-host-reviewed-r1-solfix-rerun2.{json,csv}`.
  - valid_suite, complete and bar_met are all true. All 8 thresholds are true.
  - G1 2/2, G5 2/2. Geometry 18/18.
  - per_suite total: 60/60 completed and passing (dev 3/3, legacy 4/4, mvp 10/10, geometry 18/18, q 13/13, completion 6/6, fault 6/6).
- `substituted_rows` keeps both rows for each ID (original passed=false, replacement passed=true). The other 58 rows are copied unchanged.
- Calls:
  - Aggregate real_calls is 88 (retained segments only).
  - total_charged_calls is 109 of 163, including archived_charged_calls 21.
- Preserved, not overwritten: the original segment-1 rows, the `aggregate-verify-v3-host-reviewed-r1-solfix.*` files, and RESULTS.md (previous verdict PASS, 58/60).
- Note: this rerun replaces two provider-failed observations after the first scoring. It is not a blind, uninterrupted replication.
- STOP. There is no next phase.
