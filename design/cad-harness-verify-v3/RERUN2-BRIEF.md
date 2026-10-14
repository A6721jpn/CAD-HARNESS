# RERUN2 brief (user decision 2026-10-14 08:58 JST, option 1)

## User decision (verbatim intent)
- Re-run ONLY geometry-G5-r1 and geometry-G1-r2, the two segment-1 episodes scored as interpretation failures because of provider `server_overloaded` (SOL-FAILURE.md).
- Allowed: a minimal code addition.
  - (a) A rerun-by-ID subcommand, with `-rerun2` naming.
  - (b) An aggregate substitution with a new suffix.
- Not allowed: changes to scoring, gold, thresholds, order or the driver.
- Overloaded handling: wait 600 s and resend (the existing solfix provider_retry). Quota: consult at 55%, hard stop at 60%.
- Originals are preserved and never overwritten. There is no next phase.

## Required behaviour
1. `eval_verify_v3.py rerun --prefix host-verify-v3-reviewed-r1 --ids geometry-G5-r1,geometry-G1-r2 --run-manifest design/cad-harness-verify-v3/SHA256.run-r1.json --quota-snapshot ... --codex ...`
   - Only these two IDs are allowed: a fixed allowlist equal to the provider-annotated segment-1 failures. Any other ID gives Stop.
   - Each episode runs through the unchanged `agent.run_driver` with `provider_retry=True`, the same route and max_calls, and `record()` scoring. The run names are `<run_name>-rerun2`.
   - A new suite dir `<suite>-rerun2` holds plan.json, progress.jsonl and suite-run.json. If any target exists, the command refuses.
   - Bindings checked: frozen verify, CLI version, original artifacts unchanged, the Guard with no deadline and the quota stops, and the call budget.
   - Call budget: 105 of 163 is already charged (RESULTS.md); the two episodes' max_calls fit.
2. `aggregate ... --suffix host-reviewed-r1-solfix-rerun2 --rerun2`
   - Takes the existing two-segment aggregate and replaces exactly those two rows with the rerun2 rows.
   - Records `substituted_rows` (original row and new row both kept in the JSON).
   - Recomputes the summary and thresholds with the unchanged functions.
   - The new suffix files must not already exist, so nothing is overwritten.
3. Unit tests (mocked): the allowlist, the refusal on existing dirs, that substitution touches only those two IDs, and that the original rows are retained.

## Out of scope
- Any other episode, and any re-scoring of the A5/A6 segment-2 records.
