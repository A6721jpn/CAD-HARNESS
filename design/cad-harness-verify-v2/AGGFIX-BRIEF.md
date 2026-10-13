# AGGFIX BRIEF (verify-v2-reviewed-r1-aggfix) — user decision 2026-10-13 10:43 JST (option A)

## Facts
- Run host-verify-v2-reviewed-r1 completed 60/60 (stop_reason null). Records: reports\cad-run\host-verify-v2-reviewed-r1-verify-v2-suite-mvp1\
- `aggregate` stops with `suite_record_binding`. Only failing check: `observed["deadline_monotonic"]-observed["started_monotonic"]!=10800` (actual 10799.999999999942, float rounding). All other binding checks pass (schema/version/sha_manifest/entries/ids/monotonic equality).
- Must run with CODEX_HOME=C:\Users\backo\AppData\Roaming\orca\codex-accounts\43cffd0b-d58b-4227-9a09-215b2f2cd78e\home (freeze identity).

## Proposed minimal fix (ONLY this)
- In tools\eval_verify_v2.py aggregate(): replace exact equality with `abs((deadline-started)-10800) > 1e-6` -> stop. Nothing else: no scoring, gold, threshold, order, or runner change.
- Add a unit test: 10799.999999999942 accepted; 10799.9 and 10801 rejected.
- Problem to solve: re-freeze rewrites SHA256.json, but the run records bind to sha256 of the ORIGINAL SHA256.json (129087752b…). Proposal: keep the original manifest archived byte-identical (e.g. SHA256.run-r1.json) and have aggregate bind `observed/plan sha_manifest` to that archived original, while verify_frozen checks the new aggfix manifest (which differs only in tools\eval_verify_v2.py + test file hashes and version). Reviewers: confirm or propose a smaller safe alternative.
- FROZEN.md gets a new section documenting the post-run change, justification, and diff. Outputs to new files: aggregate-verify-v2-host-reviewed-r1-aggfix.{json,csv}. Never overwrite.

## Ask
Reply AGREE / COUNTER (with exact change) in design\cad-harness-verify-v2\aggfix-<you>.md. Codex: if AGREE, also state the exact diff you will apply.
