# VERIFY v2 FROZEN
- version: verify-v2-reviewed-r1
- implementation commits: 666e9df, fac9560, 1e93a1b (reviews grok READY + gemini READY; grok SHOULD1/2 + NIT3 fixed pre-freeze)
- plan commit: 2159ce0 (PLAN-V2-CONSENSUS codex+grok+gemini AGREE)
- manifest: design/cad-harness-verify-v2/SHA256.json (187 files, sha256 129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8); phase2 snapshot archived alongside
- frozen at: 2026-10-13 09:05 JST (supervisor, DPC-019); host unit tests 91 OK (6 skips)
- Phase 3 prefix: host-verify-v2-reviewed-r1, call budget 163, fresh holdout test/ (W/S/A/C/K); v1 items are dev only.

## Post-run aggregation fix: verify-v2-reviewed-r1-aggfix (2026-10-13 JST)

- Exception approved by the user (option A, 10:43 JST) after the measurement run `host-verify-v2-reviewed-r1` completed 60/60 (stop_reason null).
- Defect: in `aggregate()`, the exact float check `deadline_monotonic - started_monotonic != 10800`. The stored pair is 525342.3589999999 - 514542.359 = 10799.999999999942, an error of 5.82e-11 s, so the check raised `suite_record_binding`.
- Fix: the span check is now `abs(span - 10800) > 1e-6`. Aggregate takes `--run-manifest` and binds the run records to the archived original manifest. `run` refuses `-aggfix` versions. Unit tests were added.
- No change to scoring, gold, thresholds, order, runner or Probe. No new Sol or CAD calls. deadline_ok and the elapsed checks stay exact.
- Consensus: AGGFIX-CONSENSUS.md (codex, grok and gemini AGREE). Implementation review: grok and gemini READY. Implementation commit: dd7225c. Plan commit: 2159ce0 (unchanged).
- Original manifest archived byte-identical as SHA256.run-r1.json, sha256 129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8.
- New SHA256.json (version verify-v2-reviewed-r1-aggfix), sha256 b129072a9b1681795f6ec6339e6e6c808ec2a169c0b5acf2ac0708c058d8c999. The file-hash delta is exactly {tools/eval_verify_v2.py, tools/test_verify_v2.py}; all other fields are equal.
- Outputs: reports/aggregate-verify-v2-host-reviewed-r1-aggfix.{json,csv} (new files; nothing overwritten).
