# SOLFIX BRIEF: verify-v3-reviewed-r1-solfix (user order, 16:02 JST)

Read SOL-FAILURE.md first. In short: three transient provider `server_overloaded` rejections.
- The q-A5-r5 rejection caused the harness stop.
- G5-r1 and G1-r2 were scored as `interpretation` failures, but the actual cause was the same provider rejection.

## Proposed minimal fix (harness only; no change to scoring, gold, thresholds, order, N or budgets)
1. **Classify.** After each `codex exec`, parse the `--json` stdout for an error event or `task_complete.error`.
   - If `codex_error_info` is in the allowlist `{server_overloaded}` and there was no model output (no final message), the call is `provider_rejected`.
   - Nothing else changes classification. Do not match free text or "startswith".
2. **Bounded retry.** On `provider_rejected`, retry the same call with byte-identical args/prompt/context.
   - At most 2 retries, with backoffs of 30 s and 90 s, clipped to the stage, episode and shared clocks.
   - Every attempt is recorded (session_id, error info, wall) and counts toward the 163-call cap and the clocks.
   - A provider-rejected attempt does not consume the model's P/R allowance.
   - If retries are exhausted, the episode ends `provider_unavailable`. That is an episode stop with partial data, not a model failure. A version harness stop happens only if 3 consecutive episodes end `provider_unavailable`.
3. **Capture.** Save a bounded stdout/stderr tail (≤16 KB each) per call as episode artifacts, with hashes in driver-run.json.
4. **Resume.** Add `eval_verify_v3.py resume --prefix host-verify-v3-reviewed-r1 --run-manifest <archived original SHA256>`. It:
   - runs only the not_started IDs in frozen order;
   - keeps all 46 completed records byte-identical;
   - writes a second suite segment record bound to the original plan/order;
   - gives the resumed segment its own 10800 s monotonic clock. The original segment keeps its own deadline_ok. No extension of the old clock; each segment is checked strictly.
   Aggregate binds both segments, plus the original manifest for segment 1 and the solfix manifest for segment 2.
5. **Re-freeze.** Archive SHA256.json → SHA256.run-r1.json (byte-identical), then re-freeze as `verify-v3-reviewed-r1-solfix`. FROZEN.md documents why. The new aggregate goes to new files (`aggregate-verify-v3-host-reviewed-r1-solfix.*`).

## Open question (decide explicitly)
G5-r1 and G1-r2 are already-completed records whose failure was a provider rejection.
- Supervisor default: keep them scored as recorded (conservative, no result replacement, per the plan's "no manual result replacement"). Document the attribution in RESULTS and add a `provider_rejected` annotation in the aggregate.
- The source threshold is already met with them counted as failures, so the bar is unaffected.
Alternatives (e.g. re-running them as extra IDs) need justification.

## Ask
Write `AGREE` or `COUNTER <exact change>` to design\cad-harness-verify-v3\solfix-<you>.md. Codex: if AGREE, list the exact files and diff plan.
